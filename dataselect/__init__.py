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
        warnings.warn(name + " already taken", RuntimeWarning)
    else:
        custom_funcs[name] = func
    return func

def pick(whitelist, dictionary):
    return toolz.keyfilter(lambda k: k in whitelist, dictionary)

class Selector(object):
    def __init__(self, expr, symbols=None, custom_funcs=()):
        if symbols is None: # assume var names are column names too
            self.symbols = {s:s for s in map(str, expr.atoms(sympy.Symbol))}
        else:
            self.symbols = symbols
        self.custom_funcs = custom_funcs
        self.funcs = {}

        def register_custom_functions(expr):
            if isinstance(expr.func, UndefinedFunction):
                name = "f{}".format(len(self.funcs))
                self.funcs[name] = None # reserve name

                args = (register_custom_functions(arg) for arg in expr.args)
                self.funcs[name] = expr.func(*args)
                return sympy.Symbol(name)
            elif expr.args:
                args = (register_custom_functions(arg) for arg in expr.args)
                return expr.func(*args)
            else:
                return expr
        self.expr = register_custom_functions(expr)

    def __call__(self, data):
        kwargs = {k: data[v] for k, v in self.symbols.iteritems()}

        def compute(expr):
            symbols = expr.atoms(sympy.Symbol)
            kwarg = pick(map(str, symbols), kwargs)
            f = sympy.lambdify(symbols, expr, "numpy")
            return f(**kwarg)

        for fs, sym_func in sorted(self.funcs.iteritems(), reverse=True):
            funcname = str(sym_func.func)
            if funcname in self.custom_funcs:
                func = self.custom_funcs[funcname]
            else:
                func = custom_funcs[funcname]
            args = (compute(arg) for arg in sym_func.args)
            kwargs[fs] = func(*args)

        return compute(self.expr)

lpar = pp.Suppress("(")
rpar = pp.Suppress(")")
comma = pp.Suppress(",")
digits = pp.Word(pp.nums)
number = pp.Optional("-") + (digits + "." + digits | digits)
number = number.setParseAction(lambda t: float("".join(t)))
func_name = pp.Word(pp.alphanums + "_")

def parse(s):
    expr = pp.Forward()
    args = pp.Group(pp.ZeroOrMore(expr + comma) + expr)

    symbols = {}
    def register_var(t):
        name = t[0]
        if name in symbols:
            return symbols[name]
        else:
            symbols[name] = "x{}".format(len(symbols))
            return symbols[name]
    var = pp.QuotedString('"', "\\").setParseAction(register_var)

    def register_func(t):
        func_name, args = t[0], t[1]
        return "{}({})".format(func_name, ",".join(map(str, args)))
    func = (func_name + lpar + args + rpar).setParseAction(register_func)
    atom = var | number | lpar + expr + rpar | func

    fact = atom + pp.ZeroOrMore("!")
    expo = fact + pp.ZeroOrMore("**" + fact)
    mult = expo + pp.ZeroOrMore(pp.oneOf("* /") + expo)
    addi = mult + pp.ZeroOrMore(pp.oneOf("+ -") + mult)
    def f(ts):
        return "".join(map(str, ts))
    expr << addi.setParseAction(f)

    return parse_expr("".join(expr.parseString(s))), symbols

def select(expr, data=None, c_funcs=()):
    expr, symbols = parse(expr)
    symbols = {v:k for k, v in symbols.iteritems()} # reverse mapping
    s = Selector(expr, symbols, c_funcs)

    if data is None:
        return s
    else:
        return s(data)
