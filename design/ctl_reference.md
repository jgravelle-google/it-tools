# CTL Reference

CTL is a small language designed to generate C++-aware ITL

## Caveats / Footguns

* Can't pass function pointers as an `any` value, they use separate index spaces
    * TODO: add an `anyfunc` type? (lowers to `void(*)(void)`?)
