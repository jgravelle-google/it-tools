// #include "fizz.h"
// TODO: generate headers
__attribute__((export_name("isFizz")))
bool isFizz(int);

bool isFizz(int n) {
    return n % 3 == 0;
}

const char* fizzStr() {
    return "Fizz";
}
