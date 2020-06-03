(import "_it_runtime" "string_len" (func $string_len (param anyref) (result i32)))
(import "_it_runtime" "mem_to_string" (func $mem_to_string (param anyref i32 i32 i32) (result anyref)))
(import "_it_runtime" "string_to_mem" (func $string_to_mem (param anyref i32 anyref i32)))
(import "_it_runtime" "load_wasm" (func $load_wasm (param i32) (result anyref)))
(import "_it_runtime" "set_table" (func $set_table (param i32 i32 anyref)))
(import "_it_runtime" "get_func" (func $get_func (param anyref i32) (result anyref)))

(global $wasm_instance (mut anyref) (ref.null))

(table (export "_it_table") 5 funcref)
(type $i (func (param i32)))
(type $i_i (func (param i32) (result i32)))
(type $ii (func (param i32 i32)))

(memory (export "_it_memory") 1)
(data (i32.const 0) "\0dout/buzz.wasm")
(data (i32.const 15) "\0a_it_strlen")
(data (i32.const 26) "\13_it_writeStringTerm")
(data (i32.const 46) "\09_it_table")
(data (i32.const 56) "\06memory")
(data (i32.const 63) "\06malloc")
(data (i32.const 70) "\06isBuzz")
(data (i32.const 77) "\07buzzStr")

;; Helpers
(func $malloc (param i32) (result i32)
    (call_indirect (type $i_i)
        (local.get 0)
        (i32.const 0) ;; malloc id
    )
)
(func $_it_writeStringTerm (param i32 i32)
    (call_indirect (type $ii)
        (local.get 0)
        (local.get 1)
        (i32.const 1) ;; _it_writeStringTerm id
    )
)
(func $_it_strlen (param i32) (result i32)
    (call_indirect (type $i_i)
        (local.get 0)
        (i32.const 2) ;; _it_strlen id
    )
)
(func $cppToString (param i32) (result anyref)
    ;; helper function to convert strings as a unary expression
    (call $mem_to_string
        (global.get $wasm_instance)
        (i32.const 56) ;; "memory"
        (local.get 0)
        (call $_it_strlen (local.get 0))
    )
)
(func $stringToCpp (param anyref) (result i32)
    (local i32 i32)
    (local.set 1 (call $string_len (local.get 0)))
    (local.set 2 (call $malloc (i32.add (local.get 1) (i32.const 1))))
    (call $string_to_mem
        (global.get $wasm_instance)
        (i32.const 56) ;; "memory"
        (local.get 0) ;; str
        (local.get 2) ;; ptr
    )
    (call $_it_writeStringTerm
        (local.get 2) ;; ptr
        (local.get 1) ;; len
    )
    (local.get 2) ;; ptr
)

;; Initialization function
(func $set_func (param i32 i32)
    (call $set_table
        (i32.const 46) ;; _it_table
        (local.get 0) ;; table idx
        (call $get_func
            (global.get $wasm_instance)
            (local.get 1) ;; func name
        )
    )
)
(func (export "init")
    (global.set $wasm_instance
        (call $load_wasm
            (i32.const 0) ;; "out/buzz.wasm"
        )
    )
    (call $set_func (i32.const 0)
        (i32.const 63) ;; "malloc"
    )
    (call $set_func (i32.const 1)
        (i32.const 26) ;; "_it_writeStringTerm"
    )
    (call $set_func (i32.const 2)
        (i32.const 15) ;; "_it_strlen"
    )
    (call $set_func (i32.const 3)
        (i32.const 70) ;; "isBuzz"
    )
    (call $set_func (i32.const 4)
        (i32.const 77) ;; "buzzStr"
    )
)

;; Exports
(func $it_isBuzz (export "isBuzz") (param i32) (result i32)
    (call_indirect (param i32) (result i32)
        (local.get 0)
        (i32.const 3) ;; isBuzz id
    )
)
(func $it_buzzStr (export "buzzStr") (result anyref)
    (call $cppToString (call_indirect (param) (result i32)
        (i32.const 4) ;; buzzStr id
    ))
)
