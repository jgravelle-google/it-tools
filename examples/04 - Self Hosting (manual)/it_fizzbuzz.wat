;; IT `string` is passed as `anyref`
(import "fizz" "isFizz" (func $isFizz (param i32) (result i32)))
(import "fizz" "fizzStr" (func $fizzStr (param) (result anyref)))
(import "buzz" "isBuzz" (func $isBuzz (param i32) (result i32)))
(import "buzz" "buzzStr" (func $buzzStr (param) (result anyref)))
(import "console" "log" (func $log (param anyref)))
(import "console" "logInt" (func $logInt (param i32)))

(import "_it_runtime" "string_len" (func $string_len (param anyref) (result i32)))
(import "_it_runtime" "mem_to_string" (func $mem_to_string (param anyref i32 i32 i32) (result anyref)))
(import "_it_runtime" "string_to_mem" (func $string_to_mem (param anyref i32 anyref i32)))
(import "_it_runtime" "load_wasm" (func $load_wasm (param i32) (result anyref)))
(import "_it_runtime" "set_table" (func $set_table (param i32 i32 anyref)))
(import "_it_runtime" "get_func" (func $get_func (param anyref i32) (result anyref)))

(global $wasm_instance (mut anyref) (ref.null))

(table (export "_it_table") 4 funcref)
(type $i (func (param i32)))
(type $i_i (func (param i32) (result i32)))
(type $ii (func (param i32 i32)))

(memory (export "_it_memory") 1)
(data (i32.const 0) "\11out/fizzbuzz.wasm")
(data (i32.const 18) "\08fizzbuzz")
(data (i32.const 27) "\06malloc")
(data (i32.const 34) "\0a_it_strlen")
(data (i32.const 45) "\13_it_writeStringTerm")
(data (i32.const 65) "\06memory")
(data (i32.const 72) "\09_it_table")

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
        (i32.const 65) ;; "memory"
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
        (i32.const 65) ;; "memory"
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
(func (export "init")
    (global.set $wasm_instance
        (call $load_wasm
            (i32.const 0) ;; "out/fizzbuzz.wasm"
        )
    )
    (call $set_table
        (i32.const 72) ;; "_it_table"
        (i32.const 0)
        (call $get_func
            (global.get $wasm_instance)
            (i32.const 27) ;; "malloc"
        )
    )
    (call $set_table
        (i32.const 72) ;; "_it_table"
        (i32.const 1)
        (call $get_func
            (global.get $wasm_instance)
            (i32.const 45) ;; "_it_writeStringTerm"
        )
    )
    (call $set_table
        (i32.const 72) ;; "_it_table"
        (i32.const 2)
        (call $get_func
            (global.get $wasm_instance)
            (i32.const 34) ;; "_it_strlen"
        )
    )
    (call $set_table
        (i32.const 72) ;; "_it_table"
        (i32.const 3)
        (call $get_func
            (global.get $wasm_instance)
            (i32.const 18) ;; "fizzbuzz"
        )
    )
)

;; Imports
(func $it_isFizz (export "isFizz") (param i32) (result i32)
    (call $isFizz (local.get 0))
)
(func $it_fizzStr (export "fizzStr") (param) (result i32)
    (call $stringToCpp (call $fizzStr))
)
(func $it_isBuzz (export "isBuzz") (param i32) (result i32)
    (call $isBuzz (local.get 0))
)
(func $it_buzzStr (export "buzzStr") (param) (result i32)
    (call $stringToCpp (call $buzzStr))
)
(func $it_log (export "log") (param i32) (result)
    (call $log (call $cppToString (local.get 0)))
)
(func $it_logInt (export "logInt") (param i32) (result)
    (call $logInt (local.get 0))
)

;; Exports
(func $fizzbuzz (export "fizzbuzz") (param i32)
    (call_indirect (type $i)
        (local.get 0)
        (i32.const 3) ;; fizzbuzz id
    )
)
