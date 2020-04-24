#include "fizzbuzz_impl.h"

void fizzbuzz(int n) {
    for (int i = 1; i <= n; ++i) {
        if (isFizz(i) && isBuzz(i)) {
            print("FizzBuzz");
        } else if (isFizz(i)) {
            print(fizzStr());
        } else if (isBuzz(i)) {
            print(buzzStr());
        } else {
            printInt(i);
        }
    }
}
