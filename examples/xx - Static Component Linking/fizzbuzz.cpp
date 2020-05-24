/**IT_START**/

import "fizz" {
    func isFizz(s32) -> u1;
    func fizzStr() -> string;
}
import "buzz" {
    func isBuzz(s32) -> u1;
    func buzzStr() -> string;
}
import "console" {
    func log(string);
    func logInt(s32);
}
export {
    func fizzbuzz(s32);
}

/**IT_END**/

void fizzbuzz(int n) {
    auto fizz = fizzStr();
    auto buzz = buzzStr();
    for (int i = 1; i <= n; ++i) {
        if (isFizz(i) && isBuzz(i)) {
            log("Fizzier Buzz");
        } else if (isFizz(i)) {
            log(fizz);
        } else if (isBuzz(i)) {
            log(buzz);
        } else {
            logInt(i);
        }
    }
}
