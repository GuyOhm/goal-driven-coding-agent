import string

ALPHABET = string.ascii_lowercase
M = len(ALPHABET)


def _gcd(x, y):
    while y:
        x, y = y, x % y
    return x


def _modinv(a, m):
    # Extended Euclidean algorithm
    a = a % m
    if _gcd(a, m) != 1:
        raise ValueError("a and m must be coprime.")
    # find inverse
    t0, t1 = 0, 1
    r0, r1 = m, a
    while r1 != 0:
        q = r0 // r1
        r0, r1 = r1, r0 - q * r1
        t0, t1 = t1, t0 - q * t1
    # r0 is gcd, t0 is inverse of a mod m if gcd==1
    inv = t0 % m
    return inv


def _check_coprime(a, m=M):
    if _gcd(a % m, m) != 1:
        raise ValueError("a and m must be coprime.")


def encode(plain_text, a, b):
    _check_coprime(a)
    res_chars = []
    for ch in plain_text.lower():
        if ch.isalpha():
            i = ALPHABET.index(ch)
            enc_i = (a * i + b) % M
            res_chars.append(ALPHABET[enc_i])
        elif ch.isdigit():
            res_chars.append(ch)
        else:
            # skip spaces and punctuation
            continue
    # group into blocks of 5
    groups = ["".join(res_chars[i : i + 5]) for i in range(0, len(res_chars), 5)]
    return " ".join(groups)


def decode(ciphered_text, a, b):
    _check_coprime(a)
    a_inv = _modinv(a, M)
    # remove spaces and other non-alphanumeric except digits and letters
    cleaned = [ch for ch in ciphered_text.lower() if ch.isalnum()]
    res = []
    for ch in cleaned:
        if ch.isalpha():
            y = ALPHABET.index(ch)
            x = (a_inv * (y - b)) % M
            res.append(ALPHABET[x])
        else:
            # digits
            res.append(ch)
    return "".join(res)
