// Exports
__attribute__((export_name("isFizz"))) bool isFizz(int);
__attribute__((export_name("fizzStr"))) const char* fizzStr();

bool isFizz(int n) {
    return n % 3 == 0;
}

const char* fizzStr() {
    return "Fizz";
}

// Helper functions used in adapters
__attribute__((export_name("_it_strlen")))
int _it_strlen(const char* str) {
    int len = 0;
    while (*str++) len++;
    return len;
}
