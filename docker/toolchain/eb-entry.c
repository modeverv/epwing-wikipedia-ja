#define _XOPEN_SOURCE 700

#include <eb/eb.h>
#include <eb/error.h>
#include <eb/sysdefs.h>
#include <eb/text.h>

#include <errno.h>
#include <ftw.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define MAX_BODY_BYTES 262144
#define READ_CHUNK_BYTES 8192
#define MAX_CONSECUTIVE_EMPTY_READS 1024
#define MAX_REFERENCE_ENTRIES 100000
#define MAX_REFERENCE_DEPTH 16

typedef struct {
    int reference;
    int bmp;
    int narrow_gaiji;
    int wide_gaiji;
} Hook_Counts;

static int visited_entries = 0;
static const char *walk_error = NULL;

static void fail_eb(const char *operation, EB_Error_Code error_code) {
    fprintf(stderr, "%s: %s\n", operation, eb_error_message(error_code));
    exit(EXIT_FAILURE);
}

static void fail_message(const char *message) {
    fprintf(stderr, "%s\n", message);
    exit(EXIT_FAILURE);
}

static int inspect_entry(
    const char *path,
    const struct stat *status,
    int type_flag,
    struct FTW *walk
) {
    (void)path;
    (void)status;
    visited_entries++;
    if (visited_entries > MAX_REFERENCE_ENTRIES) {
        walk_error = "reference entry limit exceeded";
        return 1;
    }
    if (walk->level > MAX_REFERENCE_DEPTH) {
        walk_error = "reference depth limit exceeded";
        return 1;
    }
    if (type_flag == FTW_SL || type_flag == FTW_SLN) {
        walk_error = "reference symlink is not allowed";
        return 1;
    }
    return 0;
}

static void validate_reference_root(const char *path) {
    struct stat status;
    if (path[0] != '/') {
        fail_message("book directory must be absolute");
    }
    if (lstat(path, &status) != 0) {
        fprintf(stderr, "cannot inspect book directory: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }
    if (S_ISLNK(status.st_mode) || !S_ISDIR(status.st_mode)) {
        fail_message("book directory must be a real directory");
    }
    if (nftw(path, inspect_entry, 32, FTW_PHYS) != 0) {
        fail_message(walk_error == NULL ? "reference traversal failed" : walk_error);
    }
}

static int parse_integer(const char *value, int minimum, int maximum, const char *label) {
    char *end = NULL;
    long parsed;
    errno = 0;
    parsed = strtol(value, &end, 10);
    if (errno != 0 || end == value || *end != '\0' || parsed < minimum
        || parsed > maximum) {
        fprintf(stderr, "%s must be from %d to %d\n", label, minimum, maximum);
        exit(EXIT_FAILURE);
    }
    return (int)parsed;
}

static void validate_directory_name(const char *directory) {
    size_t length = strlen(directory);
    if (length == 0 || length > 8) {
        fail_message("invalid subbook directory length");
    }
    for (size_t index = 0; index < length; index++) {
        char character = directory[index];
        if (!((character >= 'A' && character <= 'Z')
                || (character >= 'a' && character <= 'z')
                || (character >= '0' && character <= '9') || character == '_')) {
            fail_message("invalid subbook directory character");
        }
    }
}

static EB_Error_Code count_hook(
    EB_Book *book,
    EB_Appendix *appendix,
    void *container,
    EB_Hook_Code hook_code,
    int argc,
    const unsigned int *argv
) {
    Hook_Counts *counts = container;
    (void)book;
    (void)appendix;
    (void)argc;
    (void)argv;
    if (hook_code == EB_HOOK_END_REFERENCE) {
        counts->reference++;
    } else if (hook_code == EB_HOOK_BEGIN_COLOR_BMP) {
        counts->bmp++;
    } else if (hook_code == EB_HOOK_NARROW_FONT) {
        counts->narrow_gaiji++;
    } else if (hook_code == EB_HOOK_WIDE_FONT) {
        counts->wide_gaiji++;
    }
    return EB_SUCCESS;
}

static void install_hook(EB_Hookset *hookset, EB_Hook_Code code) {
    EB_Hook hook = {code, count_hook};
    EB_Error_Code error_code = eb_set_hook(hookset, &hook);
    if (error_code != EB_SUCCESS) {
        fail_eb("eb_set_hook", error_code);
    }
}

static void print_hex(const char *bytes, size_t length) {
    static const char digits[] = "0123456789abcdef";
    for (size_t index = 0; index < length; index++) {
        unsigned char byte = (unsigned char)bytes[index];
        putchar(digits[byte >> 4]);
        putchar(digits[byte & 0x0f]);
    }
}

int main(int argc, char **argv) {
    EB_Book book;
    EB_Hookset hookset;
    EB_Subbook_Code subbooks[EB_MAX_SUBBOOKS];
    EB_Character_Code character_code;
    EB_Position position;
    Hook_Counts counts = {0, 0, 0, 0};
    EB_Error_Code error_code;
    char *body;
    int subbook_count = 0;
    int selected = 0;
    int max_body_bytes;
    int total_bytes = 0;
    int empty_reads = 0;
    int truncated;

    if (argc != 6) {
        fprintf(
            stderr,
            "usage: wikiepwing-eb-entry BOOK SUBBOOK_DIRECTORY PAGE OFFSET MAX_BYTES\n"
        );
        return EXIT_FAILURE;
    }
    validate_reference_root(argv[1]);
    validate_directory_name(argv[2]);
    position.page = parse_integer(argv[3], 1, INT_MAX, "page");
    position.offset = parse_integer(argv[4], 0, 2047, "offset");
    max_body_bytes = parse_integer(argv[5], 1, MAX_BODY_BYTES, "max bytes");

    error_code = eb_initialize_library();
    if (error_code != EB_SUCCESS) {
        fail_eb("eb_initialize_library", error_code);
    }
    eb_initialize_book(&book);
    eb_initialize_hookset(&hookset);
    install_hook(&hookset, EB_HOOK_END_REFERENCE);
    install_hook(&hookset, EB_HOOK_BEGIN_COLOR_BMP);
    install_hook(&hookset, EB_HOOK_NARROW_FONT);
    install_hook(&hookset, EB_HOOK_WIDE_FONT);
    error_code = eb_bind(&book, argv[1]);
    if (error_code != EB_SUCCESS) {
        fail_eb("eb_bind", error_code);
    }
    error_code = eb_character_code(&book, &character_code);
    if (error_code != EB_SUCCESS) {
        fail_eb("eb_character_code", error_code);
    }
    if (character_code != EB_CHARCODE_JISX0208) {
        fail_message("only JIS X 0208 reference books are supported");
    }
    error_code = eb_subbook_list(&book, subbooks, &subbook_count);
    if (error_code != EB_SUCCESS) {
        fail_eb("eb_subbook_list", error_code);
    }
    for (int index = 0; index < subbook_count; index++) {
        char directory[EB_MAX_DIRECTORY_NAME_LENGTH + 1];
        error_code = eb_subbook_directory2(&book, subbooks[index], directory);
        if (error_code != EB_SUCCESS) {
            fail_eb("eb_subbook_directory2", error_code);
        }
        if (strcmp(directory, argv[2]) == 0) {
            error_code = eb_set_subbook(&book, subbooks[index]);
            if (error_code != EB_SUCCESS) {
                fail_eb("eb_set_subbook", error_code);
            }
            selected = 1;
            break;
        }
    }
    if (!selected) {
        fail_message("requested subbook directory was not found");
    }
    error_code = eb_seek_text(&book, &position);
    if (error_code != EB_SUCCESS) {
        fail_eb("eb_seek_text", error_code);
    }
    body = malloc((size_t)max_body_bytes);
    if (body == NULL) {
        fail_message("cannot allocate bounded entry buffer");
    }
    while (total_bytes < max_body_bytes && !eb_is_text_stopped(&book)) {
        ssize_t read_bytes = 0;
        size_t remaining = (size_t)(max_body_bytes - total_bytes);
        size_t chunk_bytes = remaining < READ_CHUNK_BYTES ? remaining : READ_CHUNK_BYTES;
        error_code = eb_read_text(
            &book,
            NULL,
            &hookset,
            &counts,
            chunk_bytes,
            body + total_bytes,
            &read_bytes
        );
        if (error_code != EB_SUCCESS) {
            free(body);
            fail_eb("eb_read_text", error_code);
        }
        if (read_bytes < 0 || (size_t)read_bytes > chunk_bytes) {
            free(body);
            fail_message("eb_read_text returned an invalid byte count");
        }
        if (read_bytes == 0 && !eb_is_text_stopped(&book)) {
            empty_reads++;
            if (empty_reads > MAX_CONSECUTIVE_EMPTY_READS) {
                free(body);
                fail_message("eb_read_text exceeded the empty-read limit");
            }
        } else {
            empty_reads = 0;
        }
        total_bytes += (int)read_bytes;
    }
    if (total_bytes == 0) {
        free(body);
        fail_message("entry text is empty");
    }
    truncated = !eb_is_text_stopped(&book);
    printf("WIKIEPWING_EB_ENTRY\t1\tJISX0208\n");
    printf(
        "E\t%s\t%d\t%d\t%d\t", argv[2], position.page, position.offset, truncated
    );
    print_hex(body, (size_t)total_bytes);
    printf(
        "\t%d\t%d\t%d\t%d\n",
        counts.reference,
        counts.bmp,
        counts.narrow_gaiji,
        counts.wide_gaiji
    );

    free(body);
    eb_finalize_hookset(&hookset);
    eb_finalize_book(&book);
    eb_finalize_library();
    return EXIT_SUCCESS;
}
