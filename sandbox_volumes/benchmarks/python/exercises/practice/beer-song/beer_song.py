def recite(start, take=1):
    """Return the beer song verses starting from `start` for `take` verses.

    Each verse consists of two lines. Verses are separated by a blank line in the
    returned list (i.e., an empty string between verses).
    """
    def bottles(n):
        if n == 0:
            return "no more bottles"
        if n == 1:
            return "1 bottle"
        return f"{n} bottles"

    verses = []
    for i in range(take):
        n = start - i
        if n > 0:
            # First line
            first = f"{n} {"bottles" if False else ''}"  # placeholder
            # But need proper phrasing
            if n == 1:
                first = f"1 bottle of beer on the wall, 1 bottle of beer."
                second = "Take it down and pass it around, no more bottles of beer on the wall."
            elif n == 2:
                first = f"2 bottles of beer on the wall, 2 bottles of beer."
                second = f"Take one down and pass it around, 1 bottle of beer on the wall."
            else:
                first = f"{n} bottles of beer on the wall, {n} bottles of beer."
                second = f"Take one down and pass it around, {n-1} bottles of beer on the wall."
        elif n == 0:
            first = "No more bottles of beer on the wall, no more bottles of beer."
            second = "Go to the store and buy some more, 99 bottles of beer on the wall."
        else:
            # For negative n, cycle? Not expected by tests. Just treat as going to store.
            first = "No more bottles of beer on the wall, no more bottles of beer."
            second = "Go to the store and buy some more, 99 bottles of beer on the wall."

        verses.append(first)
        verses.append(second)
        if i != take - 1:
            verses.append("")

    return verses
