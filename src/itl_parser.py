#!/usr/bin/python

# ITL parser

import sys

class Component(object):
    def __init__(self):
      self.imports = {}
      self.exports = []
      self.modules = []

class Func(object):
    def __init__(self, name, params, results, body):
        self.name = name
        self.params = params
        self.results = results
        self.body = body

class Module(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.funcs = []
        self.imports = {}

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
            elif c == ';' and self.body[i+1] == ';':
                # line comments are ';;'
                while self.body[i] != '\n':
                    i += 1
            else:
                self.cur += c
            i += 1
        return self.pop()

def parse(body):
    sexprs = SexprParser(body).parse()
    component = Component()

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
    def parse_module_elem(mod, sexpr):
        if sexpr[0] == 'func':
            mod.funcs.append(parse_func(sexpr))
        elif sexpr[0] == 'import':
            im_name = sexpr[1]
            funcs = [parse_func(e) for e in sexpr[2:]]
            mod.imports[im_name] = funcs

    for group in sexprs:
        if group[0] == 'module':
            name = group[1]
            path = group[2]
            mod = Module(name, path)
            for elem in group[3:]:
                parse_module_elem(mod, elem)
            component.modules.append(mod)
        elif group[0] == 'export':
            for elem in group[1:]:
                func = parse_func(elem)
                component.exports.append(func)
        elif group[0] == 'import':
            name = group[1]
            funcs = [parse_func(e) for e in group[2:]]
            component.imports[name] = funcs

    return component
