import unittest

import numpy as np
from sympy.parsing.sympy_parser import parse_expr
import sympy

import dataselect as ds

class ParseTest(unittest.TestCase):
    def test_variable_replacement(self):
        expr, symbols = ds.parse('"test" + "test1" + "te\\"s ()t2" + "test1"')
        sym_symbols = expr.atoms(sympy.Symbol)
        assert len(sym_symbols) == len(symbols) == 3
        for col in ["test", "test1", 'te"s ()t2']:
            assert col in symbols
        for symbol in sym_symbols:
            assert str(symbol) in symbols.values()
    def test_order_of_ops(self):
        s = '"x" + "y" * "z"'
        expr, symbols = ds.parse(s)
        symbols = {k: sympy.Symbol(v) for k, v in symbols.iteritems()}
        for a in "xyz":
            assert a in symbols
        x, y, z = symbols["x"], symbols["y"], symbols["z"]
        assert expr == (x + (y*z))
    def test_complicated_expression(self):
        s = 'log("x" / "y") + exp("y" * "z") * "x" + "x" + "x"'
        expr, symbols = ds.parse(s)
        symbols = {k: sympy.Symbol(v) for k, v in symbols.iteritems()}
        for a in "xyz":
            assert a in symbols
        x, y, z = symbols["x"], symbols["y"], symbols["z"]
        assert expr == sympy.log(x / y) + sympy.exp(y * z) * x + x + x

class SelectorTest(unittest.TestCase):
    def setUp(self):
        self.data = {"x": 2, "y": 3, "z": 4, "x1":10}
        self.data2 = {"x": [1, 2, 3]}
    def test_arithmetic(self):
        x, y, z = sympy.symbols("x y z")
        s = ds.Selector(x + y * z)(self.data)
        assert s == 2 + 3 * 4
    def test_sympy_functions(self):
        x = sympy.symbols("x")
        s = ds.Selector(sympy.sin(sympy.cosh(sympy.log(x))))(self.data)
        assert s == np.sin(np.cosh(np.log(2)))
    def test_custom_functions(self):
        custom_funcs = {"mean": lambda x: sum(x) / len(x)}
        @ds.register("double")
        def double(s):
            return 2 * s
        f = ds.Selector(parse_expr("double(mean(x)) + 1"), custom_funcs=custom_funcs)
        assert f(self.data2) == double(custom_funcs["mean"](self.data2["x"])) + 1
    def test_custom_get(self):
        f = ds.Selector(parse_expr('log(x)'), get=lambda v, d: d[v + "1"])
        s = f(self.data)
        assert s == np.log(10)

class SelectTest(unittest.TestCase):
    def setUp(self):
        self.data = {"x": 2, "y": 3, "z": 4, "x1":10}
        self.data2 = {"x": [1, 2, 3]}
    def test_arithmetic(self):
        assert ds.select('"x" + "y" * "z"', self.data) == 2 + 3 * 4
    def test_sympy_functions(self):
        assert ds.select('sin(cosh(log("x")))', self.data) == np.sin(np.cosh(np.log(2)))
    def test_register(self):
        custom_funcs = {"mean": lambda x: sum(x) / len(x)}
        @ds.register("triple")
        def triple(s):
            return 3 * s
        s = ds.select('triple(mean("x")) + 1', self.data2, custom_funcs=custom_funcs)
        assert s == triple(custom_funcs["mean"](self.data2["x"])) + 1
    def test_custom_get(self):
        s = ds.select('log("x")', self.data, get=lambda v, d: d[v + "1"])
        assert s == np.log(self.data["x1"])

if __name__ == "__main__":
    unittest.main()
