from collections import deque
from functools import reduce


class State(dict):
    _count = 0
    def __init__(self, done=False):
        self._id = State._count
        State._count += 1
        self.done = done
    def __getitem__(self, key):
        if key not in self:
            self[key] = set()
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
        return "{hash} {dict} {done}".format(hash=hash(self), dict=d, 
                                             done=self.done)

class DFSA():

    def __init__(self, fsm):
        fsm.remove()
        fsm.clean()

        self.nstates = list(fsm.states)
        self.size = 2 ** len(self.nstates)
        self.states, self.done = {}, {}
        
        states = fsm.descend({fsm.begin})
        self.begin = self.toIndex(states)

        stack = deque([states])
        visited = set()

        while stack:
            states = stack.pop()
            index = self.toIndex(states)
            if index not in visited:
                self.done[index] = any(state.done for state in states)
                visited.add(index)
                self.states[index] = {}
                for key in self._getKeys(states):
                    new = reduce(set.union, (s[key] for s in states), set())
                    stack.append(new)
                    if new:
                        self.states[index][key] = self.toIndex(new)
    def match(self, s):
        try:
            state = self.begin
            for char in s:
                state = self.states[state][char]
            return True
        except KeyError:
            return False

    def toIndex(self, states):
        bits = [i for i, s in enumerate(self.nstates) if s in states]
        bitstring = "".join("1" if bit in bits else "0"
                            for bit in range(self.size))
        return int(bitstring, 2)
    def _getKeys(self, states):
        return reduce(set.union, (set(s) for s in states), set())


class FSM():
    def __init__(self):
        self.begin = State()
        self.done = State()
        self.states = {self.begin, self.done}
    def new(self):
        new = State()
        self.states.add(new)
        return new
    def match(self, s):
        states = {self.begin}
        for char in s:
            states = reduce(set.union, (state[char] for state in states), 
                            set())
            if not states:
                break
        return any(state.done for state in states)
    def remove(self):
        """ Remove empty transitions """
        for state in self.states:
            for key in frozenset(state):
                if key is None:
                    toVisit = self.descend(state[key])
                    for other in frozenset(toVisit):
                        for k, value in other.items():
                            state[k].update(value)
                    if self.done in toVisit:
                        state.done = True
                    del state[None]
                else:
                    new = self._descendOneLevel(state[key])
                    while any(x not in state[key] for x in new):
                        new = self._descendOneLevel(state[key])
                        del state[key]
                        state[key] = new
        self.done.done = True
    def clean(self):
        """ Remove unused states """
        visited = set()
        toVisit = deque([self.begin])
        while toVisit:
            state = toVisit.pop()
            if state not in visited:
                toVisit.extend(v for value in state.values() 
                                 for v in value)
            visited.add(state)
        for state in frozenset(self.states):
            if state not in visited:
                self.states.remove(state)
                del state
    def _descendOneLevel(self, states):
        return reduce(set.union, (state[None] for state in states), set())

    def descend(self, states):
        none = self._descendOneLevel(states)
        while any(x not in states for x in none) and none:
            states |= none
            none = self._descendOneLevel(states)
        return states


def Concat(r1, r2):
    r1.done[None].add(r2.begin)
    r1.states |= r2.states
    r1.done = r2.done
    return r1
def Branch(r1, r2):
    f = FSM()
    f.begin[None].add(r1.begin)
    f.begin[None].add(r2.begin)
    r1.done[None].add(f.done)
    r2.done[None].add(f.done)
    f.states |= r1.states
    f.states |= r2.states
    return f

def Repeat(r1):
    r1.done[None].add(r1.begin)
    r1.begin[None].add(r1.done)
    return r1

def Basic(r1):
    f = FSM()
    f.begin[r1].add(f.done)
    return f


class Regex(object):
    """Dummy Class for pretty print testing"""
    def __init__(self, t, r1, r2=None):
        self.t = t
        self.r1 = r1
        self.r2 = r2
    def __str__(self):
        if self.t is None:
            return self.r1
        elif self.r2 is None:
            return "({} {})".format(self.t, self.r1)
        else:
            return "({} {} {})".format(self.t, self.r1, self.r2)
    def __repr__(self):
        return str(self)

def findClose(s):
    level = 0
    for i, char in enumerate(s):
        if char == ')':
            if level == 1:
                return i
            else:
                level -= 1
        elif char == '(':
            level += 1


def parse(s, regexs=None):
    fold = False
    if regexs is None:
        regexs = deque()
        fold = True
    if s:
        if s[0] == "*":
            regexs[-1] = Repeat(regexs[-1])
            parse(s[1:], regexs)
        elif s[0] == "|":
            other = deque()
            parse(s[1:], other)

            regexs[-1] = Branch(regexs[-1], other.popleft())
            regexs.extend(other)
        elif s[0] == "(":
            # skip closing paren, so add one
            nxt, rest = s[1:findClose(s)], s[findClose(s) + 1:]
            regexs.append(parse(nxt))
            parse(rest, regexs)
        else:
            regexs.append(Basic(s[0]))
            parse(s[1:], regexs)
        if fold:
            f = reduce(Concat, regexs)
            f.remove()
            f.clean()
            return f
def compile(pattern):
    return DFSA(parse(pattern))
