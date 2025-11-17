class Record:
    def __init__(self, record_id, parent_id):
        self.record_id = record_id
        self.parent_id = parent_id


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.children = []


def BuildTree(records):
    # Empty input
    if not records:
        return None

    # Sort records by record_id
    records.sort(key=lambda r: r.record_id)

    # Validate ids are continuous from 0..n-1 and unique
    for index, record in enumerate(records):
        if record.record_id != index:
            raise ValueError("Record id is invalid or out of order.")

    # Validate parent relationships and build nodes
    nodes = [Node(i) for i in range(len(records))]

    for record in records:
        if record.record_id == record.parent_id:
            # Only root (id 0) is allowed to have equal parent_id
            if record.record_id != 0:
                raise ValueError("Only root should have equal record and parent id.")
        if record.parent_id > record.record_id:
            raise ValueError("Node parent_id should be smaller than it's record_id.")

        if record.record_id != 0:
            parent = nodes[record.parent_id]
            parent.children.append(nodes[record.record_id])

    return nodes[0]
