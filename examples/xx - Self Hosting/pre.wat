(import "foo" "bar" (func $bar (param i32 i32) (result i32)))

(func (export "baz") (param i32) (result i32)
    (call $bar (local.get 0) (i32.const 2))
)
