#!/usr/bin/python

# Generates an ITL description and a vanilla .cpp from an annotated .cpp file

import os
import sys

def ensure_path(path):
    try:
        os.makedirs(path)
    except:
        pass

outpath = 'out'
ensure_path(outpath)

cpp_in = sys.argv[1]
basename, _ = os.path.splitext(cpp_in)
h_out = basename + '_impl.h'
cpp_out = cpp_in
itl_out = basename + '.itl'

contents = open(cpp_in).read()
start_str, end_str = '/**IT_START**/', '/**IT_END**/'
start = contents.find(start_str) + len(start_str)
end = contents.find(end_str)
it_contents = contents[start:end]
cpp_contents = (
    contents[:start-len(start_str)] +
    '#include "' + h_out + '"\n' +
    contents[end+len(end_str):]
)
print '<<IT>>'
print it_contents
print ''
print '<<CPP>>'
print cpp_contents
