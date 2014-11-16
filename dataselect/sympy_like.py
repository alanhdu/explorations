varname = re.compile(r'"((?:\\"|[^"])*)"')

class Expr(object):
    __slots__ = ["expr", "names"]
    def __init__(self, expr):
        # Find and replace variable names w/ xi
        self.names = {"x{subscript}".format(subscript=i): name
                      for i, name in enumerate(set(varname.findall(expr)))}
        for name, var in self.names.iteritems():
            expr = expr.replace('"{var}"'.format(var=var), name)

        print str(parse_expr(expr))
        self.expr = _Expr(parse_expr(expr))

    def __str__(self):
        return str(self.names) + ": " + str(self.expr)
    def __repr__(self):
        return repr(self.names) + ": " + repr(self.expr)

class _Expr(object):
    __slots__ = ["head", "args"]
    def __init__(self, expr):
        print expr
        self.head = expr.func
        self.args = tuple(_Expr(arg) for arg in expr.args)
    def __str__(self):
        if self.args:
            return str(self.head) + str(self.args)
        else:
            return str(self.head)
    def __repr__(self):
        return repr(self.head) + repr(self.args)
    def __call__(self, data):
        pass
