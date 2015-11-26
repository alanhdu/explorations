from collections import namedtuple
import math

class Expr:
    def eval(self, **kwargs):
        raise NotImplementedError("eval not implemented")

    def diff(self, **kwargs):
        raise NotImplementedError("diff not implemented")

    def __add__(self, other):
        return Add(self, other)

    def __sub__(self, other):
        return Subtract(self, other)

    def __mul__(self, other):
        return Multiply(self, other)

    def __truediv__(self, other):
        return Divide(self, other)

    def __pow__(self, other):
        return Pow(self, other)

class Variable(Expr, namedtuple("Variable", ["name"])):
    def eval(self, **kwargs):
        return kwargs[self.name]

    def forward_diff(self, **kwargs):
        if self.name in kwargs:
            return 1
        else:
            return 0

class Constant(Expr, namedtuple("Constant", ["value"])):
    def eval(self, **kwargs):
        return self.value

    def forward_diff(self, **kwargs):
        return 0

class Add(Expr, namedtuple("Add", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) + self.expr2.eval(**kwargs)

    def forward_diff(self, **kwargs):
        return self.expr1.forward_diff(**kwargs) + \
            self.expr2.forward_diff(**kwargs)

class Subtract(Expr, namedtuple("Subtract", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) - self.expr2.eval(**kwargs)

    def forward_diff(self, **kwargs):
        return self.expr1.forward_diff(**kwargs) - \
            self.expr2.forward_diff(**kwargs)

class Multiply(Expr, namedtuple("Multiply", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) * self.expr2.eval(**kwargs)

    def forward_diff(self, **kwargs):
        a = self.expr1.eval(**kwargs) * self.expr2.forward_diff(**kwargs)
        b = self.expr2.eval(**kwargs) * self.expr1.forward_diff(**kwargs)
        return a + b

class Divide(Expr, namedtuple("Divide", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) / self.expr2.eval(**kwargs)

    def forward_diff(self, **kwargs):
        low = self.expr2.eval(**kwargs)
        dlow = self.expr2.forward_diff(**kwargs)
        high = self.expr1.eval(**kwargs)
        dhigh = self.expr1.forward_diff(**kwargs)

        # low d high - high d-low, over denominator squared we go!
        return (low * dhigh - high * dlow) / low ** 2

class Pow(Expr, namedtuple("Pow", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) ** self.expr2.eval(**kwargs)

    def forward_diff(self, **kwargs):
        # D_x[f ** g] = f ** (g - 1) * (g * f' + f * log f * g'

        base = self.expr1.eval(**kwargs)
        dbase = self.expr1.forward_diff(**kwargs)
        exp = self.expr2.eval(**kwargs)
        dexp = self.expr2.forward_diff(**kwargs)

        if base == 0:       # avoid MathDomainError
            return 0

        return base ** (exp - 1) * (exp * dbase + base * math.log(base) * dexp)
