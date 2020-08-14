#!/usr/bin/python

# Generates an ITL description and a vanilla .cpp from an annotated .cpp file

import argparse
import os
import sys
import traceback

tab = '    '

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

    srcpath = os.path.dirname(__file__)

    # Paths
    cpp_in = args.cpp_in
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

    def write_file(filename, contents):
        ensure_path_for(filename)
        open(filename, 'w').write(contents)

    # read + parse
    contents = open(cpp_in).read()
    start_str, end_str = '/**IT_START**/', '/**IT_END**/'
    start = contents.find(start_str) + len(start_str)
    end = contents.find(end_str)
    it_contents = contents[start:end]
    ast = parse_it(it_contents)

    #############################################

    # Write compute import+export declarations
    template_path = os.path.join(srcpath, 'c_header_template.h')
    h_contents = open(template_path).read()
    import_decls = ''
    for imp, funcs in ast.imports.items():
        for func in funcs:
            attr = '__attribute__((import_module("{}"), import_name("{}")))'.format(imp, func.name)
            import_decls += attr + ' ' + func.to_cpp()
    h_contents = h_contents.replace('/**IMPORT_DECLS**/', import_decls)
    export_decls = ''
    for func in ast.exports:
        attr = '__attribute__((export_name("{}")))'.format(func.name)
        export_decls += attr + ' ' + func.to_cpp()
    for ty, funcs in ast.types.items():
        print('TYPES', ty)
    h_contents = h_contents.replace('/**EXPORT_DECLS**/', export_decls)

    #############################################

    # Write output .cpp file
    cpp_contents = (
        contents[:start-len(start_str)] +
        h_contents +
        # Add an include to the generated header file
        # '#include "' + h_out + '"\n' +
        contents[end+len(end_str):]
    )
    write_file(cpp_out, cpp_contents)

    #############################################

    # Write .itl file
    # TODO: extract this AST -> ITL logic to an ItlWriter class
    itl_contents = ''

    # ITL Types
    itl_contents += '(types\n'
    for struct in ast.types.values():
        itl_contents += tab + '(record {}\n'.format(struct.name)
        for name, ty in struct.fields:
            itl_contents += tab * 2 + '({} {})\n'.format(name, ty)
        itl_contents += tab + ')\n'
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

    write_file(itl_out, itl_contents)

integer_types = ['u1', 's8', 'u8', 's16', 'u16', 's32', 'u32']
float_types = ['f32', 'f64']
numeric_types = integer_types + float_types
def lift(ty, expr):
    # C++ -> IT
    if isinstance(ty, FuncType):
        # TODO
        return '(lift {})'.format(ty.to_it())
    if ty.ty in numeric_types:
        return '(as {} {})'.format(ty.ty, expr)
    elif ty.ty == 'string':
        return '(call _it_cppToString {})'.format(expr)
    elif ty.ty == 'buffer':
        return '(call _it_cppToBuffer  {})'.format(expr)
    elif ty.ty == 'void':
        return expr
    struct = ast.types.get(ty.ty)
    assert struct, 'unknown lifting type: ' + ty.ty
    return '(make-record {})'.format(ty.ty)
def lower(ty, expr):
    if isinstance(ty, FuncType):
        # TODO
        return '(lower {})'.format(ty.to_it())
    if ty.ty in integer_types:
        # TODO: handle 64bit ints
        return '(as i32 {})'.format(expr)
    elif ty.ty in float_types:
        # currently all float types happen to match core wasm
        return '(as {} {})'.format(ty.ty, expr)
    elif ty.ty == 'string':
        return '(call _it_stringToCpp {})'.format(expr)
    elif ty.ty == 'buffer':
        return '(call _it_bufferToCpp {})'.format(expr)
    elif ty.ty == 'void':
        return expr
    assert False, 'unknown lowering type: ' + ty.ty

class AST(object):
    def __init__(self, imports, exports, types):
        self.imports = imports
        self.exports = exports
        self.types = types

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
        args = [ty.to_it() for ty in self.ty.args]
        ret = self.ty.ret.to_it()
        return '(func {} "{}" (param {}) (result {}))'.format(
            self.name, self.name, ' '.join(args), ret)
    def to_itl_import(self):
        args = ' '.join(arg.to_wasm() for arg in self.ty.args)
        ret = self.ty.ret.to_wasm()
        contents = tab * 2 + '(func _it_{} "{}" (param {}) (result {})\n'.format(
            self.name, self.name, args, ret)
        args = ''
        for i, arg in enumerate(self.ty.args):
            local = '(local {})'.format(i)
            args += '\n' + tab * 4 + lift(arg, local)
        call = '(call {}{})'.format(self.name, args)
        body = lower(self.ty.ret, call)
        contents += tab * 3 + body + ')\n'
        return contents
    def to_itl_export(self):
        ret = self.ty.ret.to_it()
        contents = tab + '(func _it_{} "{}" (param {}) (result {})\n'.format(
            self.name, self.name, ' '.join([ty.to_it() for ty in self.ty.args]), ret)
        args = ''
        for i, arg in enumerate(self.ty.args):
            local = '(local {})'.format(i)
            args += '\n' + tab * 3 + lower(arg, local)
        call = '(call {}{})'.format(self.name, args)
        body = lift(self.ty.ret, call)
        contents += tab * 2 + body + '\n'
        contents += tab + ')\n'
        return contents

class Struct(object):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

class Type(object):
    # base class for type system
    pass

class SimpleType(Type):
    def __init__(self, ty):
        self.ty = ty

    def to_it(self):
        if self.ty == 'void':
            return ''
        return self.ty
    def to_cpp(self):
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
            'void': 'void',
            'buffer': 'ITBuffer*',
        }
        return mapping[self.ty]
    def to_wasm(self):
        if self.ty == 'void':
            return ''
        return 'i32'

class FuncType(Type):
    def __init__(self, args, ret):
        for ty in args:
            assert(isinstance(ty, Type))
        assert(isinstance(ret, Type))
        self.args = args
        self.ret = ret

    def to_it(self):
        args = [arg.to_it() for arg in self.args]
        ret = self.ret.to_it()
        return '<<functype : {} -> {}>>'.format(args, ret)
    def to_cpp(self, name=''):
        ret_ty = self.ret.to_cpp()
        arg_tys = [arg.to_cpp() for arg in self.args]
        arg_str = ', '.join(arg_tys)
        return '{} {}({});\n'.format(ret_ty, name, arg_str)
    def to_wasm(self):
        return 'i32'

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
            elif c in '(){},;':
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
        types = {}
        while self.i < len(self.tokens):
            head = self.pop()
            if head == 'export':
                self.expect('{')
                while True:
                    if self.peek() == 'func':
                        exports.append(self.parse_func())
                    elif self.peek() == 'type':
                        ty = self.parse_type_decl()
                        types[ty.name] = ty
                    else:
                        self.expect('}')
                        break
            elif head == 'import':
                name, funcs = self.parse_import()
                imports[name] = funcs
            else:
                assert False, 'unknown top-level stmt'
        return AST(imports, exports, types)

    def parse_import(self):
        name = unquote(self.pop())
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

    def parse_type(self):
        kind = self.pop()
        if kind == 'func':
            return self.parse_func_type()
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

    def parse_type_decl(self):
        self.expect('type')
        name = self.pop()
        self.expect('=')
        kind = self.pop()
        if kind == 'struct':
            self.expect('{')
            body = self.until('}')
            i = 0
            fields = []
            while i < len(body):
                ty = body[i]
                field_name = body[i+1]
                assert body[i+2] == ';'
                i += 3
                fields.append((ty, field_name))
            return Struct(name, fields)
        assert False, 'unknown type: ' + kind

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

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        trace = traceback.format_exc(e)
        print(trace)
        sys.exit(1)
