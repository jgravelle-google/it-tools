# Interface Types Tools

This repository serves as a collection of tools useful for prototyping code
related to the WebAssembly Interface Types proposal.

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
this script. The output of this is a header file with annotations that map to
the imports and exports specified, as well as an ITL file that wraps the wasm
module with adapter functions.

The purpose of this script is to automate the bulk of writing ITL and C++
annotations by hand.
