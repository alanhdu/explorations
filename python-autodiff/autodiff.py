from collections import namedtuple
import math

Point = "Dict[str, float]"

class Expr:
    def eval(self, point: Point) -> float:
        """ Evaluate the expr @ the given point.

        :param point: Dict[str, float]. Maps variable names to their value
        :returns float:
        """
        return self._eval(point, {})

    def _eval(self, point: Point, cache: dict) -> float:
        """ Fills out a cache mapping Expr objects to their evaluated value.

        We can't just use functools.lru_cache here because Point (dictionaries)
        aren't hashable.
        """
        raise NotImplementedError

    def forward_diff(self, direction: Point, point: Point) -> float:
        """ Evaulate the directional derivative of a direction @ a point via
        forward-mode automatic differentiation

        :param point: Dict[str, float]. Maps variable names to their value
        :param direction: Dict[str, float]. Maps variable names to their value
        :returns float:
        """
        cache = {}
        self._eval(point, cache)
        return self._forward_diff(direction, point, cache)

    def _forward_diff(self, direction: Point, point: Point, cache) -> float:
        raise NotImplementedError

    def reverse_diff(self, point: Point) -> Point:
        """ Evaulate the gradient of a direction @ a point via
        reverse-mode automatic differentiation.

        Internally dispatches to subclass-specific `_reverse_diff`

        :param point: Dict[str, float]. Maps variable names to their value
        :returns Dict[str, float]: Returns gradient @ point
        """
        cache = {}
        self._eval(point, cache)
        x = {key: 0 for key in point}
        self._reverse_diff(point, 1, x, cache)
        return x

    def _reverse_diff(self, point: Point, adjoint: float,
                      gradient: Point, cache):
        raise NotImplementedError

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
    def _eval(self, point, cache):
        cache[id(self)] = point[self.name]
        return point[self.name]

    def _forward_diff(self, direction, point, cache):
        return direction[self.name]

    def _reverse_diff(self, point, adjoint, gradient, cache):
        gradient[self.name] += adjoint

class Constant(Expr, namedtuple("Constant", ["value"])):
    def _eval(self, point, cache):
        cache[id(self)] = self.value
        return self.value

    def _forward_diff(self, direction, point, cache):
        return 0

    def _reverse_diff(self, point, ajoint, gradient, cache):
        pass

class Add(Expr, namedtuple("Add", ["expr1", "expr2"])):
    def _eval(self, point, cache):
        if id(self) not in cache:
            eval1, eval2 = self.expr1._eval, self.expr2._eval
            cache[id(self)] = eval1(point, cache) + eval2(point, cache)
        return cache[id(self)]

    def _forward_diff(self, direction, point, cache):
        return (self.expr1._forward_diff(direction, point, cache) +
                self.expr2._forward_diff(direction, point, cache))

    def _reverse_diff(self, point, adjoint, gradient, cache):
        self.expr1._reverse_diff(point, adjoint, gradient, cache)
        self.expr2._reverse_diff(point, adjoint, gradient, cache)

class Subtract(Expr, namedtuple("Subtract", ["expr1", "expr2"])):
    def _eval(self, point, cache):
        if id(self) not in cache:
            eval1, eval2 = self.expr1._eval, self.expr2._eval
            cache[id(self)] = eval1(point, cache) - eval2(point, cache)
        return cache[id(self)]

    def _forward_diff(self, direction, point, cache):
        return (self.expr1._forward_diff(direction, point, cache) -
                self.expr2._forward_diff(direction, point, cache))

    def _reverse_diff(self, point, adjoint, gradient, cache):
        self.expr1._reverse_diff(point, adjoint, gradient, cache)
        self.expr2._reverse_diff(point, -adjoint, gradient, cache)

class Multiply(Expr, namedtuple("Multiply", ["expr1", "expr2"])):
    def _eval(self, point, cache):
        if id(self) not in cache:
            eval1, eval2 = self.expr1._eval, self.expr2._eval
            cache[id(self)] = eval1(point, cache) * eval2(point, cache)
        return cache[id(self)]

    def _forward_diff(self, direction, point, cache):
        lhs = cache[id(self.expr1)]
        rhs = cache[id(self.expr2)]

        return (rhs * self.expr1._forward_diff(direction, point, cache) +
                lhs * self.expr2._forward_diff(direction, point, cache))

    def _reverse_diff(self, point, adjoint, gradient, cache):
        lhs = cache[id(self.expr1)]
        rhs = cache[id(self.expr2)]
        self.expr1._reverse_diff(point, adjoint * rhs, gradient, cache)
        self.expr2._reverse_diff(point, adjoint * lhs, gradient, cache)

class Divide(Expr, namedtuple("Divide", ["expr1", "expr2"])):
    def _eval(self, point, cache):
        if id(self) not in cache:
            eval1, eval2 = self.expr1._eval, self.expr2._eval
            cache[id(self)] = eval1(point, cache) / eval2(point, cache)
        return cache[id(self)]

    def _forward_diff(self, direction, point, cache):
        high = cache[id(self.expr1)]
        low = cache[id(self.expr2)]
        dhigh = self.expr1._forward_diff(direction, point, cache)
        dlow = self.expr2._forward_diff(direction, point, cache)

        return (low * dhigh - high * dlow) / low ** 2

    def _reverse_diff(self, point, adjoint, gradient, cache):
        high = cache[id(self.expr1)]
        low = cache[id(self.expr2)]
        self.expr1._reverse_diff(point, adjoint / low, gradient, cache)
        self.expr2._reverse_diff(point, -adjoint * high / low ** 2, gradient,
                                 cache)

class Pow(Expr, namedtuple("Pow", ["expr1", "expr2"])):
    def _eval(self, point, cache):
        if id(self) not in cache:
            eval1, eval2 = self.expr1._eval, self.expr2._eval
            cache[id(self)] = eval1(point, cache) ** eval2(point, cache)
        return cache[id(self)]

    def _forward_diff(self, direction, point, cache):
        base = cache[id(self.expr1)]
        exp = cache[id(self.expr2)]
        dbase = self.expr1._forward_diff(direction, point, cache)
        dexp = self.expr2._forward_diff(direction, point, cache)

        if base == 0:       # avoid MathDomainError
            return 0
        else:
            # D_x[f ** g] = D_x[exp(g ln f)] = exp(g ln f) D_x[g ln f]
            #             = exp(g ln f) (g'ln f + gf' / f)
            #             = f ** (g - 1) (fg' ln f + gf')

            return (base ** (exp - 1) *
                    (exp * dbase + base * dexp * math.log(base)))

    def _reverse_diff(self, point, adjoint, gradient, cache):
        base = cache[id(self.expr1)]
        exp = cache[id(self.expr2)]

        self.expr1._reverse_diff(point, adjoint * exp * base ** (exp - 1),
                                 gradient, cache)
        self.expr2._reverse_diff(point, adjoint * math.log(base) * base ** exp,
                                 gradient, cache)
