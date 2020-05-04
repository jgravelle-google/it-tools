#!/usr/bin/python

# ITL parser

import sys

class Component(object):
    def __init__(self):
        self.imports = {} # imports to the component
        self.exports = [] # exports from the component
        self.modules = [] # modules wrapped by the component
        
        # lookup table for all functions by name
        self.all_funcs = {}

    def add_func(self, func):
        self.all_funcs[func.name] = func

def unquote(name):
    assert(name[0] == '"' and name[-1] == '"')
    return name[1:-1]

class Func(object):
    def __init__(self, sexpr, location):
        assert(sexpr[0] == 'func')
        self.name = sexpr[1]
        # external name
        self.exname = unquote(sexpr[2])
        assert(sexpr[3][0] == 'param')
        self.params = sexpr[3][1:]
        assert(sexpr[4][0] == 'result')
        self.results = sexpr[4][1:]
        self.body = sexpr[5:]

        self.location = location

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

    def parse_module_elem(mod, sexpr):
        if sexpr[0] == 'func':
            func = Func(sexpr, ['module', mod.name])
            mod.funcs.append(func)
            component.add_func(func)
        elif sexpr[0] == 'import':
            im_name = unquote(sexpr[1])
            funcs = [Func(e, None) for e in sexpr[2:]]
            mod.imports[im_name] = funcs
            for func in funcs:
                component.add_func(func)

    for group in sexprs:
        if group[0] == 'module':
            name = group[1]
            path = unquote(group[2])
            mod = Module(name, path)
            for elem in group[3:]:
                parse_module_elem(mod, elem)
            component.modules.append(mod)
        elif group[0] == 'export':
            for elem in group[1:]:
                func = Func(elem, None)
                component.exports.append(func)
                component.add_func(func)
        elif group[0] == 'import':
            name = unquote(group[1])
            funcs = [Func(e, ['import', name]) for e in group[2:]]
            component.imports[name] = funcs
            for func in funcs:
                component.add_func(func)

    return component
