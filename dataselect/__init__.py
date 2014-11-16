import numpy as np
import pyparsing as pp
from sympy.parsing.sympy_parser import parse_expr
from sympy.core.function import UndefinedFunction
from toolz import keyfilter
import sympy

custom_funcs = {"rank": np.log}

def pick(whitelist, d):
    return keyfilter(lambda k: k in whitelist, d)

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

class Selector(object):
    def __init__(self, s):
        expr, symbols = parse(s)
        self.symbols = {v:k for k, v in symbols.iteritems()}
        self.funcs = {}

        def compute(expr):
            if isinstance(expr.func, UndefinedFunction):

                name = "f{}".format(len(self.funcs))
                f = sympy.Symbol(name)
                self.funcs[name] = ""
                self.funcs[name] = expr.func(*(compute(arg) for arg in expr.args))
                return f
            elif expr.args:
                args = [compute(arg) for arg in expr.args]
                return expr.func(*args)
            else:
                return expr
        self.expr = compute(expr)
    def __call__(self, data):
        kwargs = {k: data[v] for k, v in self.symbols.iteritems()}

        def compute(expr):
            symbols = expr.atoms(sympy.Symbol)
            kwarg = pick(map(str, symbols), kwargs)
            f = sympy.lambdify(symbols, expr, "numpy")
            return f(**kwarg)

        for fs in sorted(self.funcs, reverse=True):
            func = self.funcs[fs]
            funcname = str(func.func)
            s = [compute(arg) for arg in func.args]
            kwargs[fs] = custom_funcs[funcname](*(compute(arg) for arg in func.args))

        return compute(self.expr)

def compute(expr, data):
    s = Selector(expr)
    return s(data)
