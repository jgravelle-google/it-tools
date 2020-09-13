#!/usr/bin/python

# Generates an ITL description and a vanilla .cpp from an annotated .cpp file

import argparse
import os
import sys
import traceback

tab = '    '
srcpath = os.path.dirname(__file__)
search_paths = ['.']

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('cpp_in', help='C++ file with CTL declarations')
    arg_parser.add_argument(
        '--cpp', dest='cpp_out', default=None,
        help='Output C++ file with CTL stripped and replaced with function declarations')
    arg_parser.add_argument(
        '--itl', dest='itl_out', default=None,
        help='Output ITL file')
    arg_parser.add_argument(
        '--wasm', dest='wasm_out', default=None,
        help='Oputput wasm file. This path is baked into the ITL file, so should be'
             ' overridden to match the core wasm module to be loaded')
    args = arg_parser.parse_args(sys.argv[1:])

    # Paths
    cpp_in = args.cpp_in
    search_paths.append(os.path.dirname(cpp_in))
    basename, _ = os.path.splitext(cpp_in)
    outpath = 'out' # default path for output files
    cpp_out = args.cpp_out
    if not cpp_out:
        cpp_out = os.path.join(outpath, cpp_in)
    itl_out = args.itl_out
    if not itl_out:
        itl_out = os.path.join(outpath, basename + '.itl')
    wasm_out = args.wasm_out
    if not wasm_out:
        # / instead of os.path.join because ITL expects / for paths
        wasm_out = outpath + '/' + basename + '.wasm'

    ctl = CTLReader(cpp_in)
    ctl.write_cpp(cpp_out)
    write_itl(ctl.ast, wasm_out, itl_out)

class CTLReader(object):
    start_str, end_str = '/**IT_START**/', '/**IT_END**/'
    def __init__(self, filename):
        for path in search_paths:
            pathname = os.path.join(path, filename)
            if os.path.exists(pathname):
                break
        contents = open(pathname).read()
        self.start = contents.find(CTLReader.start_str) + len(CTLReader.start_str)
        self.end = contents.find(CTLReader.end_str)
        self.it_contents = contents[self.start:self.end]
        self.ast = parse_it(self.it_contents)
        self.cpp_contents = (self.ast.cpp_extra +
            contents[:self.start-len(CTLReader.start_str)] +
            contents[self.end+len(CTLReader.end_str):])


        # Write compute import+export declarations
        type_decls = ''
        for ty in self.ast.types.values():
            type_decls += ty.cpp_type_decl()
        import_decls = ''
        for imp, funcs in self.ast.imports.items():
            import_decls += 'namespace {} {{\n'.format(imp)
            for func in funcs:
                attr = '__attribute__((import_module("{}"), import_name("{}")))'.format(imp, func.name)
                import_decls += tab + attr + ' ' + func.to_cpp() + ';\n'
            import_decls += '}\n'
        export_decls = ''
        for func in self.ast.exports:
            attr = '__attribute__((export_name("{}")))'.format(func.name)
            export_decls += attr + ' ' + func.to_cpp() + ';\n'
        self.it_decls = type_decls + import_decls + export_decls

    # Write output .cpp file
    def write_cpp(self, filename):
        template_path = os.path.join(srcpath, 'c_header_template.h')
        h_contents = open(template_path).read()
        h_contents = h_contents.replace('/**IT_DECLS**/', self.it_decls)
        contents = h_contents + self.cpp_contents
        write_file(filename, contents)

def write_itl(ast, wasm_out, itl_out):
    # TODO: extract this AST -> ITL logic to a shared ItlWriter class (?)
    itl_contents = ''

    # ITL Types
    itl_contents += '(types\n'
    for ty in ast.types.values():
        itl_contents += ty.itl_type_decl()
    itl_contents += ')\n'

    # ITL Imports
    for imp, funcs in ast.imports.items():
        itl_contents += '(import "{}"\n'.format(imp)
        for func in funcs:
            itl_contents += tab + func.to_it_decl() + '\n'
        itl_contents += ')\n'

    # Wasm module
    # declare imports on the core module
    itl_contents += '\n(module wasm "{}"\n'.format(wasm_out)
    # builtin exports to polyfill for WASI imports added by Emscripten
    itl_contents += (
        '    (import "wasi_snapshot_preview1"\n'
        '       (func _it_proc_exit "proc_exit" (param i32) (result)\n'
        '           (unreachable)\n'
        '       )\n'
        '    )\n'
    )
    for imp, funcs in ast.imports.items():
        itl_contents += tab + '(import "{}"\n'.format(imp)
        for func in funcs:
            itl_contents += func.to_itl_import()
        itl_contents += tab + ')\n'
    # C++ runtime builtin declarations
    def builtin(name, args, ret):
        return Func(name, FuncType([SimpleType(arg) for arg in args], SimpleType(ret)))
    builtins = [
        builtin('_it_malloc', ['string'], 's32'),
        builtin('_it_strlen', ['string'], 's32'),
        builtin('_it_writeStringTerm', ['string', 's32'], 'void'),
    ]
    for func in ast.exports + builtins:
        itl_contents += tab + func.to_it_decl() + '\n'
    itl_contents += ')\n\n'

    # ITL exports
    itl_contents += '(export\n'
    for func in ast.exports:
        itl_contents += func.to_itl_export()
    itl_contents += ')\n\n'

    # builtin helpers
    itl_contents += '''
(func _it_cppToString "" (param i32) (result string)
    ;; helper function to convert strings as a unary expression
    (mem-to-string wasm "memory"
        (local 0)
        (call _it_strlen (local 0))
    )
)
(func _it_stringToCpp "" (param string) (result i32)
    ;; helper function to convert strings as a unary expression
    (let (string-len (local 0)))
    (let (call _it_malloc (+ (local 1) 1)))
    (string-to-mem wasm "memory"
        (local 0) ;; str
        (local 2) ;; ptr
    )
    (call _it_writeStringTerm
        (local 2) ;; ptr
        (local 1) ;; len
    )
    (local 2) ;; ptr
)

(func _it_cppToBuffer "" (param i32) (result buffer)
    ;; helper function to convert buffer from struct to buffer
    (mem-to-buffer wasm "memory"
        (load u32 wasm "memory" (+ (local 0) 4))
        (load u32 wasm "memory" (local 0))
    )
)
(func _it_bufferToCpp "" (param buffer) (result i32)
    ;; helper function to convert buffers as a unary expression
    (let (buffer-len (local 0)))

    ;; allocate a C++ buffer, write bytes into it
    (let (call _it_malloc (local 1)))
    (buffer-to-mem wasm "memory"
        (local 0) ;; buff
        (local 2) ;; ptr
    )

    ;; allocate C++ Buffer struct
    (let (call _it_malloc 8))
    ;; store len
    (store u32 wasm "memory" (local 3) (local 1))
    ;; store ptr value
    (store u32 wasm "memory" (+ 4 (local 3)) (local 2))
    ;; return
    (local 3)
)

'''

    # adapter functions for structs
    for ty in ast.types.values():
        itl_contents += ty.itl_adapter_funcs()

    write_file(itl_out, itl_contents)

integer_types = ['u1', 's8', 'u8', 's16', 'u16', 's32', 'u32']
float_types = ['f32', 'f64']
numeric_types = integer_types + float_types

class AST(object):
    def __init__(self, imports, exports, types, cpp_extra):
        self.imports = imports
        self.exports = exports
        self.types = types
        self.cpp_extra = cpp_extra

class Func(object):
    def __init__(self, name, ty):
        assert(isinstance(ty, FuncType))
        self.name = name
        self.ty = ty

    def to_cpp(self):
        return self.ty.to_cpp(name=self.name)
    def to_wasm(self):
        args = [ty.to_wasm() for ty in self.ty.args]
        ret = self.ty.ret.to_wasm()
        return '(func {} "{}" (param {}) (result {}))'.format(
            self.name, self.name, ' '.join(args), ret)
    def to_it_decl(self):
        return self.ty.to_it(name='{0} "{0}"'.format(self.name))
    def to_itl_import(self):
        args = ' '.join(arg.to_wasm() for arg in self.ty.args)
        ret = self.ty.ret.to_wasm()
        contents = tab * 2 + '(func _it_{} "{}" (param {}) (result {})\n'.format(
            self.name, self.name, args, ret)
        args = ''
        n_locals = len(self.ty.args)
        for i, arg in enumerate(self.ty.args):
            local = '(local {})'.format(i)
            args += '\n' + tab * 4 + arg.lift(local, n_locals+1)
        contents += tab * 3 + '(let (call {}{}))\n'.format(self.name, args)
        body = self.ty.ret.lower('(local {})'.format(n_locals), n_locals+1)
        contents += tab * 3 + body + ')\n'
        return contents
    def to_itl_export(self):
        ret = self.ty.ret.to_it()
        contents = tab + '(func _it_{} "{}" (param {}) (result {})\n'.format(
            self.name, self.name, ' '.join([ty.to_it() for ty in self.ty.args]), ret)
        args = ''
        n_locals = len(self.ty.args)
        for i, arg in enumerate(self.ty.args):
            local = '(local {})'.format(i)
            args += '\n' + tab * 3 + arg.lower(local, n_locals+1)
        contents += tab * 2 + '(let (call {}{}))\n'.format(self.name, args)
        body = self.ty.ret.lift('(local {})'.format(n_locals), n_locals+1)
        contents += tab * 2 + body + '\n'
        contents += tab + ')\n'
        return contents

class Type(object):
    # base class for type system
    def to_cpp_array(self):
        # cpp type when used in arrays; special cased for StructTypes which are
        # Foo* when passed alone, and Array<Foo> in arrays
        return self.to_cpp()

class SimpleType(Type):
    mapping = {
        'u1': 'bool',
        's8': 'char',
        'u8': 'unsigned char',
        's16': 'short',
        'u16': 'unsigned short',
        's32': 'int',
        'u32': 'unsigned int',
        'f32': 'float',
        'f64': 'double',
        'string': 'const char*',
        'any': 'void*',
        'void': 'void',
        'buffer': 'ITBuffer*',
    }

    def __init__(self, ty):
        self.ty = ty

    def to_it(self):
        if self.ty == 'void':
            return ''
        return self.ty
    def to_cpp(self):
        return SimpleType.mapping[self.ty]
    def to_wasm(self):
        return {
            'void': '',
            'f32': 'f32',
        }.get(self.ty, 'i32')

    def lift(self, expr, n_locals):
        if self.ty in numeric_types:
            return '(as {} {})'.format(self.ty, expr)
        elif self.ty == 'string':
            return '(call _it_cppToString {})'.format(expr)
        elif self.ty == 'buffer':
            return '(call _it_cppToBuffer  {})'.format(expr)
        elif self.ty == 'any':
            return '(lift-ref {})'.format(expr)
        elif self.ty == 'void':
            return expr
        assert False

    def lower(self, expr, n_locals):
        if self.ty in integer_types:
            # TODO: handle 64bit ints
            return '(as i32 {})'.format(expr)
        elif self.ty in float_types:
            # currently all float types happen to match core wasm
            return '(as {} {})'.format(self.ty, expr)
        elif self.ty == 'string':
            return '(call _it_stringToCpp {})'.format(expr)
        elif self.ty == 'buffer':
            return '(call _it_bufferToCpp {})'.format(expr)
        elif self.ty == 'any':
            return '(lower-ref {})'.format(expr)
        elif self.ty == 'void':
            return expr
        assert False

    def sizeof(self):
        if self.ty in ['u1', 's8', 'u8']:
            return 1
        elif self.ty in ['u16', 's16']:
            return 2
        return 4

    def it_store_expr(self, ptr, val):
        if self.ty in ['buffer', 'string']:
            ty = 'u32'
        else:
            ty = self.ty
        return '(store {} wasm "memory" {} {})'.format(ty, ptr, val)
    def it_load_expr(self, ptr):
        if self.ty in ['buffer', 'string']:
            ty = 'u32'
        else:
            ty = self.ty
        return '(load {} wasm "memory" {})'.format(ty, ptr)

class StructType(Type):
    def __init__(self, name, fields):
        self.fields = fields
        assert name is not None
        self.name = name

    def to_it(self):
        return self.name
    def to_cpp(self):
        return self.name + '*'
    def to_cpp_array(self):
        return self.name
    def to_wasm(self):
        return 'i32'

    def lift(self, expr, n_locals):
        return '(call _it_lift_{} {})'.format(self.name, expr)
    def lower(self, expr, n_locals):
        return '(call _it_lower_{} {})'.format(self.name, expr)

    def sizeof(self):
        size = 0
        for ty in self.fields.values():
            size += ty.sizeof()
        return size

    def itl_type_decl(self):
        ret = tab + '(record {}\n'.format(self.name)
        for name, ty in self.fields.items():
            ret += tab * 2 + '({} {})\n'.format(name, ty.to_it())
        ret += tab + ')\n'
        return ret
    def itl_adapter_funcs(self):
        # lifting function: reads fields and stores on a new record object
        ret = '(func _it_lift_{} "" (param i32) (result any)\n'.format(self.name)
        ret += tab + '(make-record {}\n'.format(self.name)
        offset = 0
        for name, ty in self.fields.items():
            ptr = '(+ {} (local 0))'.format(offset)
            load = ty.it_load_expr(ptr)
            ret += tab*2 + '(field {} {})\n'.format(name, ty.lift(load, n_locals=2))
            offset += ty.sizeof()
        ret += tab + ')\n'
        ret += ')\n'

        # writeTo: helper function to write fields to a specific pointer in memory
        # used in lowering, but also for writing into arrays
        ret += '(func _it_writeTo_{} "" (param i32 any) (result i32)\n'.format(self.name)
        offset = 0
        for name, ty in self.fields.items():
            read = '(read-field {} {} (local 1))'.format(self.name, name)
            ptr = '(+ {} (local 0))'.format(offset)
            val = ty.lower(read, n_locals=2)
            ret += tab + ty.it_store_expr(ptr, val) + '\n'
            offset += ty.sizeof()
        ret += tab + '(local 0)\n'
        ret += ')\n'

        # lowering function: mallocs memory and writes into it
        ret += '(func _it_lower_{} "" (param any) (result i32)\n'.format(self.name)
        ret += tab + '(call _it_writeTo_{} (call _it_malloc {}) (local 0))\n'.format(
            self.name, self.sizeof())
        ret += ')\n'
        return ret
    def cpp_type_decl(self):
        ret = 'struct ' + self.name + ' {\n'
        # fields
        for name, ty in self.fields.items():
            ret += tab + '{} {};\n'.format(ty.to_cpp(), name)
        # default constructor
        ret += tab + '{}() {{}}\n'.format(self.name)
        # constructor w/ all fields initialized
        args = ''
        inits = ''
        for name, ty in self.fields.items():
            if args:
                args += ', '
                inits += ', '
            args += '{} _{}'.format(ty.to_cpp(), name)
            inits += '{0}(_{0})'.format(name)
        ret += tab + '{}({}) : {} {{}}\n'.format(self.name, args, inits)
        ret += '};\n'
        return ret

class EnumType(Type):
    def __init__(self, name, kinds):
        self.name = name
        self.kinds = kinds

    def to_it(self):
        return self.name
    def to_cpp(self):
        return self.name
    def to_wasm(self):
        return 'i32'

    def lift(self, expr, n_locals):
        return '(lift-enum {} {})'.format(self.name, expr)
    def lower(self, expr, n_locals):
        return '(lower-enum {} {})'.format(self.name, expr)

    def sizeof(self):
        return 4

    def itl_type_decl(self):
        ret = tab + '(enum {}\n'.format(self.name)
        for kind in self.kinds:
            ret += tab * 2 + kind + '\n'
        ret += tab + ')\n'
        return ret
    def itl_adapter_funcs(self):
        # no need for helper funcs
        return ''
    def cpp_type_decl(self):
        # base class
        ret = 'enum class {} {{\n'.format(self.name)
        for kind in self.kinds:
            ret += tab + kind + ',\n'
        ret += '};\n'
        return ret

    def it_store_expr(self, ptr, val):
        return '(store u32 wasm "memory" {} {})'.format(ptr, val)
    def it_load_expr(self, ptr):
        return '(load u32 wasm "memory" {})'.format(ptr)

class VariantType(Type):
    def __init__(self, name, kinds):
        assert name is not None
        self.name = name
        self.kinds = kinds

    def to_it(self):
        return self.name
    def to_cpp(self):
        return self.name + '*'
    def to_wasm(self):
        return 'i32'

    def lift(self, expr, n_locals):
        return '(call _it_lift_{} {})'.format(self.name, expr)
    def lower(self, expr, n_locals):
        return '(call _it_lower_{} {})'.format(self.name, expr)

    def sizeof(self):
        # the variant itself is always just a pointer (to a struct)
        return 4

    def itl_type_decl(self):
        # TODO
        return ''
    def itl_adapter_funcs(self):
        # TODO
        return ''
    def cpp_type_decl(self):
        # base class
        ret = 'class {} {{\n'.format(self.name)
        ret += 'protected:\n'
        ret += tab + 'enum _Kind {\n'
        for struct in self.kinds.values():
            ret += tab * 2 + struct.name + ',\n'
        ret += tab + '};\n'
        ret += tab + 'volatile _Kind kind;\n'
        ret += 'public:\n'
        ret += tab + self.name + '(_Kind _kind) : kind(_kind) {}\n'
        ret += '};\n'

        # sublcasses
        for struct in self.kinds.values():
            ret += 'struct {} : public {} {{\n'.format(struct.name, self.name)
            # fields
            for name, ty in struct.fields.items():
                ret += tab + '{} {};\n'.format(ty.to_cpp(), name)
            # constructor w/ all fields initialized
            args = ''
            inits = ''
            for name, ty in struct.fields.items():
                if args:
                    args += ', '
                    inits += ', '
                args += '{} _{}'.format(ty.to_cpp(), name)
                inits += '{0}(_{0})'.format(name)
            # base class constructor with _Kind enum set
            base = '{0}({0}::{1})'.format(self.name, struct.name)
            ret += tab + '{}({}) : {}, {} {{}}\n'.format(struct.name, args, base, inits)
            ret += '};\n'
        return ret

class FuncType(Type):
    def __init__(self, args, ret):
        for ty in args:
            assert(isinstance(ty, Type))
        assert(isinstance(ret, Type))
        self.args = args
        self.ret = ret

    def to_it(self, name=''):
        args = [arg.to_it() for arg in self.args]
        ret = self.ret.to_it()
        return '(func {} (param {}) (result {}))'.format(
            name, ' '.join(args), ret)
    def to_cpp(self, name='(*)'):
        ret_ty = self.ret.to_cpp()
        arg_tys = [arg.to_cpp() for arg in self.args]
        arg_str = ', '.join(arg_tys)
        return '{} {}({})'.format(ret_ty, name, arg_str)
    def to_wasm(self):
        return 'i32'

    def lift(self, expr, n_locals):
        fn = '(table-read wasm "__indirect_function_table" {})'.format(expr)
        args = ''
        for i, arg in enumerate(self.args):
            args += arg.lower('(local {})'.format(n_locals + i), n_locals + len(self.args))
        return '(lambda {} (call-expr {} {}))'.format(
            self.to_it(), fn, args)

class ArrayType(Type):
    def __init__(self, ty):
        assert(isinstance(ty, Type))
        self.ty = ty

    def to_it(self):
        return '(array {})'.format(self.ty.to_it())
    def to_cpp(self):
        return 'Buffer<{}>*'.format(self.ty.to_cpp_array())
    def to_wasm(self):
        return 'i32'

    def lift(self, expr, n_locals):
        size = self.ty.sizeof()
        ptr = '(local {})'.format(n_locals)
        if isinstance(self.ty, StructType):
            # structs are passed inline with the array memory, so no need to load
            body = ptr
        else:
            body = self.ty.it_load_expr(ptr)
        # args are: type, stride, ptr, count, body
        return ('(lift-array {} {} '.format(self.ty.to_it(), size) +
            '(load u32 wasm "memory" (+ {} 4)) '.format(expr) +
            '(/ (load u32 wasm "memory" {}) {}) '.format(expr, size) +
            self.ty.lift(body, n_locals+1) +
        ')')
    def lower(self, expr, n_locals):
        # this is complicated
        # need to do all this in a single expression, meaning we make a lambda
        arr_ptr = '(local {})'.format(n_locals)
        expr_local = '(local {})'.format(n_locals+1)
        # lower-array will also introduce two new locals
        ptr = '(local {})'.format(n_locals+2)
        val = '(local {})'.format(n_locals+3)
        size = self.ty.sizeof()
        if isinstance(self.ty, StructType):
            body = '(call _it_writeTo_{} {} {})'.format(self.ty.name, ptr, val)
        else:
            # structs are passed inline with the array memory, so no need to load
            body = self.ty.lower(self.ty.it_store_expr(ptr, val), n_locals+4)
        # args to lower-array are: type, stride, ptr, array, body
        array = ('(lower-array {} {} '.format(self.ty.to_it(), size) +
            '(call _it_malloc (* {} (array-len {}))) '.format(size, expr_local) +
            expr_local + ' ' +
            body +
        ')')
        lam_body = ('(store u32 wasm "memory" {} (* {} (array-len {}))) '.format(arr_ptr, size, expr_local) +
            '(store u32 wasm "memory" (+ 4 {}) {}) '.format(arr_ptr, array) +
            arr_ptr)
        lam_ty = FuncType([SimpleType('s32'), SimpleType('any')], self)
        return '(call-expr (lambda {} {}) (call _it_malloc 8) {})'.format(lam_ty.to_it(), lam_body, expr)

def parse_it(contents):
    tokens = Lexer(contents).lex()
    ast = Parser(tokens).parse()
    return ast

class Lexer(object):
    def __init__(self, contents):
        self.tokens = []
        self.i = 0
        self.cur = ''
        self.contents = contents

    def term(self):
        # helper function to end token
        if self.cur:
            self.tokens.append(self.cur)
        self.cur = ''

    def peek(self):
        return self.contents[self.i];
    def pop(self):
        ret = self.peek()
        self.i += 1
        return ret

    def lex(self):
        while self.i < len(self.contents):
            c = self.pop()
            if c == '/' and self.peek() == '/':
                self.pop()
                self.term()
                while self.peek() not in '\n\r':
                    self.pop()
            elif c in ' \n\r\t':
                self.term()
            elif c in '(){},;:':
                self.term()
                self.tokens.append(c)
            else:
                self.cur += c
        self.term()
        return self.tokens

class Parser(object):
    def __init__(self, tokens):
        self.i = 0
        self.tokens = tokens

    def parse(self):
        imports = {}
        exports = []
        cpp_extra = ''
        self.types = {}
        while self.i < len(self.tokens):
            head = self.pop()
            if head == 'export':
                self.expect('{')
                while True:
                    if self.peek() == 'func':
                        exports.append(self.parse_func())
                    else:
                        self.expect('}')
                        break
            elif head == 'import':
                name, funcs = self.parse_import()
                self.add_import(imports, name, funcs)
            elif head == 'type':
                name = self.pop()
                self.expect('=')
                self.types[name] = self.parse_type(name)
            elif head == 'include':
                file = unquote(self.pop())
                reader = CTLReader(file)
                for k, v in reader.ast.imports.items():
                    self.add_import(imports, k, v)
                for ex in reader.ast.exports:
                    exports.append(ex)
                for k, v in reader.ast.types.items():
                    self.types[k] = v
                cpp_extra += reader.cpp_contents
            else:
                assert False, 'unknown top-level stmt'
        return AST(imports, exports, self.types, cpp_extra)

    def add_import(self, imports, name, funcs):
        if name not in imports:
            imports[name] = funcs
        else:
            for fun in funcs:
                for f in imports[name]:
                    if f.name == fun.name:
                        break
                else:
                    imports[name].append(fun)

    def parse_import(self):
        name = self.pop()
        self.expect('{')
        funcs = []
        while True:
            if self.peek() == 'func':
                funcs.append(self.parse_func())
            else:
                self.expect('}')
                break
        return name, funcs

    def parse_func(self):
        self.expect('func')
        name = self.pop()

        ty = self.parse_func_type()
        self.expect(';')
        return Func(name, ty)

    def parse_type(self, name=None):
        kind = self.pop()
        if kind == 'func':
            return self.parse_func_type()
        elif kind == 'struct':
            fields = self.parse_struct_body()
            return StructType(name, fields)
        elif kind == 'enum':
            return self.parse_enum(name)
        elif kind == 'variant':
            return self.parse_variant(name)
        elif kind == 'array':
            self.expect('(')
            ty = self.parse_type()
            self.expect(')')
            return ArrayType(ty)
        elif kind in self.types:
            return self.types[kind]
        else:
            return SimpleType(kind)

    def parse_func_type(self):
        # assumption: we have already popped `func` or `func [name]`

        # parse args in ()s
        args = []
        self.expect('(')
        while self.peek() != ')':
            args.append(self.parse_type())
            if self.peek() != ')':
                self.expect(',')
        self.expect(')')

        # return type, or void
        if self.check('->'):
            ret = self.parse_type()
        else:
            ret = SimpleType('void')
        return FuncType(args, ret)

    def parse_struct_body(self):
        # parses the body of a struct declaration between {}s
        # also used for variant branches
        self.expect('{')
        fields = {}
        while self.peek() != '}':
            field_name = self.pop()
            self.expect(':')
            ty = self.parse_type()
            self.expect(';')
            fields[field_name] = ty
        self.expect('}')
        return fields

    def parse_enum(self, name):
        self.expect('{')
        kinds = []
        while self.peek() != '}':
            kind = self.pop()
            self.expect(',')
            kinds.append(kind)
        self.expect('}')
        return EnumType(name, kinds)

    def parse_variant(self, name):
        self.expect('{')
        kinds = {}
        while self.peek() != '}':
            kind_name = self.pop()
            fields = self.parse_struct_body()
            kinds[kind_name] = StructType(kind_name, fields)
        self.expect('}')
        return VariantType(name, kinds)

    # Helper funcs
    def peek(self):
        return self.tokens[self.i]
    def pop(self):
        ret = self.peek()
        self.i += 1
        return ret
    def check(self, tok):
        if self.peek() == tok:
            return self.pop()
        return None
    def expect(self, tok):
        assert self.pop() == tok, 'Expected "{}", got "{}"'.format(tok, self.tokens[self.i])
    def until(self, tok):
        ret = []
        while self.peek() != tok:
            ret.append(self.pop())
        self.expect(tok)
        return ret

def unquote(name):
    assert(name[0] == '"' and name[-1] == '"')
    return name[1:-1]

def ensure_path(path):
    try:
        os.makedirs(path)
    except:
        pass
def ensure_path_for(filepath):
    ensure_path(os.path.dirname(filepath))
def write_file(filename, contents):
    ensure_path_for(filename)
    open(filename, 'w').write(contents)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        trace = traceback.format_exc(e)
        print(trace)
        sys.exit(1)
