# Self Hosting

This example demonstrates implementing IT-like bindings in Wasm itself. We
compile an ITL file to pure wasm modules, rather than JS.

It depends on the bulk-memory proposal for maximum efficiency, but can be
implemented in terms of function calls (and JS imports) in the interim.

## Plan

### Step 1: Implement manually

Handwritten JS functions that load a single wasm module and wrap it with another.
Each wasm module has an associated adapter module build from .wat assembly.

Each JS module has its own copy of the IT-runtime JS module, which adapts any
unrepresentable IT types, such as strings, arrays, and records.

### Step 2: Automate

Extract those to templates, generate the glue
