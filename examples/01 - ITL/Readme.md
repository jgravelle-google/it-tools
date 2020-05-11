# 1 - ITL IDL

This is a proof-of-concept for the ITL file format. ITL stands for "Interface
Types IDL".

The purpose of this version is to demonstrate writing + polyfilling ITL by hand.
Future tools will have more comfortable generation of ITL from the source
language, but this is essentially an asm format for the IT proposal.

## ITL is an IDL, IT is not an IDL

ITL is an IDL that maps as closely as possible to IT semantics, while still
taking liberties and defining behavior that is unmodeled by IT. Examples include:

* ITL specifies how to load its wasm modules
* ITL uses symbol names instead of indices for its local functions
