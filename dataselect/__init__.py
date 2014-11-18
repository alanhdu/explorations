import warnings

import pyparsing as pp
from sympy.parsing.sympy_parser import parse_expr
from sympy.core.function import UndefinedFunction
import toolz
import sympy

custom_funcs = {}

@toolz.curry
def register(name, func):
    if name in custom_funcs:
        warnings.warn("Name '" + name + "' already taken", RuntimeWarning)
    custom_funcs[name] = func
    return func

def pick(whitelist, dictionary):
    return toolz.keyfilter(lambda k: k in whitelist, dictionary)

class Selector(object):
    def __init__(self, expr, symbols=None, custom_funcs=(), get=toolz.get):
        if symbols is None: # assume var names stay unchanged
            self.symbols = {s:s for s in map(str, expr.atoms(sympy.Symbol))}
        else:
            self.symbols = symbols
        self.custom_funcs = custom_funcs
        self.funcs = {}
        self.get = get

        self.original_expr = expr
        self.expr = replace_custom_functions(expr, self.funcs)

    def _sympy_(self):
        return self.original_expr

    def compute(self, expr, kwargs):
        symbols = expr.atoms(sympy.Symbol)
        kwarg = pick(map(str, symbols), kwargs)
        f = sympy.lambdify(symbols, expr, "numpy")
        return f(**kwarg)

    def __call__(self, data):
        kwargs = {k: self.get(v, data) for k, v in self.symbols.iteritems()}

        for fs, sym_func in sorted(self.funcs.iteritems(), reverse=True):
            funcname = str(sym_func.func)
            if funcname in self.custom_funcs:
                func = self.custom_funcs[funcname]
            else:
                func = custom_funcs[funcname]

            args = (self.compute(arg, kwargs) for arg in sym_func.args)
            kwargs[fs] = func(*args)

        return self.compute(self.expr, kwargs)

lpar, rpar = pp.Suppress("("), pp.Suppress(")")
comma = pp.Suppress(",")

digits = pp.Word(pp.nums)
number = pp.Optional("-") + (digits + "." + digits | digits)
number = number.setParseAction(lambda t: float("".join(t)))
func_name = pp.Word(pp.alphanums + "_")


expr = pp.Forward()
args = pp.Group(pp.ZeroOrMore(expr + comma) + expr)
def register_func(t):
    fname, args = t[0], t[1]
    args=  ",".join(map(str,args))
    return "{fname}({args})".format(fname=fname, args=args)
func = (func_name + lpar + args + rpar).setParseAction(register_func)

# var's parseAction depends on "global" variable, so set it in parse function
var = pp.Forward()
atom = var | number | lpar + expr + rpar | func

# order things in order-of-operations
fact = atom + pp.ZeroOrMore("!")
expo = fact + pp.ZeroOrMore("**" + fact)
mult = expo + pp.ZeroOrMore(pp.oneOf("* /") + expo)
addi = mult + pp.ZeroOrMore(pp.oneOf("+ -") + mult)

expr << addi.setParseAction(lambda ts: "".join(map(str, ts)))

def parse(s):
    symbols = {}
    def register_var(t):
        name = t[0]
        if name in symbols:
            return symbols[name]
        else:
            symbols[name] = "x{}".format(len(symbols))
            return symbols[name]
    var << pp.QuotedString('"', "\\").setParseAction(register_var)

    sympy_expr = "".join(expr.parseString(s))
    return parse_expr(sympy_expr), symbols

def replace_custom_functions(expr, funcs):
    if isinstance(expr.func, UndefinedFunction):
        name = "f{}".format(len(funcs))
        funcs[name] = None # reserve name

        args = (replace_custom_functions(arg, funcs) for arg in expr.args)
        funcs[name] = expr.func(*args)
        return sympy.Symbol(name)
    elif expr.args:
        args = (replace_custom_functions(arg, funcs) for arg in expr.args)
        return expr.func(*args)
    else:
        return expr

def select(expr, data=None, get=toolz.get, custom_funcs=()):
    expr, symbols = parse(expr)
    symbols = {v:k for k, v in symbols.iteritems()} # reverse mapping
    s = Selector(expr, symbols, custom_funcs=custom_funcs, get=get)

    if data is None:
        return s
    else:
        return s(data)
