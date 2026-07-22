#define _XOPEN_SOURCE 700

#include <eb/eb.h>
#include <eb/error.h>
#include <eb/sysdefs.h>
#include <eb/text.h>

#include <errno.h>
#include <ftw.h>
#include <iconv.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define MAX_QUERY_BYTES 4096
#define MAX_ENCODED_QUERY_BYTES 8192
#define MAX_HEADING_BYTES 16384
#define MAX_REFERENCE_ENTRIES 100000
#define MAX_REFERENCE_DEPTH 16

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

static int parse_max_results(const char *value) {
    char *end = NULL;
    long parsed;
    errno = 0;
    parsed = strtol(value, &end, 10);
    if (errno != 0 || end == value || *end != '\0' || parsed < 1 || parsed > 1000) {
        fail_message("max results must be an integer from 1 to 1000");
    }
    return (int)parsed;
}

static void validate_query(const char *query) {
    size_t length = strlen(query);
    if (length == 0 || length > MAX_QUERY_BYTES) {
        fail_message("query must contain from 1 to 4096 UTF-8 bytes");
    }
    if (query[0] == ' ' || query[length - 1] == ' ') {
        fail_message("query must be trimmed");
    }
    for (size_t index = 0; index < length; index++) {
        unsigned char byte = (unsigned char)query[index];
        if (byte < 0x20 || byte == 0x7f) {
            fail_message("query contains a control byte");
        }
    }
}

static void convert_query_to_euc_jp(
    const char *input,
    char output[MAX_ENCODED_QUERY_BYTES]
) {
    iconv_t converter = iconv_open("EUC-JP", "UTF-8");
    char *input_cursor = (char *)input;
    char *output_cursor = output;
    size_t input_left = strlen(input);
    size_t output_left = MAX_ENCODED_QUERY_BYTES - 1;
    if (converter == (iconv_t)-1) {
        fail_message("cannot initialize UTF-8 to EUC-JP converter");
    }
    if (iconv(converter, &input_cursor, &input_left, &output_cursor, &output_left)
            == (size_t)-1
        || input_left != 0) {
        iconv_close(converter);
        fail_message("query is not representable as JIS X 0208/EUC-JP");
    }
    *output_cursor = '\0';
    if (iconv_close(converter) != 0) {
        fail_message("cannot finalize query encoding converter");
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

int main(int argc, char **argv) {
    EB_Book book;
    EB_Hookset hookset;
    EB_Subbook_Code subbooks[EB_MAX_SUBBOOKS];
    EB_Character_Code character_code;
    EB_Error_Code error_code;
    char encoded_query[MAX_ENCODED_QUERY_BYTES];
    int subbook_count = 0;
    int max_results;

    if (argc != 5) {
        fprintf(stderr, "usage: wikiepwing-eb-search BOOK MODE QUERY MAX_RESULTS\n");
        return EXIT_FAILURE;
    }
    validate_reference_root(argv[1]);
    if (strcmp(argv[2], "exact") != 0 && strcmp(argv[2], "word") != 0
        && strcmp(argv[2], "endword") != 0 && strcmp(argv[2], "keyword") != 0
        && strcmp(argv[2], "cross") != 0) {
        fail_message("search mode must be exact, word, endword, keyword, or cross");
    }
    validate_query(argv[3]);
    max_results = parse_max_results(argv[4]);
    convert_query_to_euc_jp(argv[3], encoded_query);

    error_code = eb_initialize_library();
    if (error_code != EB_SUCCESS) {
        fail_eb("eb_initialize_library", error_code);
    }
    eb_initialize_book(&book);
    eb_initialize_hookset(&hookset);
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
    if (subbook_count < 1) {
        fail_message("reference book has no subbooks");
    }

    printf("WIKIEPWING_EB_SEARCH\t1\tJISX0208\n");
    for (int subbook_index = 0; subbook_index < subbook_count; subbook_index++) {
        EB_Hit *hits;
        char directory[EB_MAX_DIRECTORY_NAME_LENGTH + 1];
        char title[EB_MAX_TITLE_LENGTH + 1];
        int hit_count = 0;
        int returned_count;
        int truncated;

        error_code = eb_set_subbook(&book, subbooks[subbook_index]);
        if (error_code != EB_SUCCESS) {
            fail_eb("eb_set_subbook", error_code);
        }
        error_code = eb_subbook_directory(&book, directory);
        if (error_code != EB_SUCCESS) {
            fail_eb("eb_subbook_directory", error_code);
        }
        validate_directory_name(directory);
        error_code = eb_subbook_title(&book, title);
        if (error_code != EB_SUCCESS) {
            fail_eb("eb_subbook_title", error_code);
        }
        if (strcmp(argv[2], "exact") == 0) {
            error_code = eb_search_exactword(&book, encoded_query);
        } else if (strcmp(argv[2], "word") == 0) {
            error_code = eb_search_word(&book, encoded_query);
        } else if (strcmp(argv[2], "endword") == 0) {
            error_code = eb_search_endword(&book, encoded_query);
        } else {
            const char *input_words[] = {encoded_query, NULL};
            if (strcmp(argv[2], "keyword") == 0) {
                error_code = eb_search_keyword(&book, input_words);
            } else {
                error_code = eb_search_cross(&book, input_words);
            }
        }
        if (error_code != EB_SUCCESS) {
            fail_eb("eb_search", error_code);
        }
        hits = calloc((size_t)max_results + 1, sizeof(*hits));
        if (hits == NULL) {
            fail_message("cannot allocate bounded hit list");
        }
        error_code = eb_hit_list(&book, max_results + 1, hits, &hit_count);
        if (error_code != EB_SUCCESS) {
            free(hits);
            fail_eb("eb_hit_list", error_code);
        }
        truncated = hit_count > max_results;
        returned_count = truncated ? max_results : hit_count;
        printf("S\t%d\t%s\t", subbooks[subbook_index], directory);
        print_hex(title, strlen(title));
        printf("\t%d\t%d\n", returned_count, truncated);

        for (int hit_index = 0; hit_index < returned_count; hit_index++) {
            char heading[MAX_HEADING_BYTES];
            ssize_t heading_length = 0;
            error_code = eb_seek_text(&book, &hits[hit_index].heading);
            if (error_code != EB_SUCCESS) {
                free(hits);
                fail_eb("eb_seek_text heading", error_code);
            }
            error_code = eb_read_heading(
                &book,
                NULL,
                &hookset,
                NULL,
                sizeof(heading),
                heading,
                &heading_length
            );
            if (error_code != EB_SUCCESS) {
                free(hits);
                fail_eb("eb_read_heading", error_code);
            }
            if (heading_length <= 0) {
                free(hits);
                fail_message("search hit has an empty heading");
            }
            printf("R\t%d\t%d\t", subbooks[subbook_index], hit_index + 1);
            print_hex(heading, (size_t)heading_length);
            printf(
                "\t%d\t%d\t%d\t%d\n",
                hits[hit_index].heading.page,
                hits[hit_index].heading.offset,
                hits[hit_index].text.page,
                hits[hit_index].text.offset
            );
        }
        free(hits);
    }

    eb_finalize_hookset(&hookset);
    eb_finalize_book(&book);
    eb_finalize_library();
    return EXIT_SUCCESS;
}
