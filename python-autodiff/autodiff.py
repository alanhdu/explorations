from collections import namedtuple

class Expr:
    def eval(self, **kwargs):
        raise NotImplementedError("eval not implemented")

    def __add__(self, other):
        return Add(self, other)

    def __sub__(self, other):
        return Subtract(self, other)

    def __mul__(self, other):
        return Multiply(self, other)

    def __truediv__(self, other):
        return Divide(self, other)

    def __pow__(self, other):
        return Power(self, other)

class Variable(Expr, namedtuple("Variable", ["name"])):
    def eval(self, **kwargs):
        return kwargs[self.name]

class Constant(Expr, namedtuple("Constant", ["value"])):
    def eval(self, **kwargs):
        return self.value

class Add(Expr, namedtuple("Add", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) + self.expr2.eval(**kwargs)

class Subtract(Expr, namedtuple("Subtract", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) - self.expr2.eval(**kwargs)

class Multiply(Expr, namedtuple("Multiply", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) * self.expr2.eval(**kwargs)

class Divide(Expr, namedtuple("Divide", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) / self.expr2.eval(**kwargs)

class Power(Expr, namedtuple("Power", ["expr1", "expr2"])):
    def eval(self, **kwargs):
        return self.expr1.eval(**kwargs) ** self.expr2.eval(**kwargs)
