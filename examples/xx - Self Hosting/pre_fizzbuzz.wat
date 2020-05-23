(import "buzz" "isBuzz" (func $isBuzz (param i32) (result i32)))
(import "buzz" "buzzStr" (func $buzzStr (param) (result i32)))
(import "buzz" "_it_strlen" (func $buzz_strlen (param i32) (result i32)))

;; IT `string` memory is managed by the _it runtime
(import "_it_runtime" "string-len" (func $string_len (param i32) (result i32)))
;; mem-to-string passes the memory ID to the runtime, in addition to ptr+len,
;; returns string ID
(import "_it_runtime" "mem-to-string"
    (func $mem_to_string (param i32 i32 i32) (result i32)))
;; args: memID, string, ptr
(import "_it_runtime" "string-to-mem"
    (func $string_to_mem (param i32 i32 i32)))
(import "_it_runtime" "table" (table 0 funcref))
(type $i_i (func (param i32) (result i32)))
(type $ii (func (param i32 i32) (result)))

(func $malloc (param i32) (result i32)
    (call_indirect (type $i_i)
        (local.get 0)
        (i32.const 1) ;; malloc id
    )
)
(func $_it_writeStringTerm (param i32 i32)
    (call_indirect (type $ii)
        (local.get 0)
        (local.get 1)
        (i32.const 2) ;; _it_writeStringTerm id
    )
)

(global $buzz_memory i32 (i32.const 0))
(global $fizzbuzz_memory i32 (i32.const 2))

;; Fused lift+lower adapters
(func $it_isBuzz (export "isBuzz") (param i32) (result i32)
    (call $isBuzz (local.get 0))
)
(func $it_buzzStr (export "buzzStr") (param) (result i32)
    (local i32 i32 i32 i32)
    (local.set 0 (call $buzzStr)) ;; CStr
    (local.set 1 (call $mem_to_string (global.get $buzz_memory)
        (local.get 0)
        (call $buzz_strlen (local.get 0))
    )) ;; IT string
    (local.set 2 (call $string_len (local.get 1)))
    (local.set 3 (call $malloc (i32.add (local.get 2) (i32.const 1))))
    (call $string_to_mem (global.get $fizzbuzz_memory)
        (local.get 1) ;; str
        (local.get 3) ;; ptr
    )
    (call $_it_writeStringTerm
        (local.get 3) ;; ptr
        (local.get 2) ;; len
    )
    (local.get 3) ;; ptr
)
