class InputCell:
    def __init__(self, initial_value):
        self._value = initial_value
        self.dependents = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        old = self._value
        self._value = new_value
        # Only propagate if value actually changed
        if old != new_value:
            self._propagate()

    def _propagate(self):
        # Collect affected compute cells reachable from this input
        affected = set()
        stack = list(getattr(self, "dependents", []))
        while stack:
            node = stack.pop()
            if node in affected:
                continue
            affected.add(node)
            for dep in getattr(node, "dependents", []):
                stack.append(dep)

        if not affected:
            return

        # Compute indegrees within affected subgraph: number of inputs that are compute cells in affected
        indegree = {}
        for node in affected:
            cnt = 0
            for inp in node.inputs:
                if inp in affected:
                    cnt += 1
            indegree[node] = cnt

        # Kahn's algorithm for topological sort
        queue = [n for n, d in indegree.items() if d == 0]
        order = []
        while queue:
            n = queue.pop(0)
            order.append(n)
            for dep in getattr(n, "dependents", []):
                if dep in indegree:
                    indegree[dep] -= 1
                    if indegree[dep] == 0:
                        queue.append(dep)

        # Recompute values in topological order
        changed = []
        for cell in order:
            inputs_values = [inp.value for inp in cell.inputs]
            new_val = cell.compute_function(inputs_values)
            old_val = cell._value
            cell._value = new_val
            if new_val != old_val:
                changed.append(cell)

        # Call callbacks for cells whose value changed
        for cell in changed:
            for cb in list(cell.callbacks):
                try:
                    cb(cell._value)
                except Exception:
                    pass


class ComputeCell:
    def __init__(self, inputs, compute_function):
        self.inputs = list(inputs)
        self.compute_function = compute_function
        self.dependents = []
        self.callbacks = []

        # Register self as dependent on inputs
        for inp in self.inputs:
            if not hasattr(inp, "dependents"):
                inp.dependents = []
            inp.dependents.append(self)

        # Compute initial value
        self._value = self.compute_function([inp.value for inp in self.inputs])

    @property
    def value(self):
        return self._value

    def add_callback(self, callback):
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def remove_callback(self, callback):
        try:
            while callback in self.callbacks:
                self.callbacks.remove(callback)
        except ValueError:
            pass
