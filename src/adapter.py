#!/usr/bin/python

# Generates a JS adapter module from an IDL file

import os
import sys

import itl_parser

def ensure_path(path):
    try:
        os.makedirs(path)
    except:
        pass

itl_path = sys.argv[1]
itl_filename = os.path.basename(itl_path)
basename, _ = os.path.splitext(itl_filename)
contents = open(itl_path).read()
ast = itl_parser.parse(contents)

outpath = 'out'
ensure_path(outpath)

def it_to_cpp_ty(ty):
    TYPES = {
        'u1': 'bool',
        's32': 'int',
        'string': 'const char*',
    }
    return TYPES[ty]

# Implementation header, for use by the module itself
def write_header():
    header_path = os.path.join(outpath, basename + '_impl.h')
    template_path = os.path.join('src', 'c_header_template.h')
    header = open(template_path).read()
    export_decls = ''
    for func in ast.exports:
        attr = '__attribute__((export_name("{}")))'.format(func.name)
        ret_ty = it_to_cpp_ty(func.results[0])
        arg_tys = [it_to_cpp_ty(param) for param in func.params]
        arg_str = ', '.join(arg_tys)
        export_decls += '{} {} {}({});\n'.format(attr, ret_ty, func.name, arg_str)
    header = header.replace('/**EXPORT_DECLS**/', export_decls)
    open(header_path, 'w').write(header)
    print('Wrote header', header_path)

# NodeJS wrapper module
num_locals = 0
def write_js_module():
    global num_locals # thanks python
    def escape(s):
        return s.replace('\\', '/')
    def expr(sexpr):
        global num_locals
        assert(len(sexpr) > 0)
        head = sexpr[0]
        if head == 'as':
            assert(len(sexpr) == 3)
            return expr(sexpr[2])
        elif head == 'local':
            assert(len(sexpr) == 2)
            return 'x' + sexpr[1]
        elif head == 'call-export':
            assert(len(sexpr) >= 3)
            mod_name = sexpr[1]
            fn = sexpr[2]
            args = ', '.join([expr(x) for x in sexpr[3:]])
            return '{}[{}]({})'.format(mod_name, fn, args)
        elif head == 'let':
            assert(len(sexpr) == 2)
            local = 'x' + str(num_locals)
            num_locals += 1
            ex = expr(sexpr[1])
            return 'let {} = {}'.format(local, ex)
        elif head == 'mem-to-string':
            assert(len(sexpr) == 5)
            mod = sexpr[1]
            mem = sexpr[2]
            ptr = expr(sexpr[3])
            length = expr(sexpr[4])
            return 'memToString({}[{}], {}, {})'.format(mod, mem, ptr, length)
        else:
            assert(False)

    # Paths and setup
    js_path = os.path.join(outpath, basename + '.js')
    template_path = os.path.join('src', 'wrapper_module_template.js')
    js_str = open(template_path).read()
    tab = '    '

    # TODO: imports
    # imports = ''
    # js_str = js_str.replace('/**IMPORTS**/\n', imports)

    module_names = ''
    load_modules = ''        
    for mod in ast.modules:
        name = mod.name
        path = mod.path
        module_names += tab * 2 + 'let {};'.format(name)
        load_modules += tab * 2 + '{} = await loadModule({}, {{}})'.format(name, path)
    js_str = js_str.replace('/**MODULE_NAMES**/', module_names)
    js_str = js_str.replace('/**LOAD_MODULES**/', load_modules)

    exports = ''
    for func in ast.exports:
        params = ', '.join(['x' + str(i) for i in range(len(func.params))])
        exports += tab * 3 + '{}: function({}) {{\n'.format(func.name, params)
        num_locals = len(func.params)
        for i in range(len(func.body)):
            sexpr = func.body[i]
            exports += tab * 4
            if func.results and i == len(func.body) - 1:
                exports += 'return ' + expr(sexpr)
            else:
                exports += expr(sexpr)
            exports += ';\n'

        exports += tab * 3 + '},\n'
    js_str = js_str.replace('/**EXPORTS**/\n', exports)
    open(js_path, 'w').write(js_str)
    print('Wrote JS module', js_path)

write_header()
write_js_module()
