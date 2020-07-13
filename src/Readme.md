# List of Tools

These are the tools, and a brief discussion of what they do.

## itl_parser.py

Parser for the ITL format. ITL is a domain-specific language (DSL) that is
intended to map nearly identically to the Interface Types (IT) text format.

This script is a common base for parsing the format, and is intended to be used
by other tools in this repo.

## adapter.py

Consumes ITL and generates a JavaScript polyfill.

The purpose of this script is to allow for experimentation with IT-like ideas in
a language-agnostic way.

## cpp_itl_generator.py

Takes a C++ file that describes a wasm module, specified with a DSL specific to
this script (called CTL). The output of this is a header file with annotations
that map to the imports and exports specified, as well as an ITL file that wraps
the wasm module with adapter functions.

The purpose of this script is to automate the bulk of writing ITL and C++
annotations by hand.

### Arguments

`python cpp_itl_generator.py INPUT.cpp [additional arguments]`

* `INPUT` : C++ file with CTL declarations
* `--cpp` : Output C++ file with CTL stripped and replaced with function
    declarations. Defaults to `out/INPUT.cpp`
* `--itl`: Output ITL file. Defaults to `out/INPUT.itl`
* `--wasm`: Oputput wasm file. This path is baked into the ITL file, so should
    be overridden to match the core wasm module to be loaded. Defaults to
    `out/INPUT.wasm`

## itl_iwasm_generator.py

Generates an .iwasm module from an .itl file.

IWasm is an binary format that describes an IT module, aka a component.
