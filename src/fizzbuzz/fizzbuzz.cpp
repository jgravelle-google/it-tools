#include "fizzbuzz_impl.h"

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
