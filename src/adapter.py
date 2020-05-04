#!/usr/bin/python

# Generates a JS adapter module from an IDL file
# TODO: split JS and .h generation to two scripts

import os
import sys
import traceback

import itl_parser

outpath = 'out'
itl_path = sys.argv[1]
itl_filename = os.path.basename(itl_path)
basename, _ = os.path.splitext(itl_filename)
srcpath = os.path.dirname(__file__)

def main():
    contents = open(itl_path).read()
    component = itl_parser.parse(contents)

    ensure_path(outpath)

    write_header(component)
    write_js_module(component)

def ensure_path(path):
    try:
        os.makedirs(path)
    except:
        pass

def it_to_cpp_ty(ty):
    TYPES = {
        'u1': 'bool',
        's32': 'int',
        'string': 'const char*',
    }
    return TYPES[ty]
def it_to_cpp_func(func):
    ret_ty = it_to_cpp_ty(func.results[0]) if func.results else 'void'
    arg_tys = [it_to_cpp_ty(param) for param in func.params]
    arg_str = ', '.join(arg_tys)
    return '{} {}({});\n'.format(ret_ty, func.name, arg_str)

# Implementation header, for use by the module itself
def write_header(component):
    header_path = os.path.join(outpath, basename + '_impl.h')
    template_path = os.path.join(srcpath, 'c_header_template.h')
    header = open(template_path).read()

    # XXX: this is subtly wrong, but will be fixed by a later tool
    # the key assumption is that we're the only module, and can thus uniquely
    # derive a header for a C++ module.

    import_decls = ''
    for imp, funcs in component.imports.iteritems():
        for func in funcs:
            attr = '__attribute__((import_module({}), import_name("{}")))'.format(imp, func.name)
            import_decls += attr + ' ' + it_to_cpp_func(func)
    header = header.replace('/**IMPORT_DECLS**/', import_decls)

    export_decls = ''
    for func in component.exports:
        # XXX: This should not need to have a 1:1 correspondence with the
        # component's exports, but for convenience it does for the moment
        attr = '__attribute__((export_name("{}")))'.format(func.name)
        export_decls += attr + ' ' + it_to_cpp_func(func)
    header = header.replace('/**EXPORT_DECLS**/', export_decls)

    open(header_path, 'w').write(header)
    print('Wrote header', header_path)

# NodeJS wrapper module
num_locals = 0
def write_js_module(component):
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
        elif head == 'call':
            assert(len(sexpr) >= 2)
            func_name = sexpr[1]
            args = ', '.join([expr(x) for x in sexpr[2:]])
            func = component.all_funcs[func_name]
            if func.location[0] == 'import':
                mod_name = func.location[1]
                return 'imports["{}"]["{}"]({})'.format(mod_name, func_name, args)
            elif func.location[0] == 'module':
                mod_name = func.location[1]
                return '{}["{}"]({})'.format(mod_name, func_name, args)
        elif head == 'call-import':
            assert(len(sexpr) >= 3)
            mod_name = sexpr[1]
            fn = sexpr[2]
            args = ', '.join([expr(x) for x in sexpr[3:]])
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
        elif head == 'string-to-mem':
            assert(len(sexpr) == 5)
            mod = sexpr[1]
            mem = sexpr[2]
            string = expr(sexpr[3])
            ptr = expr(sexpr[4])
            return 'stringToMem({}[{}], {}, {})'.format(mod, mem, string, ptr)
        elif head == 'string-len':
            assert(len(sexpr) == 2)
            string = expr(sexpr[1])
            return '{}.length'.format(string)
        elif head == '+':
            assert(len(sexpr) == 3)
            lhs = expr(sexpr[1])
            rhs = expr(sexpr[2])
            return '({} + {})'.format(lhs, rhs)
        else:
            try:
                n = int(head)
                return str(n)
            except:
                pass
        assert False, 'Unknown expr: {}'.format(sexpr)
    def function(func, n_indent):
        global num_locals
        ret = ''
        params = ', '.join(['x' + str(i) for i in range(len(func.params))])
        ret += tab * n_indent + '"{}": function({}) {{\n'.format(func.exname, params)
        num_locals = len(func.params)
        for i in range(len(func.body)):
            sexpr = func.body[i]
            ret += tab * (n_indent + 1)
            if func.results and i == len(func.body) - 1:
                ret += 'return ' + expr(sexpr)
            else:
                ret += expr(sexpr)
            ret += ';\n'
        ret += tab * n_indent + '},\n'
        return ret

    # Paths and setup
    js_path = os.path.join(outpath, basename + '.js')
    template_path = os.path.join(srcpath, 'wrapper_module_template.js')
    js_str = open(template_path).read()
    tab = '    '

    module_names = ''
    load_modules = ''        
    for mod in component.modules:
        name = mod.name
        path = mod.path
        module_names += tab * 2 + 'let {};'.format(name)
        load_modules += tab * 2 + '{} = await loadModule("{}", {{\n'.format(name, path)
        for imp, funcs in mod.imports.iteritems():
            load_modules += tab * 3 + imp + ': {\n'
            for func in funcs:
                load_modules += function(func, n_indent=4)
            load_modules += tab * 3 + '},\n'
        load_modules += tab * 2 + '});\n'
    js_str = js_str.replace('/**MODULE_NAMES**/', module_names)
    js_str = js_str.replace('/**LOAD_MODULES**/', load_modules)

    exports = ''
    for func in component.exports:
        exports += function(func, n_indent=3)
    js_str = js_str.replace('/**EXPORTS**/\n', exports)
    open(js_path, 'w').write(js_str)
    print('Wrote JS module', js_path)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        trace = traceback.format_exc(e)
        print trace
        sys.exit(1)
