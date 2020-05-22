# Self Hosting

This example demonstrates implementing IT-like bindings in Wasm itself. We
compile an ITL file to pure wasm modules, rather than JS.

It depends on the bulk-memory proposal for maximum efficiency, but can be
implemented in terms of function calls (and JS imports) in the interim.

## Plan

### Step 1: Implement manually

Handwrite the JS and wat needed to implement this

### Step 2: Automate

Extract those to templates, generate the glue
