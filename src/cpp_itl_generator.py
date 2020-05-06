#!/usr/bin/python

# Generates an ITL description and a vanilla .cpp from an annotated .cpp file

import os
import sys
import traceback

def main():
    srcpath = os.path.dirname(__file__)
    outpath = 'out'
    ensure_path(outpath)

    # Paths
    cpp_in = sys.argv[1]
    basename, _ = os.path.splitext(cpp_in)
    # h_out = os.path.join(outpath, basename + '_impl.h')
    h_out = outpath + '/' + basename + '_impl.h'
    cpp_out = os.path.join(outpath, cpp_in)
    itl_out = os.path.join(outpath, basename + '.itl')
    wasm_out = outpath + '/' + basename + '.wasm'

    # read + parse
    contents = open(cpp_in).read()
    start_str, end_str = '/**IT_START**/', '/**IT_END**/'
    start = contents.find(start_str) + len(start_str)
    end = contents.find(end_str)
    it_contents = contents[start:end]
    ast = parse_it(it_contents)

    #############################################

    # Write output .cpp file
    cpp_contents = (
        contents[:start-len(start_str)] +
        # Add an include to the generated header file
        '#include "' + h_out + '"\n' +
        contents[end+len(end_str):]
    )
    open(cpp_out, 'w').write(cpp_contents)

    #############################################

    # Write .h file
    template_path = os.path.join(srcpath, 'c_header_template.h')
    h_contents = open(template_path).read()
    def it_to_cpp_ty(ty):
        mapping = {
            'u1': 'bool',
            's32': 'int',
            'string': 'const char*',
            'void': 'void',
        }
        return mapping[ty]
    def it_to_cpp_func(func):
        ret_ty = it_to_cpp_ty(func.ret)
        arg_tys = [it_to_cpp_ty(arg) for arg in func.args]
        arg_str = ', '.join(arg_tys)
        return '{} {}({});\n'.format(ret_ty, func.name, arg_str)
    import_decls = ''
    for imp, funcs in ast.imports.iteritems():
        for func in funcs:
            attr = '__attribute__((import_module("{}"), import_name("{}")))'.format(imp, func.name)
            import_decls += attr + ' ' + it_to_cpp_func(func)
    h_contents = h_contents.replace('/**IMPORT_DECLS**/', import_decls)
    export_decls = ''
    for func in ast.exports:
        attr = '__attribute__((export_name("{}")))'.format(func.name)
        export_decls += attr + ' ' + it_to_cpp_func(func)
    h_contents = h_contents.replace('/**EXPORT_DECLS**/', export_decls)
    open(h_out, 'w').write(h_contents)

    #############################################

    # Write .itl file
    tab = '    '
    itl_contents = ''

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
    for imp, funcs in ast.imports.iteritems():
        itl_contents += '(import "{}"\n'.format(imp)
        for func in funcs:
            ret = func.ret if func.ret != 'void' else ''
            itl_contents += tab + '(func {} "{}" (param {}) (result {}))\n'.format(
                func.name, func.name, ' '.join(func.args), ret)
        itl_contents += ')\n'

    # Wasm module
    def lift(ty, expr):
        # C++ -> IT
        if ty in ['u1', 's32']:
            return '(as {} {})'.format(ty, expr)
        elif ty == 'string':
            return '(call _it_cppToString {})'.format(expr)
        elif ty == 'void':
            return expr
        assert False, 'unknown lifting type: ' + ty
    def lower(ty, expr):
        if ty in ['u1', 's32']:
            return '(as i32 {})'.format(expr)
        elif ty == 'string':
            return '(call _it_stringToCpp {})'.format(expr)
        elif ty == 'void':
            return expr
        assert False, 'unknown lowering type: ' + ty
    itl_contents += '\n(module wasm "{}"\n'.format(wasm_out)
    for imp, funcs in ast.imports.iteritems():
        itl_contents += tab + '(import "{}"\n'.format(imp)
        for func in funcs:
            ret = func.ret if func.ret != 'void' else ''
            itl_contents += tab * 2 + '(func _ "{}" (param {}) (result {})\n'.format(
                func.name, ' '.join(func.args), ret)
            args = ''
            for i, arg in enumerate(func.args):
                local = '(local {})'.format(i)
                args += '\n' + tab * 4 + lift(arg, local)
            call = '(call {}{})'.format(func.name, args)
            body = lower(func.ret, call)
            itl_contents += tab * 3 + body + ')\n'
        itl_contents += tab + ')\n'
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
        itl_contents += tab + '(func _ "{}" (param {}) (result {})\n'.format(
            func.name, ' '.join(func.args), ret)
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
    (let (call malloc (+ (string-len (local 0)) 1)))
    (string-to-mem wasm "memory"
        (local 0) ;; str
        (local 1) ;; ptr
    )
    (call _it_writeStringTerm
        (local 1)
        (string-len (local 0))
    )
    (local 1)
)

'''

    open(itl_out, 'w').write(itl_contents)

class AST(object):
    def __init__(self, imports, exports):
        self.imports = imports
        self.exports = exports
class Func(object):
    def __init__(self, name, args, ret):
        self.name = name
        self.args = args
        self.ret = ret

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

    def lex(self):
        while self.i < len(self.contents):
            c = self.contents[self.i]
            self.i += 1
            if c in ' \n\r\t':
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
                name = unquote(self.pop())
                self.expect('{')
                funcs = []
                while True:
                    if self.peek() == 'func':
                        funcs.append(self.parse_func())
                    else:
                        self.expect('}')
                        break
                imports[name] = funcs
            else:
                assert False, 'unknown top-level stmt'
        return AST(imports, exports)

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

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        trace = traceback.format_exc(e)
        print trace
        sys.exit(1)
