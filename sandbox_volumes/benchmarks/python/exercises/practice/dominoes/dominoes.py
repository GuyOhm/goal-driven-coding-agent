def can_chain(dominoes):
    """Return a chain (list of oriented domino tuples) using all dominoes exactly once
    forming a cycle where adjacent halves match and first left equals last right.
    Return None if impossible. Empty input -> []
    """
    if dominoes is None:
        return None
    if len(dominoes) == 0:
        return []

    # Build edges and adjacency for an undirected multigraph
    edges = list(dominoes)  # preserve original orientation for reference
    n = len(edges)
    adj = {}  # node -> list of (neighbor, edge_id)
    degree = {}
    for i, (a, b) in enumerate(edges):
        adj.setdefault(a, []).append((b, i))
        adj.setdefault(b, []).append((a, i))
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1

    # All vertices with nonzero degree must have even degree
    for v, deg in degree.items():
        if deg % 2 != 0:
            return None

    # Connectivity: consider only vertices with degree>0
    # Do DFS from any vertex with degree>0
    start = next(iter(degree))
    visited = set()
    stack = [start]
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for (u, _) in adj.get(v, []):
            if u not in visited:
                stack.append(u)
    if set(degree.keys()) != visited:
        return None

    # Hierholzer's algorithm to find Eulerian circuit
    used = [False] * n
    # pointer per vertex to skip used edges quickly
    pointers = {v: 0 for v in adj}

    circuit_edges = []  # will hold edge_ids in order
    # stack of (vertex, incoming_edge_id)
    st = [(start, None)]
    while st:
        v, in_e = st[-1]
        ptr = pointers[v]
        adj_list = adj.get(v, [])
        # find next unused edge
        while ptr < len(adj_list) and used[adj_list[ptr][1]]:
            ptr += 1
        pointers[v] = ptr
        if ptr < len(adj_list):
            u, e_id = adj_list[ptr]
            used[e_id] = True
            # advance pointer for v since this edge is now used
            pointers[v] += 1
            st.append((u, e_id))
        else:
            # backtrack
            st.pop()
            if in_e is not None:
                circuit_edges.append(in_e)

    # circuit_edges is in order of traversal (edges appended when backtracking), already in traversal order
    circuit_edges = list(reversed(circuit_edges))

    if len(circuit_edges) != n:
        return None

    # Reconstruct oriented dominoes starting from start vertex
    chain = []
    current = start
    for e_id in circuit_edges:
        a, b = edges[e_id]
        if a == current:
            chain.append((a, b))
            current = b
        elif b == current:
            chain.append((b, a))
            current = a
        else:
            # This should not happen if circuit is valid
            return None

    # Check that chain uses all dominoes and ends match start
    if chain and chain[0][0] != chain[-1][1]:
        return None

    return chain
