# AST for ITL

class Component(object):
    def __init__(self):
        self.imports = {} # imports to the component
        self.exports = [] # exports from the component
        self.modules = [] # modules wrapped by the component
        self.funcs = [] # component-local functions
        
        # lookup table for all functions by name
        self.all_funcs = {}

        self.next_string = 0
        self.string_table = {}

    def add_func(self, func):
        self.all_funcs[func.name] = func

    def all_funcs_iter(self):
        for func in self.all_funcs.values():
            yield func

    def wat_string(self, val):
        if val in self.string_table:
            return self.string_table[val]
        idx = self.next_string
        length = len(val)
        assert length <= 0xff, 'String literal too long: "{}"'.format(val)
        # bump space by len + 1 length byte
        self.next_string += len(val) + 1
        ret = '(i32.const {})'.format(idx)
        self.string_table[val] = ret
        return ret

class FuncType(object):
    # TODO: integrate with Func?
    def __init__(self, params, results):
        self.params = params
        self.results = results
class Func(object):
    def __init__(self, name, exname, params, results, body, location):
        self.name = name
        self.exname = exname # external name
        self.params = params
        self.results = results
        self.body = body
        self.extra_locals = []
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
    # ... can probably refactor this to just iterate over children,
    # don't need to generalize to two-argument traversals
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
        self.component = kwargs['component']
        # recurse to all non-self children and post_init them
        self.f = lambda ex: ex.post_init(**kwargs) if ex else None
        self.one(lambda ex: None if ex == self else ex)

    def set_field(self, field, val):
        # set field to val for self and all children
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
    def as_wat(self):
        return '(local.get {})'.format(self.idx)

class CallExpr(BaseExpr):
    def __init__(self, func_name, args):
        self.func_name = func_name
        self.args = args

    def children(self):
        return self.args
    def ty(self):
        res = self.target_func.results
        assert(len(res) <= 1)
        if res:
            return res[0]
        else:
            return 'void'

    def post_init(self, **kwargs):
        super(CallExpr, self).post_init(**kwargs)
        func = self.component.all_funcs[self.func_name]
        setattr(self, 'target_func', func)

    def as_js(self):
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
    def as_wat(self):
        args = ' '.join(arg.as_wat() for arg in self.args)
        return '(call ${} {})'.format(self.func_name, args)

class LetExpr(BaseExpr):
    def __init__(self, idx, expr):
        self.idx = idx
        self.expr = expr

    def children(self):
        return [self.expr]

    def post_init(self, **kwargs):
        super(LetExpr, self).post_init(**kwargs)
        self.func.extra_locals.append(self.expr.ty())

    def as_js(self):
        return 'let x{} = {}'.format(self.idx, self.expr.as_js())
    def as_wat(self):
        return '(local.set {} {})'.format(self.idx, self.expr.as_wat())

class MemToStringExpr(BaseExpr):
    def __init__(self, module, memory, ptr, length):
        self.module = module
        self.memory = memory
        self.ptr = ptr
        self.length = length

    def children(self):
        return [self.ptr, self.length]

    def as_js(self):
        return 'memToString({}["{}"], {}, {})'.format(
            self.module, self.memory, self.ptr.as_js(), self.length.as_js())
    def as_wat(self):
        return '(call $_it_mem_to_string (call $i32_to_ref (global.get ${})) {} {} {})'.format(
            self.module, self.component.wat_string(self.memory),
            self.ptr.as_wat(), self.length.as_wat())

class StringToMemExpr(BaseExpr):
    def __init__(self, module, memory, string, ptr):
        self.module = module
        self.memory = memory
        self.string = string
        self.ptr = ptr

    def children(self):
        return [self.string, self.ptr]

    def as_js(self):
        return 'stringToMem({}["{}"], {}, {})'.format(
            self.module, self.memory, self.string.as_js(), self.ptr.as_js())
    def as_wat(self):
        return '(call $_it_string_to_mem (call $i32_to_ref (global.get ${})) {} {} {})'.format(
            self.module, self.component.wat_string(self.memory),
            self.string.as_wat(), self.ptr.as_wat())

class StringLenExpr(BaseExpr):
    def __init__(self, expr):
        self.expr = expr

    def children(self):
        return [self.expr]
    def ty(self):
        return 's32'

    def as_js(self):
        return '{}.length'.format(self.expr.as_js())
    def as_wat(self):
        return '(call $_it_string_len {})'.format(self.expr.as_wat())

class LoadExpr(BaseExpr):
    def __init__(self, load_ty, module, memory, ptr):
        self.load_ty = load_ty
        self.module = module
        self.memory = memory
        self.ptr = ptr

    def ty(self):
        return self.load_ty

    def as_js(self):
        assert self.load_ty == 'u32'
        return '(new Uint32Array({}["{}"].buffer))[{} >> 2]'.format(
            self.module, self.memory, self.ptr.as_js())

class StoreExpr(BaseExpr):
    def __init__(self, store_ty, module, memory, ptr, expr):
        self.store_ty = store_ty
        self.module = module
        self.memory = memory
        self.ptr = ptr
        self.expr = expr

    def children(self):
        return [self.expr]

    def as_js(self):
        assert self.store_ty == 'u32'
        return '(new Uint32Array({}["{}"].buffer))[{} >> 2] = {}'.format(
            self.module, self.memory, self.ptr.as_js(), self.expr.as_js())

class BufferLenExpr(BaseExpr):
    def __init__(self, expr):
        self.expr = expr

    def children(self):
        return [self.expr]
    def ty(self):
        return 's32'

    def as_js(self):
        return '(new Uint8Array({})).length'.format(self.expr.as_js())

class MemToBufferExpr(BaseExpr):
    def __init__(self, module, memory, ptr, length):
        self.module = module
        self.memory = memory
        self.ptr = ptr
        self.length = length

    def children(self):
        return [self.ptr, self.length]

    def as_js(self):
        return 'memToBuffer({}["{}"], {}, {})'.format(
            self.module, self.memory, self.ptr.as_js(), self.length.as_js())

class BufferToMemExpr(BaseExpr):
    def __init__(self, module, memory, buff, ptr):
        self.module = module
        self.memory = memory
        self.buff = buff
        self.ptr = ptr

    def children(self):
        return [self.buff, self.ptr]

    def as_js(self):
        return 'bufferToMem({}["{}"], {}, {})'.format(
            self.module, self.memory, self.buff.as_js(), self.ptr.as_js())

class AddExpr(BaseExpr):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def children(self):
        return [self.lhs, self.rhs]

    def as_js(self):
        return '({} + {})'.format(self.lhs.as_js(), self.rhs.as_js())
    def as_wat(self):
        return '(i32.add {} {})'.format(self.lhs.as_wat(), self.rhs.as_wat())

class IntExpr(BaseExpr):
    def __init__(self, val):
        self.val = val

    def as_js(self):
        return str(self.val)
    def as_wat(self):
        return '(i32.const {})'.format(self.val)

class TableReadExpr(BaseExpr):
    def __init__(self, mod, table, idx):
        self.mod = mod
        self.table = table
        self.idx = idx

    def children(self):
        return [self.idx]

    def as_js(self):
        return '{}["{}"].get({})'.format(self.mod, self.table, self.idx.as_js())

class LiftRefExpr(BaseExpr):
    def __init__(self, expr):
        self.expr = expr

    def children(self):
        return [self.expr]

    def as_js(self):
        return 'liftRef({})'.format(self.expr.as_js())

class LowerRefExpr(BaseExpr):
    def __init__(self, expr):
        self.expr = expr

    def children(self):
        return [self.expr]

    def as_js(self):
        return 'lowerRef({})'.format(self.expr.as_js())

class UnreachableExpr(BaseExpr):
    def as_js(self):
        return '(function() { throw "UNREACHABLE"; })()'
    def as_wat(self):
        return '(unreachable)'

class LambdaExpr(BaseExpr):
    def __init__(self, ty, body, num_locals):
        self.fn_ty = ty
        self.body = body
        # num_locals here is the number of locals present when the lambda is
        # declared, in order to assign lambda local values
        self.num_locals = num_locals

    def children(self):
        return [self.body]

    def as_js(self):
        args = ', '.join('x' + str(i + self.num_locals) for i in range(len(self.fn_ty.params)))
        return '(({}) => {})'.format(args, self.body.as_js())

# naming; ugh
class CallExprExpr(BaseExpr):
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args

    def children(self):
        return [self.fn] + self.args

    def as_js(self):
        return '{}({})'.format(self.fn.as_js(), ', '.join(arg.as_js() for arg in self.args))

class MakeRecordExpr(BaseExpr):
    def __init__(self, ty, fields):
        self.record_ty = ty
        self.fields = fields

    def ty(self):
        return self.record_ty

    def children(self):
        return [expr for _, expr in self.fields]

    def as_js(self):
        ret = '{ '
        for field, expr in self.fields:
            ret += '"{}": {}, '.format(field, expr.as_js())
        ret += '}'
        return ret

class ReadFieldExpr(BaseExpr):
    def __init__(self, record, field, expr):
        self.record = record
        self.field = field
        self.expr = expr

    def children(self):
        return [self.expr]

    def as_js(self):
        return '{}["{}"]'.format(self.expr.as_js(), self.field)
