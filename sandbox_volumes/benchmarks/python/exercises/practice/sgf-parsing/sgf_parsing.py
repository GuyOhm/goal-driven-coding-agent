class SgfTree:
    def __init__(self, properties=None, children=None):
        self.properties = properties or {}
        self.children = children or []

    def __eq__(self, other):
        if not isinstance(other, SgfTree):
            return False
        for key, value in self.properties.items():
            if key not in other.properties:
                return False
            if other.properties[key] != value:
                return False
        for key in other.properties.keys():
            if key not in self.properties:
                return False
        if len(self.children) != len(other.children):
            return False
        for child, other_child in zip(self.children, other.children):
            if child != other_child:
                return False
        return True

    def __ne__(self, other):
        return not self == other


def parse(input_string):
    # simple recursive descent parser
    s = input_string
    n = len(s)
    i = 0

    def peek():
        return s[i] if i < n else None

    def consume():
        nonlocal i
        if i < n:
            ch = s[i]
            i += 1
            return ch
        return None

    def parse_value():
        # assumes starting just after '['
        val = []
        while True:
            ch = consume()
            if ch is None:
                # unterminated
                break
            if ch == ']':
                break
            if ch == '\\':
                nxt = peek()
                if nxt is None:
                    # dangling backslash, ignore
                    break
                c = consume()
                # if newline after backslash -> removed
                if c == '\n':
                    # skip (remove)
                    continue
                # whitespace other than newline -> converted to space
                if c.isspace() and c != '\n':
                    val.append(' ')
                else:
                    val.append(c)
            else:
                # normal char
                if ch == '\n':
                    val.append('\n')
                elif ch.isspace():
                    # whitespace other than newline -> space
                    val.append(' ')
                else:
                    val.append(ch)
        return ''.join(val)

    def parse_property_list():
        props = {}
        # property list: zero or more properties (key + one or more values)
        while True:
            # if next char uppercase letter starting key
            ch = peek()
            if ch is None:
                break
            if ch == ';' or ch == '(' or ch == ')' :
                break
            # expect key letters
            if not ch.isalpha():
                break
            # read key
            key_chars = []
            while True:
                ch = peek()
                if ch is None or not ch.isalpha():
                    break
                key_chars.append(consume())
            if not key_chars:
                break
            key = ''.join(key_chars)
            # key must be uppercase only
            if not key.isupper():
                raise ValueError("property must be in uppercase")
            # next should be '[' for values
            if peek() != '[':
                raise ValueError("properties without delimiter")
            values = []
            while peek() == '[':
                consume()  # consume '['
                v = parse_value()
                values.append(v)
            # store
            props.setdefault(key, [])
            props[key].extend(values)
        return props

    def parse_node():
        # expects ';' consumed before calling? We'll handle here
        nonlocal i
        if peek() != ';':
            return None
        consume()  # ';'
        props = parse_property_list()
        node = SgfTree(properties=props)
        # after properties, there may be child trees (variations) starting with '('
        children = []
        while peek() == '(':
            child = parse_tree()
            children.append(child)
        node.children = children
        return node

    def parse_tree():
        nonlocal i
        # expect '('
        if peek() != '(':
            raise ValueError("tree missing")
        consume()
        # if immediate ')' -> empty tree with no nodes
        if peek() == ')':
            consume()
            raise ValueError("tree with no nodes")
        # Now expect at least one node starting with ';'
        if peek() != ';':
            # e.g., input like "(" then something else
            raise ValueError("tree missing")
        # parse first node
        root_node = parse_node()
        if root_node is None:
            # no node parsed
            raise ValueError("tree with no nodes")
        last = root_node
        # parse subsequent nodes separated by ';' as linear chain
        while peek() == ';':
            nxt = parse_node()
            # attach nxt as single child of last
            last.children = [nxt]
            last = nxt
        # after nodes, expect closing ')'
        if peek() != ')':
            # maybe missing closing
            raise ValueError("tree missing")
        consume()  # consume ')'
        return root_node

    # top-level
    # input must start with '('
    if n == 0:
        raise ValueError("tree missing")
    if peek() != '(':
        raise ValueError("tree missing")
    tree = parse_tree()
    # after parsing tree, there should be no extra characters (or just whitespace?)
    # We'll ignore trailing whitespace
    # skip any whitespace
    while i < n:
        if s[i].isspace():
            i += 1
            continue
        # if there are extra characters, consider malformed
        raise ValueError("tree missing")
    return tree
