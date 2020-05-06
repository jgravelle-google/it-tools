// Imports
__attribute__((import_module("buzz"), import_name("isBuzz"))) bool isBuzz(int);
__attribute__((import_module("buzz"), import_name("buzzStr"))) const char* buzzStr();
__attribute__((import_module("console"), import_name("log"))) void log(const char*);
__attribute__((import_module("console"), import_name("print"))) void print(const char*);
__attribute__((import_module("console"), import_name("printInt"))) void printInt(int);
__attribute__((import_module("fizz"), import_name("isFizz"))) bool isFizz(int);
__attribute__((import_module("fizz"), import_name("fizzStr"))) const char* fizzStr();

// Exports
__attribute__((export_name("fizzbuzz"))) void fizzbuzz(int);

void fizzbuzz(int n) {
    auto fizz = fizzStr();
    auto buzz = buzzStr();
    for (int i = 1; i <= n; ++i) {
        if (isFizz(i) && isBuzz(i)) {
            print("FizzBuzz");
        } else if (isFizz(i)) {
            print(fizz);
        } else if (isBuzz(i)) {
            print(buzz);
        } else {
            printInt(i);
        }
    }
}

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
