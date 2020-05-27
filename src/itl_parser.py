#!/usr/bin/python

# ITL parser

import sys

from itl_ast import *

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

def unquote(name):
    assert(name[0] == '"' and name[-1] == '"')
    return name[1:-1]

num_locals = 0
# extra_locals tracks the new locals allocated by `let` stmts
extra_locals = []
def parse(body):
    sexprs = SexprParser(body).parse()
    component = Component()

    def parse_expr(sexpr):
        global num_locals, extra_locals
        assert(len(sexpr) > 0)
        head = sexpr[0]
        if head == 'as':
            assert(len(sexpr) == 3)
            ty = sexpr[1]
            ex = parse_expr(sexpr[2])
            return AsExpr(ty, ex)
        elif head == 'local':
            assert(len(sexpr) == 2)
            return LocalExpr(int(sexpr[1]))
        elif head == 'call':
            assert(len(sexpr) >= 2)
            name = sexpr[1]
            args = [parse_expr(x) for x in sexpr[2:]]
            return CallExpr(name, args)
        elif head == 'let':
            assert(len(sexpr) == 2)
            idx = num_locals
            num_locals += 1
            ex = parse_expr(sexpr[1])
            return LetExpr(idx, ex)
        elif head == 'mem-to-string':
            assert(len(sexpr) == 5)
            mod = sexpr[1]
            mem = sexpr[2]
            ptr = parse_expr(sexpr[3])
            length = parse_expr(sexpr[4])
            return MemToStringExpr(mod, mem, ptr, length)
        elif head == 'string-to-mem':
            assert(len(sexpr) == 5)
            mod = sexpr[1]
            mem = sexpr[2]
            string = parse_expr(sexpr[3])
            ptr = parse_expr(sexpr[4])
            return StringToMemExpr(mod, mem, string, ptr)
        elif head == 'string-len':
            assert(len(sexpr) == 2)
            string = parse_expr(sexpr[1])
            return StringLenExpr(string)
        elif head == '+':
            assert(len(sexpr) == 3)
            lhs = parse_expr(sexpr[1])
            rhs = parse_expr(sexpr[2])
            return AddExpr(lhs, rhs)
        else:
            try:
                n = int(head)
                return IntExpr(n)
            except:
                pass
        assert False, 'Unknown expr: {}'.format(sexpr)
    def parse_func(sexpr, location):
        global num_locals, extra_locals
        assert(sexpr[0] == 'func')
        name = sexpr[1]
        external_name = unquote(sexpr[2])
        assert(sexpr[3][0] == 'param')
        params = sexpr[3][1:]
        assert(sexpr[4][0] == 'result')
        results = sexpr[4][1:]
        num_locals = len(params)
        body = [parse_expr(expr) for expr in sexpr[5:]]
        func = Func(name, external_name, params, results, body, location)
        for expr in body:
            expr.initialize(func=func)
        return func

    def parse_module_elem(mod, sexpr):
        if sexpr[0] == 'func':
            func = parse_func(sexpr, ['module', mod.name])
            mod.funcs.append(func)
            component.add_func(func)
        elif sexpr[0] == 'import':
            im_name = unquote(sexpr[1])
            funcs = [parse_func(e, None) for e in sexpr[2:]]
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
                func = parse_func(elem, None)
                component.exports.append(func)
                component.add_func(func)
        elif group[0] == 'import':
            name = unquote(group[1])
            funcs = [parse_func(e, ['import', name]) for e in group[2:]]
            component.imports[name] = funcs
            for func in funcs:
                component.add_func(func)
        elif group[0] == 'func':
            # Component-only functions
            func = parse_func(group, ['component'])
            component.funcs.append(func)
            component.add_func(func)

    # set lookup table for name -> func
    for func in component.all_funcs_iter():
        component.all_funcs[func.name] = func
    # post-initialize now that AST is fully built
    for func in component.all_funcs_iter():
        for expr in func.body:
            expr.post_init(component=component)

    return component
