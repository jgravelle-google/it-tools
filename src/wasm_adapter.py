#!/usr/bin/python

# Generates a wasm adapter module from an IDL file

import os
import sys
import traceback

from itl_ast import *
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

    write_wat_module(component)

def ensure_path(path):
    try:
        os.makedirs(path)
    except:
        pass

def write_wat_module(component):
    # TODO: emit real wasm, not wat
    def it_to_wat_ty(ty):
        if ty == 'string':
            return 'anyref'
        elif ty in ['u1', 's8', 's32', 'u32']:
            return 'i32'
        return ty
    def func_decl(func, is_export=False, is_import=False):
        params = '(param {})'.format(' '.join(it_to_wat_ty(p) for p in func.params))
        results = '(result {})'.format(' '.join(it_to_wat_ty(r) for r in func.results))
        decl = '(func ${}'.format(func.name)
        if is_export:
            decl += ' (export "{}")'.format(func.exname)
        decl += ' {} {}'.format(params, results)
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
    wat_path = os.path.join(outpath, basename + '_pre.wat')
    wat_str = '''
(import "_it_runtime" "string-len" (func $_it_string_len (param anyref) (result i32)))
(import "_it_runtime" "mem-to-string" (func $_it_mem_to_string (param i32 i32) (result anyref)))
(import "_it_runtime" "string-to-mem" (func $_it_string_to_mem (param anyref i32)))
'''
    tab = '    '

    assert len(component.modules) <= 1, 'TODO: support for >1 module'
    module = component.modules[0]

    # TODO: table size based on module export length

    for imp, funcs in module.imports.iteritems():
        print 'TODO - unused imports:', imp, funcs
    for func in module.funcs:
        # TODO: call-indirects go here
        wat_str += func_decl(func) + '\n' + tab + '(unreachable)\n)\n'

    for func in component.funcs:
        wat_str += function(func, n_indent=0)

    for func in component.exports:
        wat_str += function(func, n_indent=0, is_export=True)
    open(wat_path, 'w').write(wat_str)
    print('Wrote .wat preload module', wat_path)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        trace = traceback.format_exc(e)
        print trace
        sys.exit(1)
