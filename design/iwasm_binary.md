# .iwasm binary format

## IWasm?

IWasm, short for Interface Types WebAssembly Module. A strawman binary format
that describes an IT component.

## Grammar

Notation notes:

* `A <- B` : A is produced by B
* `A / B` : A followed by B
* `A*` : 0 or more repetitions of A
* `A{N}` : exactly N repetitions of A
* `enum { (A: B)* }` : the first matching B (labeled by A's)

```
iwasm <- header / vec(import*) / vec(export*) / vec(module*) / vec(func*)
header <- magic / version
magic <- 0x00 / 'a' / 's' / 'm'
version <- 0x01 / 0x00 / 0x01 / 0x00
import <- mod_name / name / func
export <- name / func
module <- [WebAssembly module, binary format]

func <- vec(param) / vec(result) / vec(instr)
param <- type
result <- type

mod_name <- name
name <- vec(byte)
vec(T) <- uleb(length) / T{length}
byte <- 0x00..0xff

type <- enum {
  // Interface types
  s32: sleb(-64)
  u32: sleb(-65)
  f32: sleb(-66)
  any: sleb(-70)
  string: sleb(-71)
  array: sleb(-72) / type
  struct: sleb(-73) / vec(struct_field)

  # Core wasm types
  i32: sleb(-1)
  i64: sleb(-2)
  f32: sleb(-3)
  f64: sleb(-4)
  anyref: sleb(-16)
}
struct_field <- name / type
```

## Notes

* Normal wasm modules are embedded in an iwasm file inline
* The 8 bytes are nearly identical to a regular wasm module
    * The version field has another bit set. This changes the meaning from 4
      bytes of version, to 2 bytes of version and 2 bytes of module kind, 0 for
      standard wasm, 1 for IT
