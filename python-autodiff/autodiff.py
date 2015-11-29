from collections import namedtuple
import math

Point = "Dict[str, float]"
ForwardDiff = namedtuple("ForwardDiff", ["value", "diff"])

class Expr:
    def eval(self, point: Point) -> float:
        """ Evaluate the expr @ the given point.

        :param point: Dict[str, float]. Maps variable names to their value
        :returns float:
        """
        raise NotImplementedError("eval not implemented")

    def forward_diff(self, direction: Point, point: Point) -> float:
        """ Evaulate the directional derivative of a direction @ a point via
        forward-mode automatic differentiation

        :param point: Dict[str, float]. Maps variable names to their value
        :param direction: Dict[str, float]. Maps variable names to their value
        :returns float:
        """
        return self._forward_diff(direction, point).diff

    def _forward_diff(self, direction: Point, point: Point) -> ForwardDiff:
        raise NotImplementedError("forward_diff not implemented")

    def reverse_diff(self, point: Point) -> Point:
        """ Evaulate the gradient of a direction @ a point via
        reverse-mode automatic differentiation.

        Internally dispatches to subclass-specific `_reverse_diff`

        :param point: Dict[str, float]. Maps variable names to their value
        :returns Dict[str, float]: Returns gradient @ point
        """
        x = {key: 0 for key in point}
        self._reverse_diff(point, 1, x)
        return x

    def _reverse_diff(self, point: Point, adjoint: float, answer: Point):
        raise NotImplementedError("reverse_diff not implemented")

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

    def _forward_diff(self, direction, point):
        return ForwardDiff(value=point[self.name], diff=direction[self.name])

    def _reverse_diff(self, point, adjoint, answer):
        answer[self.name] += adjoint

class Constant(Expr, namedtuple("Constant", ["value"])):
    def eval(self, point):
        return self.value

    def _forward_diff(self, direction, point):
        return ForwardDiff(value=self.value, diff=0)

    def _reverse_diff(self, point, adjoint, answer):
        pass

class Add(Expr, namedtuple("Add", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) + self.expr2.eval(point)

    def _forward_diff(self, direction, point):
        lhs = self.expr1._forward_diff(direction, point)
        rhs = self.expr2._forward_diff(direction, point)

        return ForwardDiff(value=lhs.value + rhs.value,
                           diff=lhs.diff + rhs.diff)

    def _reverse_diff(self, point, adjoint, answer):
        self.expr1._reverse_diff(point, adjoint, answer)
        self.expr2._reverse_diff(point, adjoint, answer)

class Subtract(Expr, namedtuple("Subtract", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) - self.expr2.eval(point)

    def _forward_diff(self, direction, point):
        lhs = self.expr1._forward_diff(direction, point)
        rhs = self.expr2._forward_diff(direction, point)

        return ForwardDiff(value=lhs.value - rhs.value,
                           diff=lhs.diff - rhs.diff)

    def _reverse_diff(self, point, adjoint, answer):
        self.expr1._reverse_diff(point, adjoint, answer)
        self.expr2._reverse_diff(point, -adjoint, answer)

class Multiply(Expr, namedtuple("Multiply", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) * self.expr2.eval(point)

    def _forward_diff(self, direction, point):
        lhs = self.expr1._forward_diff(direction, point)
        rhs = self.expr2._forward_diff(direction, point)

        return ForwardDiff(value=lhs.value * rhs.value,
                           diff=lhs.diff * rhs.value + rhs.diff * lhs.value)

    def _reverse_diff(self, point, adjoint, answer):
        lhs = self.expr1.eval(point)
        rhs = self.expr2.eval(point)
        self.expr1._reverse_diff(point, adjoint * rhs, answer)
        self.expr2._reverse_diff(point, adjoint * lhs, answer)

class Divide(Expr, namedtuple("Divide", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) / self.expr2.eval(point)

    def _forward_diff(self, direction, point):
        high = self.expr1._forward_diff(direction, point)
        low = self.expr2._forward_diff(direction, point)

        # low d high - high d-low, over denominator squared we go!
        diff = (low.value * high.diff - high.value * low.diff) / low.value ** 2
        return ForwardDiff(value=high.value / low.value,
                           diff=diff)

    def _reverse_diff(self, point, adjoint, answer):
        lhs = self.expr1.eval(point)
        rhs = self.expr2.eval(point)
        self.expr1._reverse_diff(point, adjoint / rhs, answer)
        self.expr2._reverse_diff(point, -adjoint * lhs / rhs ** 2, answer)

class Pow(Expr, namedtuple("Pow", ["expr1", "expr2"])):
    def eval(self, point):
        return self.expr1.eval(point) ** self.expr2.eval(point)

    def _forward_diff(self, direction, point):
        # D_x[f ** g] = D_x[exp(g ln f)] = exp(g ln f) D_x[g ln f]
        #             = exp(g ln f) (g'ln f + gf' / f)
        #             = f ** (g - 1) (fg' ln f + gf')

        base = self.expr1._forward_diff(direction, point)
        exp = self.expr2._forward_diff(direction, point)

        if base.value == 0:     # avoid MathDomainError
            diff = 0
        else:
            diff = (base.value ** (exp.value - 1) *
                    (exp.value * base.diff +
                     base.value * exp.diff * math.log(base.value)))

        return ForwardDiff(value=base.value ** exp.value, diff=diff)

    def _reverse_diff(self, point, adjoint, answer):
        base = self.expr1.eval(point)
        exp = self.expr2.eval(point)

        self.expr1._reverse_diff(point, adjoint * exp * base ** (exp - 1),
                                 answer)
        self.expr2._reverse_diff(point,
                                 adjoint * math.log(base) * base ** exp,
                                 answer)
