/**IT_START**/

export {
    func isFizz(s32) -> u1;
    func fizzStr() -> string;
}

/**IT_END**/

bool isFizz(int n) {
    return n % 3 == 0;
}

const char* fizzStr() {
    return "Fizz";
}
