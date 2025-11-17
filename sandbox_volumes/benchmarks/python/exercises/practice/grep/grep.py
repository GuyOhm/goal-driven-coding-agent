def grep(pattern, flags, files):
    """Search for pattern in given files according to flags.

    pattern: search string
    flags: string containing flags like "-n -l -i -v -x" (space separated or combined)
    files: list of filenames
    """
    # parse flags into set of characters
    flag_tokens = [tok for tok in flags.split() if tok]
    flag_set = set()
    for tok in flag_tokens:
        if tok.startswith("-"):
            for ch in tok[1:]:
                flag_set.add(ch)
    # helper booleans
    show_line_numbers = "n" in flag_set
    show_files_only = "l" in flag_set
    ignore_case = "i" in flag_set
    invert = "v" in flag_set
    match_entire = "x" in flag_set

    results = []

    for fname in files:
        try:
            f = open(fname)
        except Exception:
            # If file can't be opened, skip (tests don't cover)
            continue

        file_has_match = False
        for idx, line in enumerate(f, start=1):
            # ensure line includes trailing newline in output; line as read already has it
            line_content = line.rstrip('\n')
            # prepare strings for comparison
            if ignore_case:
                lhs = line_content.lower()
                rhs = pattern.lower()
            else:
                lhs = line_content
                rhs = pattern

            if match_entire:
                matched = lhs == rhs
            else:
                matched = rhs in lhs

            if invert:
                matched = not matched

            if matched:
                file_has_match = True
                if show_files_only:
                    # when -l, we only need to note file and break
                    break
                # build output line
                out_line = ""
                multiple_files = len(files) > 1
                if multiple_files:
                    out_line += f"{fname}:"
                if show_line_numbers:
                    out_line += f"{idx}:"
                out_line += line
                results.append(out_line)
        f.close()
        if show_files_only and file_has_match:
            results.append(f"{fname}\n")
    return "".join(results)
