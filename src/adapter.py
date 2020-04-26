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
header_path = os.path.join(outpath, basename + '_impl.h')
header = '#pragma once\n'
for func in ast.exports:
    attr = '__attribute__((export_name("{}")))'.format(func.name)
    ret_ty = it_to_cpp_ty(func.results[0])
    arg_tys = [it_to_cpp_ty(param) for param in func.params]
    arg_str = ', '.join(arg_tys)
    header += '{} {} {}({});\n'.format(attr, ret_ty, func.name, arg_str)
open(header_path, 'w').write(header)
print('Wrote header', header_path)
