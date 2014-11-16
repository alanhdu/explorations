import numpy as np
import pyparsing as pp
from sympy.parsing.sympy_parser import parse_expr
import sympy

lpar = pp.Suppress("(")
rpar = pp.Suppress(")")
comma = pp.Suppress(",")
digits = pp.Word(pp.nums)
number = pp.Optional("-") + (digits + "." + digits | digits)
number = number.setParseAction(lambda t: float("".join(t)))
func_name = pp.Word(pp.alphanums + "_")

def parse(s):
    symbols = {}
    # hack w/ mutability so inner functions have access
    symbol_count = {"count": 0} 

    expr = pp.Forward()
    args = pp.Group(pp.ZeroOrMore(expr + comma) + expr)

    def register_var(t):
        name = t[0]
        if name in symbols:
            return symbols[name]
        else:
            symbols[name] = "x{}".format(symbol_count["count"])
            symbol_count["count"] += 1
            return symbols[name]
    var = pp.QuotedString('"', "\\").setParseAction(register_var)

    def register_func(t):
        func_name, args = t[0], t[1]
        return "{}({})".format(func_name, str(args)[1:-1])
    func = (func_name + lpar + args + rpar).setParseAction(register_func)
    atom = var | number | lpar + expr + rpar | func

    def register_operator(ts):
        return parse_expr("".join(str(t) for t in ts))
    fact = atom + pp.ZeroOrMore("!")
    expo = fact + pp.ZeroOrMore("**" + fact)
    mult = expo + pp.ZeroOrMore(pp.oneOf("* /") + expo)
    addi = mult + pp.ZeroOrMore(pp.oneOf("+ -") + mult)
    expr << addi.setParseAction(register_operator)

    return expr.parseString(s)[0]
