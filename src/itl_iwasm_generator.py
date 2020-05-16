#!/usr/bin/python

# Generates an .iwasm module from an .itl file

import argparse
import os
import sys
import traceback

import itl_parser

srcpath = os.path.dirname(__file__)

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('itl_in')
    arg_parser.add_argument('-o', dest='iwasm_out', default=None, required=True)
    args = arg_parser.parse_args(sys.argv[1:])

    itl_in = args.itl_in
    iwasm_out = args.iwasm_out

    print '<< ITL -> IWASM START >>'
    itl_contents = open(itl_in).read()
    ast = itl_parser.parse(itl_contents)

    writer = IWasmWriter(ast)
    writer.write_to(iwasm_out)
    print '<< DONE >>'

class IWasmWriter(object):
    def __init__(self, ast):
        self.ast = ast

    def write_to(self, filename):
        binary = self.iwasm_contents()
        with open(filename, 'wb') as f:
            f.write(bytearray(binary))

    def iwasm_contents(self):
        for mod in self.ast.modules:
            name = mod.name
            path = mod.path
        return []

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        trace = traceback.format_exc(e)
        print trace
        sys.exit(1)
