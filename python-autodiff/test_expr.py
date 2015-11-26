import pytest

import autodiff


def test_constant_expr():
    x = autodiff.Constant(10)
    y = autodiff.Constant(2)
    assert x.eval() == 10
    assert y.eval() == 2
    assert (x + y).eval() == 12
    assert (x * y).eval() == 20
    assert (x - y).eval() == 8
    assert (x / y).eval() == 5
    assert (x ** y).eval() == 100

    assert (x + x + x).eval() == 30
    assert (x - x - x).eval() == -10
    assert (x * x * x).eval() == 1000
    assert (x / x / x).eval() == 0.1

def test_variable_expr():
    x = autodiff.Variable("x")
    y = autodiff.Constant(10)

    assert x.eval(x=5) == 5
    assert (x + y).eval(x=5) == 15
    assert (x - y).eval(x=5) == -5
    assert (x * y).eval(x=5) == 50
    assert (x / y).eval(x=5) == 0.5
    assert (x ** y).eval(x=2) == 2 ** 10

    with pytest.raises(KeyError):
        x.eval()
