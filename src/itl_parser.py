#!/usr/bin/python

# ITL parser

import sys

class AST(object):
    def __init__(self):
      self.imports = []
      self.exports = []

class Func(object):
    def __init__(self, name, params, results, body):
        self.name = name
        self.params = params
        self.results = results
        self.body = body

class SexprParser(object):
    def __init__(self, body):
        self.stack = [[]]
        self.cur = ''
        self.body = body

    def top(self):
        return self.stack[-1]
    def pop(self):
        ret = self.top()
        self.stack.pop()
        return ret
    def end_atom(self):
        if self.cur != '':
            self.top().append(self.cur)
            self.cur = ''

    def parse(self):
        i = 0
        while i < len(self.body):
            c = self.body[i]
            if c in [' ', '\n']:
                self.end_atom()
            elif c == '(':
                self.end_atom()
                self.stack.append([])
            elif c == ')':
                self.end_atom()
                top = self.pop()
                self.top().append(top)
            else:
                self.cur += c
            i += 1
        return self.pop()

def parse(body):
    sexprs = SexprParser(body).parse()
    ast = AST()

    def parse_func(sexpr):
        assert(sexpr[0] == 'func')
        name = sexpr[1]
        assert(name[0] == '"' and name[-1] == '"')
        name = name[1:-1]
        assert(sexpr[2][0] == 'param')
        params = sexpr[2][1:]
        assert(sexpr[3][0] == 'result')
        results = sexpr[3][1:]
        body = sexpr[4:]
        return Func(name, params, results, body)

    for group in sexprs:
        if group[0] == 'export':
            for elem in group[1:]:
                func = parse_func(elem)
                ast.exports.append(func)

    return ast
