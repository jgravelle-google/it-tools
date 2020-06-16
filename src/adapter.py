#!/usr/bin/python

# Generates a JS adapter module from an IDL file

import argparse
import os
import sys
import traceback

import itl_parser

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('itl_in')
arg_parser.add_argument('-o', dest='js_out', default=None)
arg_parser.add_argument('--node', dest='do_node', action='store_true')
arg_parser.add_argument('--name', dest='component_name', default=None)
args = arg_parser.parse_args(sys.argv[1:])

# TODO: actually re-support node scripts

itl_path = args.itl_in
itl_filename = os.path.basename(itl_path)
basename, _ = os.path.splitext(itl_filename)
if args.js_out:
    js_path = args.js_out
    outpath = os.path.basename(js_path)
else:
    outpath = 'out'
    js_path = os.path.join(outpath, basename + '.js')
if args.component_name:
    component_name = args.component_name
else:
    component_name = basename + 'Component'

srcpath = os.path.dirname(__file__)

def main():
    contents = open(itl_path).read()
    component = itl_parser.parse(contents)

    ensure_path(outpath)

    write_js_module(component)

def ensure_path(path):
    try:
        os.makedirs(path)
    except:
        pass

# NodeJS wrapper module
def write_js_module(component):
    def escape(s):
        return s.replace('\\', '/')

    def function(func, n_indent, is_internal=False):
        global num_locals
        ret = ''
        params = ', '.join(['x' + str(i) for i in range(len(func.params))])
        if is_internal:
            decl = 'function {}'.format(func.name)
        else:
            decl = '"{}": function'.format(func.exname)
        ret += tab * n_indent + '{}({}) {{\n'.format(decl, params)
        for i in range(len(func.body)):
            sexpr = func.body[i]
            ret += tab * (n_indent + 1)
            if func.results and i == len(func.body) - 1:
                ret += 'return ' + sexpr.as_js()
            else:
                ret += sexpr.as_js()
            ret += ';\n'
        if is_internal:
            ret += tab * n_indent + '};\n'
        else:
            ret += tab * n_indent + '},\n'
        return ret

    # Paths and setup
    template_path = os.path.join(srcpath, 'wrapper_module_template.js')
    js_str = open(template_path).read()
    tab = '    '

    js_str = js_str.replace('/**COMPONENT_NAME**/', component_name)

    module_names = ''
    load_modules = ''        
    for mod in component.modules:
        name = mod.name
        path = mod.path
        module_names += tab * 2 + 'let {};\n'.format(name)
        load_modules += tab * 2 + '{} = await loadModule("{}", {{\n'.format(name, path)
        for imp, funcs in mod.imports.iteritems():
            load_modules += tab * 3 + imp + ': {\n'
            for func in funcs:
                load_modules += function(func, n_indent=4)
            load_modules += tab * 3 + '},\n'
        load_modules += tab * 2 + '});\n'
    js_str = js_str.replace('/**MODULE_NAMES**/', module_names)
    js_str = js_str.replace('/**LOAD_MODULES**/', load_modules)

    component_functions = ''
    for func in component.funcs:
        component_functions += function(func, n_indent=2, is_internal=True)
    js_str = js_str.replace('/**COMPONENT_FUNCTIONS**/\n', component_functions)

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
