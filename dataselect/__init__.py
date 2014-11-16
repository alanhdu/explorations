import numpy as np
import pyparsing as pp


class Expr(object):
    __slots__ = ["head", "args"]
    def __init__(self, head, args=None):
        self.head = head
        self.args = args
    def __str__(self):
        if self.args:
            return str(self.head) + " " + str(self.args)
        else:
            return str(self.head)
    def __repr__(self):
        return str(self)
    def __call__(self, data):
        if self.args is None:
            return data[self.head]

var = pp.QuotedString('"', "\\")
digits = pp.Word(pp.nums)
number = pp.Optional("-") + (digits + "." + digits | digits)
number = number.setParseAction(lambda t: float("".join(t)))
operator = pp.oneOf("+ / * - **")
func_name = pp.Word(pp.alphanums + "_")


lpar = pp.Suppress("(")
rpar = pp.Suppress(")")
comma = pp.Suppress(",")

expr = pp.Forward()
args = pp.Group(pp.ZeroOrMore(expr + comma) + expr)
func = (func_name + lpar + args + rpar).setParseAction(lambda t: Expr(t[0], t[1]))
atom = var | number | lpar + expr + rpar | func

def temp(t):
    if len(t) > 0:
        e = Expr(t[-1]
        for fact in t[1:]:
            e = Expr("!", (e,))
        return e
    else:
        return t

fact = (atom + pp.ZeroOrMore("!"))
def op2Expr(t):
    if len(t) > 1:
        e = Expr(t[-1])
        for i in xrange(len(t) - 2, 0, -2):
            e = Expr(t[i], (t[i-1], e))
        return e
    else:
        return t
expo = (fact + pp.ZeroOrMore("**" + fact)).setParseAction(op2Expr)
mult = (expo + pp.ZeroOrMore(pp.oneOf("* /") + expo)).setParseAction(op2Expr)
addi = (mult + pp.ZeroOrMore(pp.oneOf("+ -") + mult)).setParseAction(op2Expr)
expr << addi
