# AST for ITL

class Component(object):
    def __init__(self):
        self.imports = {} # imports to the component
        self.exports = [] # exports from the component
        self.modules = [] # modules wrapped by the component
        self.funcs = [] # component-local functions
        
        # lookup table for all functions by name
        self.all_funcs = {}

    def add_func(self, func):
        self.all_funcs[func.name] = func

    def all_funcs_iter(self):
        for k, v in self.imports.iteritems():
            print 'import', k, v
        for func in self.exports:
            yield func
        for mod in self.modules:
            print 'module', mod
        for func in self.funcs:
            yield func

class Func(object):
    def __init__(self, name, exname, params, results, body, location):
        self.name = name
        self.exname = exname # external name
        self.params = params
        self.results = results
        self.body = body
        self.location = location

class Module(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.funcs = []
        self.imports = {}

#---------------------
# Instructions

class BaseExpr(object):
    # Computed properties are set dynamically

    # Helper methods for setting computed properties
    def zero(self):
        # call my own 0-arg f
        return self.f()
    def one(self, g):
        # first do f to all my children
        for child in self.children():
            self.f(child)
        # call my one-arg f on myself as told by the passed-in g
        f = self.f
        # reimplement my one-arg f as a 0-arg version of f
        self.f = lambda: f(g(self))
        # return the result of zero()
        ret = self.zero()
        # restore original f
        self.f = f
        return ret
    # def two(self, f, g):
    #     return self.f(f(self, g), g(self, f))

    def children(self):
        return []

    def initialize(self, **kwargs):
        self.set_field('func', kwargs['func'])

    def post_init(self, **kwargs):
        print 'BaseExpr post_init', self
        self.f = lambda ex: ex.post_init(**kwargs) if ex else None
        self.one(lambda ex: None if ex == self else ex)
        # self.f = lambda ex: None if ex == self else ex
        # self.one(lambda ex: ex.post_init(**kwargs) if ex else None)

    def set_field(self, field, val):
        self.f = lambda ex: setattr(ex, field, val)
        self.one(lambda ex: ex)

class AsExpr(BaseExpr):
    def __init__(self, ty, expr):
        self.ty = ty
        self.expr = expr

    def children(self):
        return [self.expr]

    def as_js(self):
        return self.expr.as_js()
    def as_wat(self):
        return self.expr.as_wat()

class LocalExpr(BaseExpr):
    def __init__(self, idx):
        self.idx = idx

    def ty(self):
        self.func.params

    def as_js(self):
        return 'x' + str(self.idx)

class CallExpr(BaseExpr):
    def __init__(self, func_name, args):
        self.func_name = func_name
        self.args = args

    def children(self):
        return self.args

    def post_init(self, **kwargs):
        print 'CallExpr post_init', self
        func = kwargs['component'].all_funcs[self.func_name]
        print '  initing w/ func=', func.name
        setattr(self, 'target_func', func)
        print self.target_func
        super(CallExpr, self).post_init(**kwargs)

    def as_js(self):
        print 'CallExpr as_js', self, self.func_name
        func = self.target_func
        args = ', '.join(arg.as_js() for arg in self.args)
        if func.location[0] == 'import':
            mod_name = func.location[1]
            ex_name = func.exname
            return 'imports["{}"]["{}"]({})'.format(mod_name, ex_name, args)
        elif func.location[0] == 'module':
            mod_name = func.location[1]
            ex_name = func.exname
            return '{}["{}"]({})'.format(mod_name, ex_name, args)
        elif func.location[0] == 'component':
            return '{}({})'.format(self.func_name, args)
        else:
            assert False, 'Unknown location for func: ' + str(func.location)

class LetExpr(BaseExpr):
    def __init__(self, idx, expr):
        self.idx = idx
        self.expr = expr

    def children(self):
        return [self.expr]

    def as_js(self):
        return 'let x{} = {}'.format(self.idx, self.expr.as_js())

class MemToStringExpr(BaseExpr):
    def __init__(self, module, memory, ptr, length):
        self.module = module
        self.memory = memory
        self.ptr = ptr
        self.length = length

    def children(self):
        return [self.ptr, self.length]

    def as_js(self):
        return 'memToString({}[{}], {}, {})'.format(
            self.module, self.memory, self.ptr.as_js(), self.length.as_js())

class StringToMemExpr(BaseExpr):
    def __init__(self, module, memory, string, ptr):
        self.module = module
        self.memory = memory
        self.string = string
        self.ptr = ptr

    def children(self):
        return [self.string, self.ptr]

    def as_js(self):
        return 'stringToMem({}[{}], {}, {})'.format(
            self.module, self.memory, self.string.as_js(), self.ptr.as_js())

class StringLenExpr(BaseExpr):
    def __init__(self, expr):
        self.expr = expr

    def children(self):
        return [self.expr]

    def as_js(self):
        return '{}.length'.format(self.expr.as_js())

class AddExpr(BaseExpr):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def children(self):
        return [self.lhs, self.rhs]

    def as_js(self):
        return '({} + {})'.format(self.lhs.as_js(), self.rhs.as_js())

class IntExpr(BaseExpr):
    def __init__(self, val):
        self.val = val

    def as_js(self):
        return str(self.val)
