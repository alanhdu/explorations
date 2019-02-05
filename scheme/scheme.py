"""A small live-coded Scheme.

Because this was live-coded, it has a number of flaws (mostly related to
sloppy handling of scope (e.g. all variables are global)) and many
missing parts (e.g. no macros, no unquote, etc).
"""


def lex(ss):
    current = ""
    for char in ss:
        if char in "()":
            if current:
                yield current
            current = ""
            yield char
        elif char in " \t\n":
            if current:
                yield current
            current = ""
        else:
            current += char
    if current:
        yield current


def parse(tokens):
    output = []
    level = 0

    def get(output, level):
        x = output
        for i in range(level):
            x = x[-1]
        return x

    for token in tokens:
        if token == "(":
            get(output, level).append([])
            level += 1
        elif token == ")":
            level -= 1
        else:
            get(output, level).append(token)
    return output[0]


class Context:
    def __init__(self):
        self.frames = []
        self.globals = {}
        self.funcs = {}

    def run(self, s):
        return self.eval(parse(lex(s)))

    def get_var(self, name):
        for frame in self.frames:
            if name in frame:
                return frame[name]
        return self.globals[name]

    def eval(self, expr):
        if not isinstance(expr, list):
            try:
                return int(expr)
            except ValueError:
                return self.get_var(expr)

        head = expr[0]
        tail = expr[1:]

        if head == "quasiquote":
            assert len(tail) == 1
            return tail[0]
        elif head in {"car", "cdr"}:
            assert len(tail) == 1
            xs = self.eval(tail[0])
            assert isinstance(xs, list)

            if head == "car":
                return xs[0]
            else:
                return xs[1:]
        elif head == "+":
            numbers = [int(self.eval(t)) for t in tail]
            return sum(numbers)
        elif head == "define":
            if not isinstance(tail[0], list):
                # Defining a variable
                name, value = tail
                self.globals[name] = self.eval(value)
                return

            # Defining a function
            defun, body = tail
            name, args = defun[0], defun[1:]

            self.funcs[name] = (args, body)
        else:
            # This must be a user-defined function
            args, body = self.funcs[head]
            values = [self.eval(t) for t in tail]
            assert len(values) == len(args)

            self.frames.insert(
                0, {key: value for key, value in zip(args, values)}
            )
            output = self.eval(body)
            self.frames = self.frames[1:]
            return output


ctx = Context()
ctx.run("(define (cadr x) (car (cdr x)))")
