import re


def translate(text):
    words = text.split()
    result = []
    for word in words:
        # Rule 1: starts with a vowel or 'xr' or 'yt'
        if re.match(r'^(?:[aeiou]|xr|yt)', word):
            result.append(word + 'ay')
            continue
        # find first vowel: a,e,i,o,u or y (but y not at start)
        first_vowel = None
        for i, ch in enumerate(word):
            if ch in 'aeiou' or (ch == 'y' and i != 0):
                first_vowel = i
                break
        if first_vowel is None:
            # no vowel found (unlikely), treat whole word as consonant cluster
            first_vowel = len(word)
        # handle 'qu' following consonant cluster: if vowel is 'u' and preceded by 'q', include 'u'
        if first_vowel < len(word) and word[first_vowel] == 'u' and first_vowel > 0 and word[first_vowel - 1] == 'q':
            first_vowel += 1
        # Build translated word
        translated = word[first_vowel:] + word[:first_vowel] + 'ay'
        result.append(translated)
    return ' '.join(result)
