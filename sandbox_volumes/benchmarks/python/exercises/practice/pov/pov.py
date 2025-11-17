from json import dumps


class Tree:
    def __init__(self, label, children=None):
        self.label = label
        self.children = children if children is not None else []

    def __dict__(self):
        return {self.label: [c.__dict__() for c in sorted(self.children)]}

    def __str__(self, indent=None):
        return dumps(self.__dict__(), indent=indent)

    def __lt__(self, other):
        return self.label < other.label

    def __eq__(self, other):
        return self.__dict__() == other.__dict__()

    def _find_path_nodes(self, target):
        """Return list of nodes from self (root) to the node with label == target, or None."""
        if self.label == target:
            return [self]
        for child in self.children:
            sub = child._find_path_nodes(target)
            if sub is not None:
                return [self] + sub
        return None

    def _clone_subtree(self, node, exclude=None):
        """Deep copy of node, excluding the child `exclude` (by identity) if provided."""
        children = []
        for c in node.children:
            if exclude is not None and c is exclude:
                continue
            children.append(self._clone_subtree(c, None))
        return Tree(node.label, children)

    def from_pov(self, from_node):
        path = self._find_path_nodes(from_node)
        if path is None:
            raise ValueError("Tree could not be reoriented")
        # Start with a clone of the target subtree
        new_root = self._clone_subtree(path[-1], None)
        # Walk up the path, reattaching siblings and parent nodes
        # path: [root, ..., target]
        for i in range(len(path) - 2, -1, -1):
            curr = path[i]
            child_to_exclude = path[i + 1]
            # clone curr excluding the child that leads to target
            cloned = self._clone_subtree(curr, exclude=child_to_exclude)
            # attach previously built new_root as a child
            cloned.children.append(new_root)
            new_root = cloned
        return new_root

    def path_to(self, from_node, to_node):
        # find source path
        path_from = self._find_path_nodes(from_node)
        if path_from is None:
            raise ValueError("Tree could not be reoriented")
        path_to = self._find_path_nodes(to_node)
        if path_to is None:
            raise ValueError("No path found")
        # find last common ancestor index
        i = 0
        while i < len(path_from) and i < len(path_to) and path_from[i] is path_to[i]:
            i += 1
        lca_idx = i - 1
        # build path: from_node up to LCA, then down to to_node
        up_segment = [n.label for n in path_from[lca_idx + 1 :]][::-1]
        result = up_segment + [path_from[lca_idx].label] + [n.label for n in path_to[lca_idx + 1 :]]
        return result
