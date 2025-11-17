from collections import deque


def measure(bucket_one, bucket_two, goal, start_bucket):
    # Validate inputs
    if goal > max(bucket_one, bucket_two):
        raise ValueError("Goal can't be larger than both buckets")

    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a

    if goal % gcd(bucket_one, bucket_two) != 0:
        raise ValueError("Goal is not achievable with given bucket sizes")

    if start_bucket not in ("one", "two"):
        raise ValueError("start_bucket must be 'one' or 'two'")

    # Initial state: first action is to fill the starting bucket
    if start_bucket == "one":
        init = (bucket_one, 0)
    else:
        init = (0, bucket_two)

    # Check immediate goal
    if init[0] == goal:
        return 1, "one", init[1]
    if init[1] == goal:
        return 1, "two", init[0]

    # BFS
    q = deque()
    q.append((init, 1))
    visited = set()
    visited.add(init)

    while q:
        (x, y), moves = q.popleft()

        # generate possible actions
        next_states = []
        # fill bucket one
        next_states.append((bucket_one, y))
        # fill bucket two
        next_states.append((x, bucket_two))
        # empty bucket one
        next_states.append((0, y))
        # empty bucket two
        next_states.append((x, 0))
        # pour one -> two
        transfer = min(x, bucket_two - y)
        next_states.append((x - transfer, y + transfer))
        # pour two -> one
        transfer = min(y, bucket_one - x)
        next_states.append((x + transfer, y - transfer))

        for nx, ny in next_states:
            # enforce forbidden state: starting bucket empty and other bucket full
            if start_bucket == "one":
                if nx == 0 and ny == bucket_two:
                    continue
            else:
                if ny == 0 and nx == bucket_one:
                    continue

            if (nx, ny) in visited:
                continue

            # check goal
            if nx == goal:
                return moves + 1, "one", ny
            if ny == goal:
                return moves + 1, "two", nx

            visited.add((nx, ny))
            q.append(((nx, ny), moves + 1))

    # If BFS exhausted, impossible
    raise ValueError("Goal is not achievable")
