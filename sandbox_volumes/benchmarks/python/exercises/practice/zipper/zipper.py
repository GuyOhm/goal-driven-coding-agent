class Zipper:
    def __init__(self, node, path=None):
        self._node = node
        # path is a list of breadcrumbs; each breadcrumb is a tuple
        # (dir, parent_value, other_subtree)
        # dir is 'left' meaning current node was parent's left child
        # or 'right' meaning current node was parent's right child
        self._path = list(path) if path else []

    @staticmethod
    def from_tree(tree):
        return Zipper(tree, [])

    def value(self):
        return None if self._node is None else self._node.get("value")

    def set_value(self, val):
        if self._node is None:
            return None
        node = {"value": val, "left": self._node.get("left"), "right": self._node.get("right")}
        return Zipper(node, self._path)

    def left(self):
        if self._node is None:
            return None
        left = self._node.get("left")
        if left is None:
            return None
        # breadcrumb: came from parent's left, store parent value and right subtree
        bc = ("left", self._node.get("value"), self._node.get("right"))
        return Zipper(left, self._path + [bc])

    def set_left(self, subtree):
        if self._node is None:
            return None
        node = {"value": self._node.get("value"), "left": subtree, "right": self._node.get("right")}
        return Zipper(node, self._path)

    def right(self):
        if self._node is None:
            return None
        right = self._node.get("right")
        if right is None:
            return None
        bc = ("right", self._node.get("value"), self._node.get("left"))
        return Zipper(right, self._path + [bc])

    def set_right(self, subtree):
        if self._node is None:
            return None
        node = {"value": self._node.get("value"), "left": self._node.get("left"), "right": subtree}
        return Zipper(node, self._path)

    def up(self):
        if not self._path:
            return None
        bc = self._path[-1]
        rest = self._path[:-1]
        dir, parent_value, other = bc
        if dir == "left":
            parent = {"value": parent_value, "left": self._node, "right": other}
        else:
            parent = {"value": parent_value, "left": other, "right": self._node}
        return Zipper(parent, rest)

    def to_tree(self):
        node = self._node
        path = list(self._path)
        while path:
            dir, parent_value, other = path[-1]
            path = path[:-1]
            if dir == "left":
                node = {"value": parent_value, "left": node, "right": other}
            else:
                node = {"value": parent_value, "left": other, "right": node}
        return node
