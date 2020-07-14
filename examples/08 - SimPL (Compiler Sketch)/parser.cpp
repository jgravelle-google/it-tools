/**IT_START**/

import "console" {
    func log(string);
}
export {
    // type CallExpr = struct {
    //     string callee;
    //     string arg;
    // };

    // func parse(string) -> CallExpr;
}

/**IT_END**/

// temporary; what it should look like
struct CallExpr {
    const char* callee;
    const char* arg;
    CallExpr(const char* a, const char* b) {
        callee = a;
        arg = b;
    }
};

#include <string>

__attribute__((used, export_name("parse")))
CallExpr parse(const char* input) {
    log("Hello there");

    int i = 0;
    while (input[i] != ' ') { i++; }
    std::string callee(input, i);

    input = input + i + 1; // skip the space
    i = 0;
    while (input[i] != ';') { i++; }
    std::string arg(input, i);

    return CallExpr(callee.c_str(), arg.c_str());
}
