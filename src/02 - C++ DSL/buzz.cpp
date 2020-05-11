/**IT_START**/

export {
    func isBuzz(s32) -> u1;
    func buzzStr() -> string;
}

/**IT_END**/

bool isBuzz(int n) {
    return n % 5 == 0;
}

const char* buzzStr() {
    return "Buzz";
}
