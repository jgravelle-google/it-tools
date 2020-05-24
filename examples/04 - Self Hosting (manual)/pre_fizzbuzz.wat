;; IT `string` is passed as `anyref`
(import "fizz" "isFizz" (func $isFizz (param i32) (result i32)))
(import "fizz" "fizzStr" (func $fizzStr (param) (result anyref)))
(import "buzz" "isBuzz" (func $isBuzz (param i32) (result i32)))
(import "buzz" "buzzStr" (func $buzzStr (param) (result anyref)))
(import "console" "log" (func $log (param anyref)))
(import "console" "logInt" (func $logInt (param i32)))

(import "_it_runtime" "string-len" (func $string_len (param anyref) (result i32)))
(import "_it_runtime" "mem-to-string" (func $mem_to_string (param i32 i32) (result anyref)))
(import "_it_runtime" "string-to-mem" (func $string_to_mem (param anyref i32)))

(table (export "table") 4 funcref)
(type $i (func (param i32)))
(type $i_i (func (param i32) (result i32)))
(type $ii (func (param i32 i32)))

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
        (local.get 0)
        (call $_it_strlen (local.get 0))
    )
)
(func $stringToCpp (param anyref) (result i32)
    (local i32 i32)
    (local.set 1 (call $string_len (local.get 0)))
    (local.set 2 (call $malloc (i32.add (local.get 1) (i32.const 1))))
    (call $string_to_mem
        (local.get 0) ;; str
        (local.get 2) ;; ptr
    )
    (call $_it_writeStringTerm
        (local.get 2) ;; ptr
        (local.get 1) ;; len
    )
    (local.get 2) ;; ptr
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
