def recite(start, take=1):
    """Return the verses of the Ten Green Bottles song.

    start: starting number of bottles (int)
    take: number of consecutive verses to return (int)
    Returns a list of strings, with blank lines between verses when take>1.
    """
    num_words = {
        0: "no",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
    }

    def cap(n):
        return num_words[n].capitalize()

    def lower(n):
        return num_words[n]

    verses = []
    for i in range(take):
        n = start - i
        next_n = n - 1

        # first two identical lines (but singular/plural for bottle)
        first_num = cap(n)
        bottle_word = "bottle" if n == 1 else "bottles"
        verses.append(f"{first_num} green {bottle_word} hanging on the wall,")
        verses.append(f"{first_num} green {bottle_word} hanging on the wall,")

        # third fixed line
        verses.append("And if one green bottle should accidentally fall,")

        # fourth line depends on next_n
        if next_n == 0:
            verses.append("There'll be no green bottles hanging on the wall.")
        else:
            next_num = lower(next_n)
            next_bottle = "bottle" if next_n == 1 else "bottles"
            verses.append(f"There'll be {next_num} green {next_bottle} hanging on the wall.")

        # add blank line between verses except after last
        if i != take - 1:
            verses.append("")

    return verses
