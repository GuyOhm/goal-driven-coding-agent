class Scale:
    SHARP_SCALE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    FLAT_SCALE = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

    FLAT_MAJOR = {"F", "Bb", "Eb", "Ab", "Db", "Gb"}
    FLAT_MINOR = {"d", "g", "c", "f", "bb", "eb"}

    def __init__(self, tonic):
        # Normalize tonic: first letter uppercase, rest unchanged (so 'b' remains lowercase)
        if not tonic:
            self.tonic = tonic
        else:
            self.tonic = tonic[0].upper() + tonic[1:]

        t_low = tonic.lower()
        # Determine flats vs sharps based on whether tonic denotes major (uppercase) or minor (lowercase)
        if tonic[0].isupper():
            # Major keys: use flats if tonic in FLAT_MAJOR
            self.use_flats = self.tonic in self.FLAT_MAJOR
        else:
            # Minor keys: use flats if tonic (lowercase) in FLAT_MINOR
            self.use_flats = t_low in self.FLAT_MINOR

    def chromatic(self):
        scale = self.FLAT_SCALE if self.use_flats else self.SHARP_SCALE
        # find starting index matching tonic
        try:
            start = scale.index(self.tonic)
        except ValueError:
            # If not found in chosen representation, try the alternate spelling
            alt = self.SHARP_SCALE if self.use_flats else self.FLAT_SCALE
            try:
                start = alt.index(self.tonic)
                scale = alt
            except ValueError:
                # fallback
                start = 0
        # rotate
        return [scale[(start + i) % 12] for i in range(12)]

    def interval(self, intervals):
        # choose chromatic representation according to tonic preference
        scale = self.FLAT_SCALE if self.use_flats else self.SHARP_SCALE
        # ensure tonic is in scale; if not, try alternate
        if self.tonic not in scale:
            alt = self.SHARP_SCALE if self.use_flats else self.FLAT_SCALE
            if self.tonic in alt:
                scale = alt
        # find start index
        idx = scale.index(self.tonic)
        result = [scale[idx]]
        step_map = {"m": 1, "M": 2, "A": 3}
        for ch in intervals:
            step = step_map.get(ch, 0)
            idx = (idx + step) % 12
            result.append(scale[idx])
        return result
