// Exports
__attribute__((export_name("isBuzz"))) bool isBuzz(int);
__attribute__((export_name("buzzStr"))) const char* buzzStr();

bool isBuzz(int n) {
    return n % 5 == 0;
}

const char* buzzStr() {
    return "Buzz";
}

// Helper functions used in adapters
__attribute__((export_name("_it_strlen")))
int _it_strlen(const char* str) {
    int len = 0;
    while (*str++) len++;
    return len;
}
