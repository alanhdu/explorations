import numpy as np
import pyparsing as pp

var = pp.QuotedString('"', "\\")
digits = pp.Word(pp.nums)
number = pp.Optional("-") + (digits + "." + digits | digits)
number = number.setParseAction(lambda t: float("".join(t)))
operator = pp.oneOf("+ / * - **")
func_name = pp.Word(pp.alphanums + "_")

expr = pp.Forward()
func = func_name + "(" + pp.Group(pp.ZeroOrMore(expr + ",") + expr) + ")"
atom = var | number | "(" + expr + ")" | func

fact = atom + pp.ZeroOrMore("!")
expo = fact + pp.ZeroOrMore("**" + fact)
mult = expo + pp.ZeroOrMore(pp.oneOf("* /") + expo)
addi = mult + pp.ZeroOrMore(pp.oneOf("+ -") + mult)


expr << addi

"""
expr = pp.operatorPrecedence(atom,
            [#("!", 1, pp.opAssoc.LEFT),
             #("**", 2, pp.opAssoc.RIGHT),
             #(pp.oneOf("+ -"), 1, pp.opAssoc.RIGHT),
             #(pp.oneOf("* /"), 2, pp.opAssoc.LEFT),
             (pp.oneOf("+ -"), 2, pp.opAssoc.LEFT),],
            lpar="(", rpar=")")
"""


#expr = pp.Forward()
#expr << atom | expr + operator + expr

"""
func_name = pp.Word(pp.alphanums + "_")
expr = pp.Forward()
args = pp.ZeroOrMore(expr + ",") + expr

expr << infix_expr | atom | func_name + "(" + args + ")"
"""
