from collections import namedtuple

class Expr:
    def eval(self):
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

class Constant(Expr, namedtuple("Constant", ["value"])):
    def eval(self):
        return self.value

class Add(Expr, namedtuple("Add", ["expr1", "expr2"])):
    def eval(self):
        return self.expr1.eval() + self.expr2.eval()

class Subtract(Expr, namedtuple("Subtract", ["expr1", "expr2"])):
    def eval(self):
        return self.expr1.eval() - self.expr2.eval()

class Multiply(Expr, namedtuple("Multiply", ["expr1", "expr2"])):
    def eval(self):
        return self.expr1.eval() * self.expr2.eval()

class Divide(Expr, namedtuple("Divide", ["expr1", "expr2"])):
    def eval(self):
        return self.expr1.eval() / self.expr2.eval()

class Power(Expr, namedtuple("Power", ["expr1", "expr2"])):
    def eval(self):
        return self.expr1.eval() ** self.expr2.eval()
