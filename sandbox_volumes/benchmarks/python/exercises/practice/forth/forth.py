class StackUnderflowError(Exception):
    pass


def evaluate(input_data):
    import re

    # helper
    def is_number(s):
        return re.fullmatch(r"-?\d+", s) is not None

    # built-in words
    def do_add(stack):
        if len(stack) < 2:
            raise StackUnderflowError("Insufficient number of items in stack")
        b = stack.pop()
        a = stack.pop()
        stack.append(a + b)

    def do_sub(stack):
        if len(stack) < 2:
            raise StackUnderflowError("Insufficient number of items in stack")
        b = stack.pop()
        a = stack.pop()
        stack.append(a - b)

    def do_mul(stack):
        if len(stack) < 2:
            raise StackUnderflowError("Insufficient number of items in stack")
        b = stack.pop()
        a = stack.pop()
        stack.append(a * b)

    def do_div(stack):
        if len(stack) < 2:
            raise StackUnderflowError("Insufficient number of items in stack")
        b = stack.pop()
        a = stack.pop()
        if b == 0:
            raise ZeroDivisionError("divide by zero")
        # integer division that truncates toward zero
        stack.append(int(a / b))

    def do_dup(stack):
        if len(stack) < 1:
            raise StackUnderflowError("Insufficient number of items in stack")
        stack.append(stack[-1])

    def do_drop(stack):
        if len(stack) < 1:
            raise StackUnderflowError("Insufficient number of items in stack")
        stack.pop()

    def do_swap(stack):
        if len(stack) < 2:
            raise StackUnderflowError("Insufficient number of items in stack")
        stack[-1], stack[-2] = stack[-2], stack[-1]

    def do_over(stack):
        if len(stack) < 2:
            raise StackUnderflowError("Insufficient number of items in stack")
        stack.append(stack[-2])

    builtins = {
        '+': do_add,
        '-': do_sub,
        '*': do_mul,
        '/': do_div,
        'dup': do_dup,
        'drop': do_drop,
        'swap': do_swap,
        'over': do_over,
    }

    # collect all tokens from input_data
    tokens = []
    for line in input_data:
        # split by whitespace
        parts = line.split()
        tokens.extend(parts)

    # user-defined words mapping: name (lowercase) -> list of tokens (lowercase or numeric strings)
    user_defs = {}

    # process tokens using stack-like tokens list (process from left to right)
    from collections import deque
    to_process = deque(tokens)
    stack = []

    while to_process:
        raw = to_process.popleft()
        token = raw.lower()

        if token == ':':
            # definition: next token is name
            if not to_process:
                # malformed, but tests won't cover
                raise ValueError("illegal operation")
            name = to_process.popleft().lower()
            # name must not be number
            if is_number(name):
                raise ValueError("illegal operation")
            # collect definition until ';'
            body = []
            while to_process:
                t = to_process.popleft()
                t_l = t.lower()
                if t_l == ';':
                    break
                # inline existing user-defined words at define-time
                if t_l in user_defs:
                    # extend with a copy
                    body.extend(user_defs[t_l])
                else:
                    body.append(t_l)
            else:
                # no terminating ; found
                raise ValueError("illegal operation")
            # store definition
            user_defs[name] = body
            continue

        # number literal
        if is_number(token):
            stack.append(int(token))
            continue

        # user-defined word
        if token in user_defs:
            # push its tokens onto front of deque in order
            # since deque extends to right, we need to add left in reverse
            # simpler: create new deque with body + remaining
            body = list(user_defs[token])
            # prepend body tokens: we want body[0] processed next -> add to left in reverse
            for t in reversed(body):
                to_process.appendleft(t)
            continue

        # built-in
        if token in builtins:
            # execute
            builtins[token](stack)
            continue

        # unknown word
        raise ValueError("undefined operation")

    return stack
