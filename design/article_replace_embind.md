# How to Replace Embind

This is an article written with the intent of showing how one might use these tools
to incrementally replace Emscripten's Embind feature with a more-modern version.

Link: [Embind documentation](https://emscripten.org/docs/porting/connecting_cpp_and_javascript/embind.html)

## Motivation

Embind is slow. A lot of its features are implemented in its runtime, and as a
result needs to be enabled with a `--bind` flag to avoid penalizing code that
doesn't use it.

[A comparison was made](https://github.com/jgravelle-google/interface-embind)
that found Embind 10x slower than the equivalent JS (with 1 million JS/wasm calls
per frame), whereas a precompiled JS polyfill prototype was only 10% slower with
the same amount of JS/wasm calls. This shows that we can achieve near-JS speeds
without needing to wait for the full Interface Types proposal.

Embind's API for calling JS from C++ is non-idiomatic C++. In particular it uses
strings and dynamism in order to cover a wide surface area.

## Background : How Embind Works Today

In order to successfully replace Embind, we first need to be able to match the
set of features that it has on offer.

There are two major directions we care about when it comes to bindings, lifting
and lowering, aka: C++ -> JS, and JS -> C++

### Calling JS from C++

Embind's solution to using JS from C++ is straightforward, powerful, and
problematic. The core element is the `emscripten::val` type, which wraps JS
values for use in C++ code.

This is powerful because it can use any(?) JS API that exists today. It is
problematic because it uses strings to do so, which is essentially combining the
problems with JS's `eval` with C++'s memory safety.

This is interesting because we'll need to match this level of flexibility for
users to feel like any successor API is strictly better.

### Calling C++ from JS

C++ functions/classes can be exposed to JS with the `EMSCRIPTEN_BINDINGS` macro.
In that context there are special `function`, `class`, `method`, functions that
describe C++ interfaces.

Under the hood, the top-level macro defines a C++ class with a static initializer,
that calls the initializer functions that the user specified (hence, the reason
they use method chaining syntax). These static initializers are called before
`main` is called, and they set up callbacks in Embind's runtime.

There from JS these become methods added to the `Module` object, that are called
with native JS types.

## Examples

### Hello World

Vanilla JS:
```js
var hello = 'hello world!';
console.log(hello);
```

Embind C++:
```c++
using emscripten;
val console = val::global("console");
val hello = val("hello world!");
console.call<void>("log", hello);
```

Proposed C++:
```c++
#include "console.h"
const char* hello = "hello world!";
Console::log(hello);
```
