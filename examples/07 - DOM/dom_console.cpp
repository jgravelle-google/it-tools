/**IT_START**/

import "sys" {
  type Command;
  func getCommand(string) -> Command;
  func addArg(Command, string);
  func run(Command);
}
// type Document = import "document" {
//     func isBuzz(s32) -> u1;
//     func buzzStr() -> string;
// }
export {
    func log(string);
}

/**IT_END**/

void log(char* str) {
    auto item = document.createElement("li");
    item.innerText = x;
    list.append(item);
}
