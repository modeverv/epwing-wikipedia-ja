#include <eb/eb.h>
#include <eb/error.h>
#include <eb/sysdefs.h>
#include <eb/text.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int reference;
    int bmp;
    int narrow_gaiji;
    int wide_gaiji;
} Hook_Counts;

static void fail(const char *operation, EB_Error_Code error_code) {
    fprintf(stderr, "%s: %s\n", operation, eb_error_message(error_code));
    exit(EXIT_FAILURE);
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
        fail("eb_set_hook", error_code);
    }
}

int main(int argc, char **argv) {
    static const char *queries[] = {"Emacs", "Linux", "Wikipedia"};
    EB_Book book;
    EB_Hookset hookset;
    EB_Subbook_Code subbooks[EB_MAX_SUBBOOKS];
    Hook_Counts counts = {0, 0, 0, 0};
    int query_hits[3] = {0, 0, 0};
    int subbook_count = 0;
    int text_entries_read = 0;
    char directory[EB_MAX_DIRECTORY_NAME_LENGTH + 1];
    EB_Error_Code error_code;

    if (argc != 2) {
        fprintf(stderr, "usage: wikiepwing-eb-probe BOOK_DIRECTORY\n");
        return EXIT_FAILURE;
    }
    error_code = eb_initialize_library();
    if (error_code != EB_SUCCESS) {
        fail("eb_initialize_library", error_code);
    }
    eb_initialize_book(&book);
    eb_initialize_hookset(&hookset);
    install_hook(&hookset, EB_HOOK_END_REFERENCE);
    install_hook(&hookset, EB_HOOK_BEGIN_COLOR_BMP);
    install_hook(&hookset, EB_HOOK_NARROW_FONT);
    install_hook(&hookset, EB_HOOK_WIDE_FONT);

    error_code = eb_bind(&book, argv[1]);
    if (error_code != EB_SUCCESS) {
        fail("eb_bind", error_code);
    }
    error_code = eb_subbook_list(&book, subbooks, &subbook_count);
    if (error_code != EB_SUCCESS) {
        fail("eb_subbook_list", error_code);
    }
    if (subbook_count != 1) {
        fprintf(stderr, "expected one subbook, got %d\n", subbook_count);
        return EXIT_FAILURE;
    }
    error_code = eb_set_subbook(&book, subbooks[0]);
    if (error_code != EB_SUCCESS) {
        fail("eb_set_subbook", error_code);
    }
    error_code = eb_subbook_directory(&book, directory);
    if (error_code != EB_SUCCESS) {
        fail("eb_subbook_directory", error_code);
    }

    for (size_t i = 0; i < 3; i++) {
        EB_Hit hits[16];
        int hit_count = 0;
        char text[16384];
        ssize_t text_length = 0;

        error_code = eb_search_word(&book, queries[i]);
        if (error_code != EB_SUCCESS) {
            fail("eb_search_word", error_code);
        }
        error_code = eb_hit_list(&book, 16, hits, &hit_count);
        if (error_code != EB_SUCCESS) {
            fail("eb_hit_list", error_code);
        }
        if (hit_count < 1) {
            fprintf(stderr, "expected a hit for %s\n", queries[i]);
            return EXIT_FAILURE;
        }
        query_hits[i] = hit_count;
        error_code = eb_seek_text(&book, &hits[0].text);
        if (error_code != EB_SUCCESS) {
            fail("eb_seek_text", error_code);
        }
        error_code = eb_read_text(
            &book, NULL, &hookset, &counts, sizeof(text) - 1, text, &text_length
        );
        if (error_code != EB_SUCCESS) {
            fail("eb_read_text", error_code);
        }
        if (text_length <= 0) {
            fprintf(stderr, "empty text for %s\n", queries[i]);
            return EXIT_FAILURE;
        }
        text_entries_read++;
    }

    if (counts.reference < 3 || counts.bmp < 1 || counts.narrow_gaiji < 1
        || counts.wide_gaiji < 1) {
        fprintf(stderr, "expected hooks were not observed\n");
        return EXIT_FAILURE;
    }

    printf("{\n");
    printf("  \"schema_version\": 1,\n");
    printf("  \"eb_library_version\": \"%s\",\n", EB_VERSION_STRING);
    printf("  \"subbook_count\": %d,\n", subbook_count);
    printf("  \"directory\": \"%s\",\n", directory);
    printf("  \"search_methods\": [\"word\", \"endword\"],\n");
    printf("  \"queries\": {\"Emacs\": %d, \"Linux\": %d, \"Wikipedia\": %d},\n",
        query_hits[0], query_hits[1], query_hits[2]);
    printf("  \"text_entries_read\": %d,\n", text_entries_read);
    printf("  \"hooks\": {\"reference\": %d, \"bmp\": %d, "
        "\"narrow_gaiji\": %d, \"wide_gaiji\": %d}\n",
        counts.reference, counts.bmp, counts.narrow_gaiji, counts.wide_gaiji);
    printf("}\n");

    eb_finalize_hookset(&hookset);
    eb_finalize_book(&book);
    eb_finalize_library();
    return EXIT_SUCCESS;
}
