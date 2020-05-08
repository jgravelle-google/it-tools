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

__attribute__((export_name("_it_writeStringTerm")))
void _it_writeStringTerm(char* str, int len) {
    // Writes null-terminator for imported strings
    str[len] = 0;
}
