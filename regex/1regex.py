from collections import deque, defaultdict
from functools import reduce

pattern = "abc*"

class State(dict):
    _count = 0
    def __init__(self, done=False):
        self._id = State._count
        self.done = done
        State._count += 1
    def __getitem__(self, key):
        if key not in self:
            self[key] = set()
        if None not in self:
            self[None]  = set()

        return dict.__getitem__(self, key)
    def __hash__(self):
        return self._id
    def __eq__(self, other):
        return id(self) == id(other)
    def __str__(self):
        return repr(self)
    def __repr__(self):
        d = {key: ", ".join(str(hash(v)) for v in value)
             for key, value in self.items() if value}
        return "{hash} {dict}".format(hash=hash(self), dict=d)

class FSM():
    def __init__(self, begin):
        self.begin = begin
        self.done = State()
        self.states = {self.begin, self.done}
    def merge(self, other):
        self.states |= other.states
        self.done = other.done
    def new(self):
        new = State()
        self.states.add(new)
        return new
    def clean(self):
        visited = set()
        toVisit = deque()
        toVisit.append(self.begin)

        while toVisit:
            state = toVisit.pop()
            if state not in visited:
                toVisit.extend(v for value in state.values() 
                                 for v in value)
                for key, value in state.items():
                    for v in value:
                        toVisit.append(v)
            visited.add(state)
        for state in frozenset(self.states):
            if state not in visited:
                self.states.remove(state)
                del state
    def remove(self):
        """ Remove empty transitions (represented as None)"""
        for state in self.states:
            # treat begin specially because nothing points to it
            if (state is self.begin and len(state) == 1 and None in state and
                    len(state[None]) == 1):
                t = state[None].pop()
                del state
                self.begin = t
            elif None in state:
                toVisit = self.descend({state})
                for other in frozenset(toVisit):
                    for key, value in other.items():
                        for v in value:
                            toVisit.add(v)
                            state[key].add(v)

                if self.done in state[None]:
                    state.done = True
                del state[None]
        self.done.done=True
        self.clean()
    def descend(self, states):
        none = reduce(set.union, (state[None] for state in states), set())
        while any(x not in states for x in none) and none:
            states |= none
            none = reduce(set.union, (state[None] for state in states), set())
        return states
    def match(self, s):
        states = {self.begin}
        for char in s:
            states = reduce(set.union, (state[char] for state in states), set())
            if not states:
                break
        return any(state.done for state in states)


def compile(pattern):
    root = FSM(State())
    root.begin[None].add(root.done)
    stack = deque()
    stack.append(root)
    old = stack[-1]

    pipe = False
    for char in pattern:
        if char == "+":
            # all transitions that go out of the old FSM
            t = old.done
            old.done = old.new()
            t[None].add(old.begin)
            t[None].add(old.done)
        elif char == "*":
            for state in old.states:
                for key, value in state.items():
                    if old.done in value:
                        state[key].remove(old.done)
                        state[key].add(old.begin)
                        state[None].add(old.done)
            old.begin[None].add(old.done)
        elif char == "|":
            pipe = True
        elif char == "(":
            stack.append(FSM(old.done))
        elif char == ")":
            old = stack.pop()
        else:
            if not pipe:
                fsm = FSM(old.done)
                fsm.begin[char].add(fsm.done)
                old = fsm 
            else:
                old.begin[char].add(old.done)

        stack[-1].merge(old)
    root.remove()
    return root

p = compile(r"(a|b)*")
print(p.match("bababababababac"))
