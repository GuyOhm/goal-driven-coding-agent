from collections import Counter

RANKS = {str(i): i for i in range(2, 11)}
RANKS.update({"J": 11, "Q": 12, "K": 13, "A": 14})

# category values
HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIR = 2
THREE = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR = 7
STRAIGHT_FLUSH = 8


def _parse(hand):
    cards = hand.split()
    ranks = []
    suits = []
    for c in cards:
        rank = c[:-1]
        suit = c[-1]
        ranks.append(RANKS[rank])
        suits.append(suit)
    return ranks, suits


def _is_straight(ranks):
    # ranks: list of ints, may contain duplicates though valid hands won't
    unique = sorted(set(ranks))
    if len(unique) != 5:
        return False, None
    sorted_ranks = sorted(unique)
    # normal straight
    if sorted_ranks[-1] - sorted_ranks[0] == 4:
        return True, sorted_ranks[-1]
    # wheel: A-2-3-4-5 (14,2,3,4,5) -> treat as 5-high straight
    if sorted_ranks == [2, 3, 4, 5, 14]:
        return True, 5
    return False, None


def _hand_rank(hand):
    ranks, suits = _parse(hand)
    counts = Counter(ranks)
    counts_by_rank = sorted(((cnt, rank) for rank, cnt in counts.items()), reverse=True)
    # counts_by_rank sorted by count desc then rank desc? need tie-breakers; we'll sort accordingly
    # Build helper structures
    ranks_sorted_desc = sorted(ranks, reverse=True)
    is_flush = len(set(suits)) == 1
    is_straight, straight_high = _is_straight(ranks)

    if is_straight and is_flush:
        return (STRAIGHT_FLUSH, (straight_high,))

    # four of a kind
    if 4 in counts.values():
        quad = max(rank for rank, cnt in counts.items() if cnt == 4)
        kicker = max(rank for rank, cnt in counts.items() if cnt != 4)
        return (FOUR, (quad, kicker))

    # full house
    if sorted(counts.values()) == [2, 3]:
        trip = max(rank for rank, cnt in counts.items() if cnt == 3)
        pair = max(rank for rank, cnt in counts.items() if cnt == 2)
        return (FULL_HOUSE, (trip, pair))

    if is_flush:
        return (FLUSH, tuple(sorted(ranks, reverse=True)))

    if is_straight:
        return (STRAIGHT, (straight_high,))

    if 3 in counts.values():
        trip = max(rank for rank, cnt in counts.items() if cnt == 3)
        kickers = sorted((rank for rank, cnt in counts.items() if cnt == 1), reverse=True)
        return (THREE, (trip, *kickers))

    # two pairs
    if list(counts.values()).count(2) == 2:
        pairs = sorted((rank for rank, cnt in counts.items() if cnt == 2), reverse=True)
        kicker = max(rank for rank, cnt in counts.items() if cnt == 1)
        return (TWO_PAIR, (*pairs, kicker))

    # one pair
    if 2 in counts.values():
        pair = max(rank for rank, cnt in counts.items() if cnt == 2)
        kickers = sorted((rank for rank, cnt in counts.items() if cnt == 1), reverse=True)
        return (ONE_PAIR, (pair, *kickers))

    # high card
    return (HIGH_CARD, tuple(sorted(ranks, reverse=True)))


def best_hands(hands):
    if not hands:
        return []
    scored = [(hand, _hand_rank(hand)) for hand in hands]
    # find max score lexicographically
    best_score = max(score for _, score in scored)
    winners = [hand for hand, score in scored if score == best_score]
    return winners
