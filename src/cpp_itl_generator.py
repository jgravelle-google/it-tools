#!/usr/bin/python

# Generates an ITL description and a vanilla .cpp from an annotated .cpp file

import os
import sys

def main():
    outpath = 'out'
    ensure_path(outpath)

    cpp_in = sys.argv[1]
    basename, _ = os.path.splitext(cpp_in)
    h_out = os.path.join(outpath, basename + '_impl.h')
    cpp_out = os.path.join(outpath, cpp_in)
    itl_out = os.path.join(outpath, basename + '.itl')

    contents = open(cpp_in).read()
    start_str, end_str = '/**IT_START**/', '/**IT_END**/'
    start = contents.find(start_str) + len(start_str)
    end = contents.find(end_str)
    it_contents = contents[start:end]
    cpp_contents = (
        contents[:start-len(start_str)] +
        # Add an include to the generated header file
        '#include "' + h_out + '"\n' +
        contents[end+len(end_str):]
    )

    # The .cpp is done at this point; write it out
    open(cpp_out, 'w').write(cpp_contents)

    parse_it(it_contents)

def parse_it(contents):
    try:
        tokens = Lexer(contents).lex()
        ast = Parser(tokens).parse()
        print "AST", ast
    except Exception as e:
        print '[ERROR]:', e

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
        return imports, exports

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
        return (name, args, ret)

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

def ensure_path(path):
    try:
        os.makedirs(path)
    except:
        pass

if __name__ == '__main__':
    main()
