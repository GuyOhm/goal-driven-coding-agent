def proverb(*pieces, qualifier=None):
    """Generate the proverb lines from given pieces.

    Args:
        *pieces: arbitrary number of string pieces representing the chain.
        qualifier: optional string to prepend to the first piece in the final line.

    Returns:
        list of proverb lines (strings).
    """
    # If no pieces, return empty list
    if not pieces:
        return []

    lines = []
    # For each adjacent pair, create the consequence line
    for first, second in zip(pieces, pieces[1:]):
        lines.append(f"For want of a {first} the {second} was lost.")

    # Final line uses the first piece with optional qualifier
    first_piece = pieces[0]
    if qualifier:
        final_subject = f"{qualifier} {first_piece}"
    else:
        final_subject = first_piece

    lines.append(f"And all for the want of a {final_subject}.")
    return lines
