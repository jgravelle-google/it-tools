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

# number of extra locals to allocate due to let exprs
num_lets = 0
def parse(body):
    sexprs = SexprParser(body).parse()
    component = Component()

    def parse_expr(sexpr, num_locals):
        global num_lets
        assert(len(sexpr) > 0)
        head = sexpr[0]
        if head == 'as':
            assert(len(sexpr) == 3)
            ty = sexpr[1]
            ex = parse_expr(sexpr[2], num_locals)
            return AsExpr(ty, ex)
        elif head == 'local':
            assert(len(sexpr) == 2)
            return LocalExpr(int(sexpr[1]))
        elif head == 'call':
            assert(len(sexpr) >= 2)
            name = sexpr[1]
            args = [parse_expr(x, num_locals) for x in sexpr[2:]]
            return CallExpr(name, args)
        elif head == 'let':
            assert(len(sexpr) == 2)
            idx = num_locals
            num_lets += 1
            ex = parse_expr(sexpr[1], num_locals+1)
            return LetExpr(idx, ex)
        elif head == 'mem-to-string':
            assert(len(sexpr) == 5)
            mod = sexpr[1]
            mem = unquote(sexpr[2])
            ptr = parse_expr(sexpr[3], num_locals)
            length = parse_expr(sexpr[4], num_locals)
            return MemToStringExpr(mod, mem, ptr, length)
        elif head == 'string-to-mem':
            assert(len(sexpr) == 5)
            mod = sexpr[1]
            mem = unquote(sexpr[2])
            string = parse_expr(sexpr[3], num_locals)
            ptr = parse_expr(sexpr[4], num_locals)
            return StringToMemExpr(mod, mem, string, ptr)
        elif head == 'string-len':
            assert(len(sexpr) == 2)
            string = parse_expr(sexpr[1], num_locals)
            return StringLenExpr(string)
        elif head == 'buffer-len':
            assert(len(sexpr) == 2)
            buff = parse_expr(sexpr[1], num_locals)
            return BufferLenExpr(buff)
        elif head == 'mem-to-buffer':
            assert(len(sexpr) == 5)
            mod = sexpr[1]
            mem = unquote(sexpr[2])
            ptr = parse_expr(sexpr[3], num_locals)
            length = parse_expr(sexpr[4], num_locals)
            return MemToBufferExpr(mod, mem, ptr, length)
        elif head == 'buffer-to-mem':
            assert(len(sexpr) == 5)
            mod = sexpr[1]
            mem = unquote(sexpr[2])
            buff = parse_expr(sexpr[3], num_locals)
            ptr = parse_expr(sexpr[4], num_locals)
            return BufferToMemExpr(mod, mem, buff, ptr)
        elif head == 'load':
            assert len(sexpr) == 5, sexpr
            ty = sexpr[1]
            mod = sexpr[2]
            mem = unquote(sexpr[3])
            ptr = parse_expr(sexpr[4], num_locals)
            return LoadExpr(ty, mod, mem, ptr)
        elif head == 'store':
            assert len(sexpr) == 6
            ty = sexpr[1]
            mod = sexpr[2]
            mem = unquote(sexpr[3])
            ptr = parse_expr(sexpr[4], num_locals)
            expr = parse_expr(sexpr[5], num_locals)
            return StoreExpr(ty, mod, mem, ptr, expr)
        elif head == '+':
            assert(len(sexpr) == 3)
            lhs = parse_expr(sexpr[1], num_locals)
            rhs = parse_expr(sexpr[2], num_locals)
            return BinaryExpr(lhs, rhs, '+', 'i32.add')
        elif head == '*':
            assert(len(sexpr) == 3)
            lhs = parse_expr(sexpr[1], num_locals)
            rhs = parse_expr(sexpr[2], num_locals)
            return BinaryExpr(lhs, rhs, '*', 'i32.mul')
        elif head == '/':
            assert(len(sexpr) == 3)
            lhs = parse_expr(sexpr[1], num_locals)
            rhs = parse_expr(sexpr[2], num_locals)
            return BinaryExpr(lhs, rhs, '/', 'i32.div_s')
        elif head == 'table-read':
            assert(len(sexpr) == 4)
            mod = sexpr[1]
            table = unquote(sexpr[2])
            idx = parse_expr(sexpr[3], num_locals)
            return TableReadExpr(mod, table, idx)
        elif head == 'make-record':
            assert(len(sexpr) >= 2)
            ty = sexpr[1]
            # fields are a list of pairs rather than a dict, to preserve the
            # original order found in the source
            fields = []
            for sx in sexpr[2:]:
                assert(len(sx) == 3)
                assert(sx[0] == 'field')
                field = sx[1]
                expr = parse_expr(sx[2], num_locals)
                fields.append((field, expr))
            return MakeRecordExpr(ty, fields)
        elif head == 'unreachable':
            assert(len(sexpr) == 1)
            return UnreachableExpr()
        elif head == 'lambda':
            assert len(sexpr) >= 2
            assert sexpr[1][0] == 'func'
            ty = parse_func_type(sexpr[1][1:2+1])
            body = [parse_expr(s, num_locals+len(ty.params)) for s in sexpr[2:]]
            return LambdaExpr(ty, body, num_locals)
        elif head == 'call-expr':
            fn = parse_expr(sexpr[1], num_locals)
            args = [parse_expr(s, num_locals) for s in sexpr[2:]]
            return CallExprExpr(fn, args)
        elif head == 'lift-ref':
            assert(len(sexpr) == 2)
            expr = parse_expr(sexpr[1], num_locals)
            return LiftRefExpr(expr)
        elif head == 'lower-ref':
            assert(len(sexpr) == 2)
            expr = parse_expr(sexpr[1], num_locals)
            return LowerRefExpr(expr)
        elif head == 'read-field':
            assert(len(sexpr) == 4)
            record = sexpr[1]
            field = sexpr[2]
            expr = parse_expr(sexpr[3], num_locals)
            return ReadFieldExpr(record, field, expr)
        elif head == 'lift-array':
            assert len(sexpr) == 6
            ty = sexpr[1]
            stride = sexpr[2]
            ptr = parse_expr(sexpr[3], num_locals)
            length = parse_expr(sexpr[4], num_locals)
            body = parse_expr(sexpr[5], num_locals+1)
            return LiftArrayExpr(ty, stride, ptr, length, body, num_locals)
        elif head == 'lower-array':
            assert len(sexpr) == 6
            ty = sexpr[1]
            stride = sexpr[2]
            ptr = parse_expr(sexpr[3], num_locals)
            array = parse_expr(sexpr[4], num_locals)
            body = parse_expr(sexpr[5], num_locals)
            return LowerArrayExpr(ty, stride, ptr, array, body, num_locals)
        elif head == 'array-len':
            assert len(sexpr) == 2
            expr = parse_expr(sexpr[1], num_locals)
            return ArrayLenExpr(expr)
        elif head == 'lift-enum':
            assert len(sexpr) == 3
            ty = component.types[sexpr[1]]
            expr = parse_expr(sexpr[2], num_locals)
            return LiftEnumExpr(ty, expr)
        elif head == 'lower-enum':
            assert len(sexpr) == 3
            ty = component.types[sexpr[1]]
            expr = parse_expr(sexpr[2], num_locals)
            return LowerEnumExpr(ty, expr)
        else:
            try:
                n = int(sexpr)
                return IntExpr(n)
            except:
                pass
        assert False, 'Unknown expr: {}'.format(sexpr)
    def parse_func_type(sexpr):
        assert(sexpr[0][0] == 'param')
        params = sexpr[0][1:]
        assert(sexpr[1][0] == 'result')
        results = sexpr[1][1:]
        return FuncType(params, results)
    def parse_func(sexpr, location):
        global num_lets
        assert(sexpr[0] == 'func')
        name = sexpr[1]
        external_name = unquote(sexpr[2])
        ty = parse_func_type(sexpr[3:4+1])
        num_lets = 0
        body = [parse_expr(expr, len(ty.params)+num_lets) for expr in sexpr[5:]]
        func = Func(name, external_name, ty.params, ty.results, body, location)
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
        elif group[0] == 'types':
            for elem in group[1:]:
                if elem[0] == 'enum':
                    name = elem[1]
                    kinds = elem[2:]
                    component.types[name] = EnumType(name, kinds)

    # post-initialize now that AST is fully built
    for func in component.all_funcs_iter():
        for expr in func.body:
            expr.post_init(component=component)

    return component
