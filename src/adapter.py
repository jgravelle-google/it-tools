#!/usr/bin/python

# Generates a JS adapter module from an IDL file

import os
import sys

import itl_parser

itl_file = sys.argv[1]
contents = open(itl_file).read()
ast = itl_parser.parse(contents)
print(ast)
