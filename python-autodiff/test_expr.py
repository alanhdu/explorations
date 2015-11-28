import math

import pytest

import autodiff


def test_constant_expr():
    x = autodiff.Constant(10)
    y = autodiff.Constant(2)
    assert x.eval({}) == 10
    assert y.eval({}) == 2
    assert (x + y).eval({}) == 12
    assert (x * y).eval({}) == 20
    assert (x - y).eval({}) == 8
    assert (x / y).eval({}) == 5
    assert (x ** y).eval({}) == 100

    assert (x + x + x).eval({}) == 30
    assert (x - x - x).eval({}) == -10
    assert (x * x * x).eval({}) == 1000
    assert (x / x / x).eval({}) == 0.1

def test_variable_expr():
    x = autodiff.Variable("x")
    y = autodiff.Constant(10)

    assert x.eval(dict(x=5)) == 5
    assert (x + y).eval(dict(x=5)) == 15
    assert (x - y).eval(dict(x=5)) == -5
    assert (x * y).eval(dict(x=5)) == 50
    assert (x / y).eval(dict(x=5)) == 0.5
    assert (x ** y).eval(dict(x=2)) == 2 ** 10

    with pytest.raises(KeyError):
        x.eval({})

def test_arithmetic_diff():
    x = autodiff.Variable("x")

    direction = {"x": 1}

    expr = x + x
    assert expr.forward_diff(direction, dict(x=5)) == 2
    assert expr.forward_diff(direction, dict(x=1)) == 2

    expr = (x + autodiff.Constant(10)) * (x + autodiff.Constant(5))
    # D_x[expr] = D_x[x ** 2 + 15 x + 150] = 2 * x + 15
    assert expr.forward_diff(direction, dict(x=5)) == 25
    assert expr.forward_diff(direction, dict(x=0)) == 15

    expr = (x + autodiff.Constant(10)) / (x * x)
    # D_x[expr] = D_x[(x + 10) / (x ** 2)] = - 1 / x**2 - 20 / x ** 3
    assert expr.forward_diff(direction, dict(x=1)) == -21
    assert expr.forward_diff(direction, dict(x=2)) == -0.25 - 20 / 8

    expr = x
    for _ in range(50):
        expr = expr * x
    assert expr.forward_diff(direction, dict(x=0)) == 0
    assert expr.forward_diff(direction, dict(x=1)) == 51
    assert expr.forward_diff(direction, dict(x=2)) == 51 * 2 ** 50

def test_power_diff():
    x = autodiff.Variable("x")

    direction = {"x": 1}

    expr = x ** autodiff.Constant(2)
    assert expr.forward_diff(direction, dict(x=0)) == 0
    assert expr.forward_diff(direction, dict(x=1)) == 2
    assert expr.forward_diff(direction, dict(x=2)) == 4

    expr = autodiff.Constant(math.e) ** x
    assert expr.forward_diff(direction, dict(x=0)) == 1
    assert expr.forward_diff(direction, dict(x=1)) == math.e
    assert expr.forward_diff(direction, dict(x=2)) == math.e ** 2

    expr = x
    for i in range(100):
        expr = expr ** x

    assert expr.forward_diff(direction, dict(x=1)) == 1

points = [{"x": 1, "y": 1}, {"x": 0.5, "y": 1.1}, {"x": 13.4, "y": 0.2}]

@pytest.mark.parametrize("point", points)
def test_reverse_diff1(point):
    x = autodiff.Variable('x')
    y = autodiff.Variable('y')

    expr = x * y + x / y

    # grad expr = {"x": y + 1 / y, "y": x - x / y ** 2}
    x, y = point["x"], point["y"]
    assert expr.reverse_diff(point) == {"x": y + 1 / y,
                                        "y": x - x / y ** 2}
@pytest.mark.parametrize("point", points)
def test_reverse_diff2(point):
    x = autodiff.Variable('x')
    y = autodiff.Variable('y')

    expr = x * x * y - x * y * y

    # grad expr = {"x": y ** 2 - 2xy, "y": 2xy - x ** 2}
    x, y = point["x"], point["y"]
    assert expr.reverse_diff(point) == {"x": 2 * x * y - y ** 2,
                                        "y": x ** 2 - 2 * x * y}

@pytest.mark.parametrize("point", points)
def test_reverse_diff3(point):
    x = autodiff.Variable('x')
    y = autodiff.Variable('y')

    expr = x ** y

    # grad expr = {"x": x ** (y - 1), "y": ln(x) * x ** y }
    x, y = point["x"], point["y"]
    assert expr.reverse_diff(point) == {"x": x ** (y - 1),
                                        "y": math.log(x) * x ** y}
