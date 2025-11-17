def transpose(text):
    if text == "":
        return ""
    lines = text.split("\n")
    maxlen = max(len(line) for line in lines)
    rows = []
    for i in range(maxlen):
        chars = []
        padded = []
        for line in lines:
            if i < len(line):
                chars.append(line[i])
                padded.append(False)
            else:
                chars.append(' ')
                padded.append(True)
        # find last index that is not padded
        last = None
        for idx in range(len(padded)-1, -1, -1):
            if not padded[idx]:
                last = idx
                break
        if last is None:
            row = ''
        else:
            row = ''.join(chars[: last+1])
        rows.append(row)
    return '\n'.join(rows)
