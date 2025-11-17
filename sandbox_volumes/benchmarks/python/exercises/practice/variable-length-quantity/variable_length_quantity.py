def encode(numbers):
    """Encode a list of integers into VLQ byte sequences.
    Returns a list of bytes (ints 0-255).
    """
    out = []
    for n in numbers:
        if n == 0:
            out.append(0)
            continue
        parts = []
        x = n
        while x > 0:
            parts.append(x & 0x7F)
            x >>= 7
        parts.reverse()
        for i, p in enumerate(parts):
            if i != len(parts) - 1:
                out.append(p | 0x80)
            else:
                out.append(p)
    return out


def decode(bytes_):
    """Decode a list of VLQ bytes into a list of integers.

    Raises ValueError("incomplete sequence") if the final value is not
    terminated (i.e., stream ends with a byte that has the continuation bit set).
    """
    values = []
    current = 0
    in_progress = False
    for b in bytes_:
        if b & 0x80:
            # continuation byte
            in_progress = True
            current = (current << 7) | (b & 0x7F)
        else:
            # final byte for this value
            current = (current << 7) | (b & 0x7F)
            values.append(current)
            current = 0
            in_progress = False
    if in_progress:
        raise ValueError("incomplete sequence")
    return values
