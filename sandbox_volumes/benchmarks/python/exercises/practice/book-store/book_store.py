from functools import lru_cache
from itertools import combinations


def total(basket):
    """Calculate lowest possible price in cents for the given basket.
    basket: list of ints representing book titles (1..5)
    Price unit is cents: 800 per book.
    """
    if not basket:
        return 0
    # counts for 5 titles (indexes 0..4)
    counts = [0] * 5
    for b in basket:
        if 1 <= b <= 5:
            counts[b - 1] += 1
        else:
            # ignore invalid? but per problem only 1..5 will appear
            pass

    # Precompute price for group sizes in cents
    PRICE_PER_BOOK = 800
    DISCOUNTS = {1: 0, 2: 5, 3: 10, 4: 20, 5: 25}
    price_group = {k: (PRICE_PER_BOOK * k * (100 - DISCOUNTS[k]) // 100) for k in DISCOUNTS}

    @lru_cache(None)
    def dfs(counts_tuple):
        # counts_tuple is length 5
        if all(c == 0 for c in counts_tuple):
            return 0
        best = float('inf')
        # indices with available books
        available = [i for i, c in enumerate(counts_tuple) if c > 0]
        n_avail = len(available)
        # Try all possible non-empty subsets of available indices
        # There are at most 31 subsets so fine
        for r in range(1, n_avail + 1):
            for combo in combinations(available, r):
                new_counts = list(counts_tuple)
                for idx in combo:
                    new_counts[idx] -= 1
                new_tuple = tuple(new_counts)
                cost = price_group[r] + dfs(new_tuple)
                if cost < best:
                    best = cost
        return best

    return dfs(tuple(counts))
