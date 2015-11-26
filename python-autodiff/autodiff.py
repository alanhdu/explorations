from collections import namedtuple
import math

class Expr:
    def eval(self, point):
        raise NotImplementedError("eval not implemented")

    def diff(self, direction, point):
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
    def eval(self, point):
        return point[self.name]

    def forward_diff(self, direction, point):
        return direction[self.name]

class Constant(Expr, namedtuple("Constant", ["value"])):
    def eval(self, point):
        return self.value

    def forward_diff(self, direction, point):
        return 0

class Add(Expr, namedtuple("Add", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) + self.expr2.eval(point)

    def forward_diff(self, direction, point):
        return self.expr1.forward_diff(direction, point) + \
            self.expr2.forward_diff(direction, point)

class Subtract(Expr, namedtuple("Subtract", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) - self.expr2.eval(point)

    def forward_diff(self, direction, point):
        return self.expr1.forward_diff(direction, point) - \
            self.expr2.forward_diff(direction, point)

class Multiply(Expr, namedtuple("Multiply", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) * self.expr2.eval(point)

    def forward_diff(self, direction, point):
        x1 = self.expr1.eval(point)
        x2 = self.expr2.eval(point)
        d1 = self.expr1.forward_diff(direction, point)
        d2 = self.expr2.forward_diff(direction, point)

        return x1 * d2 + x2 * d1

class Divide(Expr, namedtuple("Divide", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) / self.expr2.eval(point)

    def forward_diff(self, direction, point):
        low = self.expr2.eval(point)
        dlow = self.expr2.forward_diff(direction, point)
        high = self.expr1.eval(point)
        dhigh = self.expr1.forward_diff(direction, point)

        # low d high - high d-low, over denominator squared we go!
        return (low * dhigh - high * dlow) / low ** 2

class Pow(Expr, namedtuple("Pow", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) ** self.expr2.eval(point)

    def forward_diff(self, direction, point):
        # D_x[f ** g] = f ** (g - 1) * (g * f' + f * log f * g'

        base = self.expr1.eval(point)
        dbase = self.expr1.forward_diff(direction, point)
        exp = self.expr2.eval(point)
        dexp = self.expr2.forward_diff(direction, point)

        if base == 0:       # avoid MathDomainError
            return 0

        return base ** (exp - 1) * (exp * dbase + base * math.log(base) * dexp)
