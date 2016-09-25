import warnings

import pyparsing as pp
from sympy.parsing.sympy_parser import parse_expr
from sympy.core.function import UndefinedFunction
import toolz
import sympy

custom_funcs = {}

@toolz.curry
def register(name, func):
    """
    Registers a custom function for all Selector objects

    Parameters
    ----------
    name: str
    func: function

    Returns
    ---------
    func

    Examples
    --------
    >>> @register("mean")
    ... def mean(xs):
    ...     return sum(x) / len(x)

    >>> register("double", lambda x: 2 * x)
    """
    if name in custom_funcs:
        warnings.warn("Name '" + name + "' already taken", RuntimeWarning)
    custom_funcs[name] = func
    return func

def pick(whitelist, dictionary):
    return toolz.keyfilter(lambda k: k in whitelist, dictionary)

class Selector(object):
    """
    Parses a correctly-formatted string into a sympy expression, replacing
    column names in quotes w/ sympy Symbols. Should be probably be used
    with select function

    Parameters
    ----------
    expr: sympy.Expr
    symbols: dict, default None
        Should map sympy.Symbol to corresponding column name. If it's none,
        we assume that sympy.Symbol.name is the column name
    get: function(key, data), default toolz.get
        Function that retrieves data from some object based on the key.
        Default is toolz.get(key, data), which is equivalent to data[key]
    custom_funcs: dict {string : function}, default ()
        Mapping between function name in expr and the actual function  to be
        evaluated. Default means there are no custom functions.

    Note that custom_functions can also be registered in the global
    custom_funcs variable.

    Returns
    -------
    Callable class: call the class on some data object and get corresponding
        data

    Examples
    ------------
    >>> expr = sympy.log2(sympy.Symbol('x'))
    >>> f = Selector(expr)
    >>> print f({"x": 8})
        3

    >>> expr = sympy.parse_expr('log(mean(x))')
    >>> f = Selector(expr, custom_funcs={"mean" : lambda x : sum(x) / len(x)})
    >>> print f({"x": [1, 2, 3, 4, 5]})
        3

    >>> expr = sympy.parse_expr('cosh(x)')
    >>> f = Selector(expr, get=lambda key, data: data[key + "_small"])
    >>> print f({"x_small": 0})
        1
    """
    def __init__(self, expr, symbols=None, get=toolz.get, custom_funcs=()):
        if symbols is None:  # assume var names stay unchanged
            self.symbols = {s: s for s in map(str, expr.atoms(sympy.Symbol))}
        else:
            self.symbols = symbols
        self.custom_funcs = custom_funcs
        self.funcs = {}
        self.get = get

        self.original_expr = expr
        self.expr = replace_custom_functions(expr, self.funcs)

    def _sympy_(self):
        return self.original_expr

    def _compute(self, expr, kwargs):
        symbols = expr.atoms(sympy.Symbol)
        kwarg = pick(map(str, symbols), kwargs)
        f = sympy.lambdify(symbols, expr, "numpy")
        return f(**kwarg)

    def __call__(self, data):
        kwargs = {k: self.get(v, data) for k, v in self.symbols.iteritems()}

        for fs, sym_func in sorted(self.funcs.iteritems(), reverse=True):
            funcname = str(sym_func.func)
            if funcname in self.custom_funcs:
                func = self.custom_funcs[funcname]
            else:
                func = custom_funcs[funcname]

            args = (self._compute(arg, kwargs) for arg in sym_func.args)
            kwargs[fs] = func(*args)

        return self._compute(self.expr, kwargs)

pp_lpar, pp_rpar = pp.Suppress("("), pp.Suppress(")")
pp_comma = pp.Suppress(",")

pp_digits = pp.Word(pp.nums)
pp_number = pp.Optional("-") + (pp_digits + "." + pp_digits | pp_digits)
pp_number = pp_number.setParseAction(lambda t: float("".join(t)))
pp_fname = pp.Word(pp.alphanums + "_")


pp_expr = pp.Forward()
pp_args = pp.Group(pp.ZeroOrMore(pp_expr + pp_comma) + pp_expr)
def register_func(t):
    fname, args = t[0], t[1]
    args = ",".join(map(str, args))
    return "{fname}({args})".format(fname=fname, args=args)
pp_func = (pp_fname + pp_lpar + pp_args + pp_rpar).setParseAction(register_func)

# var's parseAction depends on a state variable, so set it in parse function
pp_var = pp.Forward()
pp_atom = pp_var | pp_number | pp_lpar + pp_expr + pp_rpar | pp_func

# order things in order-of-operations
pp_fact = pp_atom + pp.ZeroOrMore("!")
pp_expo = pp_fact + pp.ZeroOrMore("**" + pp_fact)
pp_mult = pp_expo + pp.ZeroOrMore(pp.oneOf("* /") + pp_expo)
pp_addi = pp_mult + pp.ZeroOrMore(pp.oneOf("+ -") + pp_mult)

pp_expr << pp_addi.setParseAction(lambda ts: "".join(map(str, ts)))

def parse(s):
    """
    Parses a correctly-formatted string into a sympy expression, replacing
    column names in quotes w/ sympy Symbols.

    Parameters
    ----------
    s : string
        detailing query. Column names should be in quotes (use \\" to escape
        quotes). Otherwise, s should follow sympy conventions.

    Returns
    -------
    (expr, symbols)
        expr: sympy.Expr
        symbols: dict mapping sympy.Symbol -> string (column name)

    Examples
    ------------
    >>> parse('log(cosh("Column1")) + 3')
    """
    symbols = {}
    def register_var(t):
        name = t[0]
        if name in symbols:
            return symbols[name]
        else:
            symbols[name] = "x{}".format(len(symbols))
            return symbols[name]
    pp_var << pp.QuotedString('"', "\\").setParseAction(register_var)

    sympy_expr = "".join(pp_expr.parseString(s))
    return parse_expr(sympy_expr), symbols

def replace_custom_functions(expr, funcs):
    """
    Recursively finds and replaces sympy.UndefinedFunction with sympy.Symbol.
    Needed for Selector to evaluate arbitrary custom_functions that aren't
    included in sympy

    Parameters
    ----------
    expr : sympy.Expression
    funcs : dict
        Maps sympy.Symbol to arbitrary function (funcs is mutable, so it's
        edited by replace_custom_functions to be correct)

    Returns
    -------
    expr : sympy.Expression
        all arbitrary function calls have been replaced by sympy.Symbol

    Note that because dictionaries are mutable, funcs is modified to contain
    the correct starting value
    """
    if isinstance(expr.func, UndefinedFunction):
        name = "f{}".format(len(funcs))
        # Make funcs size larger, so name is updated when we recurse
        funcs[name] = None

        args = (replace_custom_functions(arg, funcs) for arg in expr.args)
        funcs[name] = expr.func(*args)
        return sympy.Symbol(name)
    elif expr.args:
        args = (replace_custom_functions(arg, funcs) for arg in expr.args)
        return expr.func(*args)
    else:
        return expr

def select(expr, data=None, get=toolz.get, custom_funcs=()):
    """
    Selects data based on an expression string

    Parameters
    ----------
    expr : string
        detailing query. Column names should be in quotes (use \\" to
        escape quotes). Otherwise, expr should follow sympy conventions.
    data : object, default None
        object where data should be retrieve from. If data is None, then
        select returns the Selector class instead of the selected data.
    get: function(key, data), default toolz.get
        Function that retrieves data from some object based on the key.
        Default is toolz.get(key, data), which is equivalent to data[key]
    custom_funcs: dict {string : function}, default ()
        Mapping between function name in expr and the actual function to be
        evaluated. Default means there are no custom functions.

    Note that custom_functions can also be registered in the global
    custom_funcs variable.

    Returns
    -------
    selected : Selector or object
        if data is None, then returns Selector object for expr. Otherwise,
        return the selected data

    Examples
    -------
    >>> import numpy as np
    >>> data = {"Sepal Length": np.array([1, 2, 3, 4, 5]),
    ...         'weird""name': np.array([4, 5, 6, 7, 8])}

    >>> select('2 ** "Sepal Length" + "weird\\"\\"name', data)
        array([  6.,   9.,  14.,  23.,  40.])

    >>> f = select('2 ** "Sepal Length" + "weird\\"\\"name')
    >>> f(data)
        array([  6.,   9.,  14.,  23.,  40.])

    >>> select('"weird  name"', get=lambda v, d: d[x.replace(" ", '"')])
        array([4, 5, 6, 7, 8])

    >>> @register("mean")
    ... def mean(xs):
    ...     return sum(x) / len(x)
    >>> select('mean("Sepal Length")', data)
        3

    >>> func = lambda x : 3 * x
    >>> select('triple("Sepal Length")', data, custom_funcs={"triple": func}])
        array([  3.,   6.,  9.,  12.,  15.])
    """
    expr, symbols = parse(expr)
    # parse returns symbols as the reverse mapping that Selector wants
    symbols = {v: k for k, v in symbols.iteritems()}
    s = Selector(expr, symbols, custom_funcs=custom_funcs, get=get)

    if data is None:
        return s
    else:
        return s(data)
