#!/usr/bin/python

# Generates a wasm adapter module from an IDL file

import argparse
import os
import sys
import traceback

from itl_ast import *
import itl_parser

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('itl_in')
arg_parser.add_argument('-o', dest='wat_out', default=None)
args = arg_parser.parse_args(sys.argv[1:])

wat_out = args.wat_out
if wat_out:
    outpath = os.path.dirname(wat_out)
else:
    outpath = 'out'
    wat_out = os.path.join(outpath, 'it_{}.wat'.format(basename))
itl_path = args.itl_in
itl_filename = os.path.basename(itl_path)
basename, _ = os.path.splitext(itl_filename)
srcpath = os.path.dirname(__file__)

def main():
    contents = open(itl_path).read()
    component = itl_parser.parse(contents)

    ensure_path(outpath)

    write_wat_module(component)

def ensure_path(path):
    try:
        os.makedirs(path)
    except:
        pass

def write_wat_module(component):
    # TODO: emit real wasm, not wat
    def it_to_wat_ty(ty):
        if ty in ['u1', 's8', 'u8', 's16', 'u16', 's32', 'u32', 'i32']:
            return 'i32'
        return 'externref'
    def func_ty(func):
        params = '(param {})'.format(' '.join(it_to_wat_ty(p) for p in func.params))
        results = '(result {})'.format(' '.join(it_to_wat_ty(r) for r in func.results))
        return params + ' ' + results
    def func_decl(func, is_export=False, is_import=False):
        ty = func_ty(func)
        decl = '(func ${}'.format(func.name)
        if is_export:
            decl += ' (export "{}")'.format(func.exname)
        decl += ' ' + ty
        return decl
    def function(func, n_indent, is_export=False):
        ret = ''
        decl = func_decl(func, is_export=is_export)
        ret += tab * n_indent + decl + '\n'
        ret += tab * (n_indent + 1) + '(local {})\n'.format(' '.join(it_to_wat_ty(loc) for loc in func.extra_locals))
        for expr in func.body:
            ret += tab * (n_indent + 1) + expr.as_wat() + '\n'
        ret += tab * n_indent + ')\n'
        return ret

    # Paths and setup
    import_str = '''
(import "_it_runtime" "string_len" (func $_it_string_len (param externref) (result i32)))
(import "_it_runtime" "mem_to_string" (func $_it_mem_to_string (param externref i32 i32 i32) (result externref)))
(import "_it_runtime" "string_to_mem" (func $_it_string_to_mem (param externref i32 externref i32)))
(import "_it_runtime" "load_wasm" (func $_it_load_wasm (param i32) (result externref)))
(import "_it_runtime" "set_table_func" (func $_it_set_table_func (param i32 externref i32)))
(import "_it_runtime" "ref_to_i32" (func $ref_to_i32 (param externref) (result i32)))
(import "_it_runtime" "i32_to_ref" (func $i32_to_ref (param i32) (result externref)))
'''
    tab = '    '

    assert len(component.modules) <= 1, 'TODO: support for >1 module'

    table_len = 0
    table_table = {}

    for imp, funcs in component.imports.iteritems():
        for func in funcs:
            import_str += '(import "{}" "{}" {}))\n'.format(
                imp, func.exname, func_decl(func))
            print imp, func.name

    global_str = ''
    func_str = ''
    for module in component.modules:
        global_str += '(global ${} (mut i32) (i32.const -1))\n'.format(module.name)
        for imp, funcs in module.imports.iteritems():
            for func in funcs:
                func_str += function(func, n_indent=0, is_export=True)
        for func in module.funcs:
            idx = table_len
            table_len += 1
            table_table[func.name] = idx
            ty = func_ty(func)
            args = ' '.join('(local.get {})'.format(i) for i in range(len(func.params)))
            func_str += func_decl(func) + '\n' \
                + tab + '(call_indirect {}\n'.format(ty) \
                + 2 * tab + '{} (i32.const {}))\n)\n'.format(args, idx)

    for func in component.funcs:
        func_str += function(func, n_indent=0)

    for func in component.exports:
        func_str += function(func, n_indent=0, is_export=True)

    # build init after collecting exported function indices
    init_str = '(func (export "_it_init")\n'
    for module in component.modules:
        init_str += tab + '(global.set ${} (call $ref_to_i32 (call $_it_load_wasm {})))\n'.format(
            module.name, component.wat_string(module.path))
        for func in module.funcs:
            idx = table_table[func.name]
            init_str += tab + '(call $_it_set_table_func (i32.const {}) (call $i32_to_ref (global.get ${})) {})\n'.format(
                idx, module.name, component.wat_string(func.exname))
    init_str += ')\n'

    # build table + memory at the end, because they depend on data from each func
    table_str = '(table (export "_it_table") {} funcref)\n'.format(table_len)
    memory_str = '(memory (export "_it_memory") 1)\n'
    for data, offset in component.string_table.iteritems():
        memory_str += '(data {} "\\{:02x}{}")\n'.format(
            offset, len(data), data)

    wat_str = '\n'.join([
        import_str,
        table_str,
        memory_str,
        global_str,
        init_str,
        func_str,
    ])
    open(wat_out, 'w').write(wat_str)
    print('Wrote .wat preload module', wat_out)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        trace = traceback.format_exc(e)
        print trace
        sys.exit(1)
