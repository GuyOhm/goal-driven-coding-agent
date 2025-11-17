class EmptyListException(Exception):
    pass


class Node:
    def __init__(self, value):
        self._value = value
        self._next = None

    def value(self):
        return self._value

    def next(self):
        return self._next


class LinkedList:
    def __init__(self, values=None):
        self._head = None
        self._length = 0
        if values is not None:
            for v in values:
                # pushing each value so that the last value becomes the head
                self.push(v)

    def __iter__(self):
        current = self._head
        while current is not None:
            yield current.value()
            current = current.next()

    def __len__(self):
        return self._length

    def head(self):
        if self._head is None:
            raise EmptyListException("The list is empty.")
        return self._head

    def push(self, value):
        node = Node(value)
        node._next = self._head
        self._head = node
        self._length += 1

    def pop(self):
        if self._head is None:
            raise EmptyListException("The list is empty.")
        node = self._head
        self._head = node.next()
        self._length -= 1
        return node.value()

    def reversed(self):
        new = LinkedList()
        for v in self:
            new.push(v)
        return new
