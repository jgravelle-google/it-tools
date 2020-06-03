# Self Hosting

**NOTE**: implementation has changed, this is out of date

This example demonstrates how one might implement IT adapters in Wasm itself.

It depends on the bulk-memory proposal for maximum efficiency, but can be
implemented in terms of function calls (and JS imports) in the interim.

## How does it work?

Each module has three parts: the core wasm module, an adapter wasm module, and
a JS harness that handles loading it.

### C++ user code

The core wasm module is built with no additional compiler support. The C++ here
is taken directly from Example #2, using the C++ DSL.

Looking at fizz.cpp, we have two normal C++ functions, isFizz and fizzStr, which
we export with a DSL annotation:

```c++
export {
    func isFizz(s32) -> u1;
    func fizzStr() -> string;
}
```

This gets translated into vanilla C++ function declarations:

```c++
__attribute__((export_name("isFizz"))) bool isFizz(int);
__attribute__((export_name("fizzStr"))) const char* fizzStr();
```

Which in turn become Wasm function exports.

### IT .wat

The adapter module is written by hand, as a translation from the ITL generated
by the C++ DSL.

So, where the C++ DSL would generate ITL wrappers for those functions like so:

```
(export
    (func _ "isFizz" (param s32) (result u1)
        (as u1 (call isFizz
            (as i32 (local 0))))
    )
    (func _ "fizzStr" (param ) (result string)
        (call _it_cppToString (call fizzStr))
    )
)
```

We can transcribe those functions into wasm that looks like:

```
(func $it_isFizz (export "isFizz") (param i32) (result i32)
    (call_indirect (param i32) (result i32)
        (local.get 0)
        (i32.const 3) ;; isFizz id
    )
)
(func $it_fizzStr (export "fizzStr") (result anyref)
    (call $cppToString (call_indirect (param) (result i32)
        (i32.const 4) ;; fizzStr id
    ))
)
```

// TODO: more info, look at cppToString to look at some of the runtime elements

### Loader JS

Each JS module has its own copy of the IT-runtime JS module, which adapts any
unrepresentable IT types, such as strings, arrays, and records.
