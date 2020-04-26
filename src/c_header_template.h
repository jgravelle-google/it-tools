#pragma once

// builtin functions
__attribute__((export_name("_it_strlen")))
int _it_strlen(const char* str) {
    int len = 0;
    while (*str++) len++;
    return len;
}

/**EXPORT_DECLS**/
