#!/usr/bin/python

# Generates an ITL description and a vanilla .cpp from an annotated .cpp file

import argparse
import os
import sys
import traceback

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
    def it_to_cpp_ty(ty):
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
            'buffer': 'ITBuffer',
        }
        return mapping.get(ty, ty)
    def it_to_cpp_func(func):
        ret_ty = it_to_cpp_ty(func.ret)
        arg_tys = [it_to_cpp_ty(arg) for arg in func.args]
        arg_str = ', '.join(arg_tys)
        return '{} {}({});\n'.format(ret_ty, func.name, arg_str)
    import_decls = ''
    for imp, funcs in ast.imports.items():
        for func in funcs:
            attr = '__attribute__((import_module("{}"), import_name("{}")))'.format(imp, func.name)
            import_decls += attr + ' ' + it_to_cpp_func(func)
    h_contents = h_contents.replace('/**IMPORT_DECLS**/', import_decls)
    export_decls = ''
    for func in ast.exports:
        attr = '__attribute__((export_name("{}")))'.format(func.name)
        export_decls += attr + ' ' + it_to_cpp_func(func)
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
    tab = '    '
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
    def it_to_wasm_ty(ty):
        if ty == 'void':
            return ''
        return 'i32'
    def it_to_wasm_func(func):
        args = [it_to_wasm_ty(ty) for ty in func.args]
        ret = it_to_wasm_ty(func.ret) if func.ret != 'void' else ''
        return '(func {} "{}" (param {}) (result {}))'.format(
            func.name, func.name, ' '.join(args), ret)
    for imp, funcs in ast.imports.items():
        itl_contents += '(import "{}"\n'.format(imp)
        for func in funcs:
            ret = func.ret if func.ret != 'void' else ''
            itl_contents += tab + '(func {} "{}" (param {}) (result {}))\n'.format(
                func.name, func.name, ' '.join(func.args), ret)
        itl_contents += ')\n'

    # Wasm module
    integer_types = ['u1', 's8', 'u8', 's16', 'u16', 's32', 'u32']
    float_types = ['f32', 'f64']
    numeric_types = integer_types + float_types
    def lift(ty, expr):
        # C++ -> IT
        if ty in numeric_types:
            return '(as {} {})'.format(ty, expr)
        elif ty == 'string':
            return '(call _it_cppToString {})'.format(expr)
        elif ty == 'buffer':
            return '(call _it_cppToBuffer  {})'.format(expr)
        elif ty == 'void':
            return expr
        struct = ast.types.get(ty)
        assert struct, 'unknown lifting type: ' + ty
        return '(make-record {})'.format(ty)
    def lower(ty, expr):
        if ty in integer_types:
            return '(as i32 {})'.format(expr)
        elif ty in float_types:
            # currently all float types happen to match core wasm
            return '(as {} {})'.format(ty, expr)
        elif ty == 'string':
            return '(call _it_stringToCpp {})'.format(expr)
        elif ty == 'void':
            return expr
        assert False, 'unknown lowering type: ' + ty
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
            args = ' '.join(it_to_wasm_ty(arg) for arg in func.args)
            ret = it_to_wasm_ty(func.ret) if func.ret != 'void' else ''
            itl_contents += tab * 2 + '(func _it_{} "{}" (param {}) (result {})\n'.format(
                func.name, func.name, args, ret)
            args = ''
            for i, arg in enumerate(func.args):
                local = '(local {})'.format(i)
                args += '\n' + tab * 4 + lift(arg, local)
            call = '(call {}{})'.format(func.name, args)
            body = lower(func.ret, call)
            itl_contents += tab * 3 + body + ')\n'
        itl_contents += tab + ')\n'
    # C++ runtime builtin declarations
    builtins = [
        Func('malloc', ['string'], 's32'),
        Func('_it_strlen', ['string'], 's32'),
        Func('_it_writeStringTerm', ['string', 's32'], 'void'),
    ]
    for func in ast.exports + builtins:
        itl_contents += tab + it_to_wasm_func(func) + '\n'
    itl_contents += ')\n\n'

    # ITL exports
    itl_contents += '(export\n'
    for func in ast.exports:
        ret = func.ret if func.ret != 'void' else ''
        itl_contents += tab + '(func _it_{} "{}" (param {}) (result {})\n'.format(
            func.name, func.name, ' '.join(func.args), ret)
        args = ''
        for i, arg in enumerate(func.args):
            local = '(local {})'.format(i)
            args += '\n' + tab * 3 + lower(arg, local)
        call = '(call {}{})'.format(func.name, args)
        body = lift(func.ret, call)
        itl_contents += tab * 2 + body + '\n'
        itl_contents += tab + ')\n'
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
    (let (call malloc (+ (local 1) 1)))
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

'''

    write_file(itl_out, itl_contents)

class AST(object):
    def __init__(self, imports, exports, types):
        self.imports = imports
        self.exports = exports
        self.types = types
class Func(object):
    def __init__(self, name, args, ret):
        self.name = name
        self.args = args
        self.ret = ret
class Struct(object):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

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
                        ty = self.parse_type()
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
        self.expect('(')

        args = self.until(')')
        if len(args):
            # validate comma-separated arguments
            assert len(args) % 2 == 1, 'unbalanced commas and args : ' + str(args)
            args, commas = args[::2], args[1::2]
            assert all(x == ',' for x in commas), 'args must be comma-separated : ' + str(args)

        if self.check('->'):
            ret = self.pop()
        else:
            ret = 'void'
        self.expect(';')
        return Func(name, args, ret)


    def parse_type(self):
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
