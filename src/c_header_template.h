#pragma once

// Imports
/**IMPORT_DECLS**/

// Exports
/**EXPORT_DECLS**/

// Helper functions used in adapters
__attribute__((export_name("_it_strlen")))
int _it_strlen(const char* str) {
    int len = 0;
    while (*str++) len++;
    return len;
}
