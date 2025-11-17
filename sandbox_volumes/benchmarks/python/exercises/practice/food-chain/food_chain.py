def recite(start_verse, end_verse):
    animals = [
        "fly",
        "spider",
        "bird",
        "cat",
        "dog",
        "goat",
        "cow",
        "horse",
    ]

    unique_lines = {
        1: "It wriggled and jiggled and tickled inside her.",
        2: "How absurd to swallow a bird!",
        3: "Imagine that, to swallow a cat!",
        4: "What a hog, to swallow a dog!",
        5: "Just opened her throat and swallowed a goat!",
        6: "I don't know how she swallowed a cow!",
        7: "She's dead, of course!",
    }

    result = []
    for verse in range(start_verse, end_verse + 1):
        idx = verse - 1
        # first line
        result.append(f"I know an old lady who swallowed a {animals[idx]}.")

        # horse is special: only second line and done
        if animals[idx] == "horse":
            result.append(unique_lines[idx])
        else:
            # optional unique second line
            if idx in unique_lines:
                result.append(unique_lines[idx])

            # cumulative lines for predators down to spider->fly
            # start from current animal index down to 1 (spider index)
            for j in range(idx, 0, -1):
                predator = animals[j]
                prey = animals[j - 1]
                line = f"She swallowed the {predator} to catch the {prey}"
                # when the prey is spider, include the extra phrase
                if prey == "spider":
                    line += " that wriggled and jiggled and tickled inside her"
                line += "."
                result.append(line)

            # final common line
            result.append("I don't know why she swallowed the fly. Perhaps she'll die.")

        # blank line between verses except after last
        if verse != end_verse:
            result.append("")

    return result
