class BowlingGame:
    def __init__(self):
        self.rolls = []

    def roll(self, pins):
        # basic validation
        if pins < 0:
            raise ValueError("negative roll is invalid")
        if pins > 10:
            raise ValueError("pin count exceeds pins on the lane")

        # If game already complete, cannot roll
        if self._is_game_complete():
            raise IndexError("cannot roll after game is over")

        # Tentatively append and validate frame constraints
        self.rolls.append(pins)
        try:
            self._validate_state()
        except Exception:
            # rollback the append before re-raising
            self.rolls.pop()
            raise

    def score(self):
        if not self.rolls:
            raise ValueError("score cannot be taken until the game is complete")
        if not self._is_game_complete():
            raise ValueError("score cannot be taken until the game is complete")

        total = 0
        rolls = self.rolls
        i = 0
        for frame in range(10):
            if rolls[i] == 10:
                # strike
                total += 10 + self._next_two_rolls(i)
                i += 1
            else:
                frame_score = rolls[i] + (rolls[i + 1] if i + 1 < len(rolls) else 0)
                if frame_score == 10:
                    # spare
                    total += 10 + (rolls[i + 2] if i + 2 < len(rolls) else 0)
                else:
                    total += frame_score
                i += 2
        return total

    # Helpers
    def _next_two_rolls(self, i):
        rolls = self.rolls
        next1 = rolls[i + 1] if i + 1 < len(rolls) else 0
        next2 = rolls[i + 2] if i + 2 < len(rolls) else 0
        return next1 + next2

    def _validate_state(self):
        rolls = self.rolls
        # Validate frames 1-9: no two-roll frame sum > 10
        i = 0
        frame = 1
        n = len(rolls)
        while frame <= 9 and i < n:
            if rolls[i] == 10:
                # strike
                i += 1
            else:
                if i + 1 >= n:
                    # incomplete frame - can't validate sum yet
                    return
                if rolls[i] + rolls[i + 1] > 10:
                    raise ValueError("two rolls in a frame cannot score more than 10")
                i += 2
            frame += 1

        # Now validate 10th frame if any rolls present for it
        if frame == 10:
            # the rest of the rolls starting at i belong to 10th frame (possibly partial)
            rest = rolls[i:]
            if not rest:
                return
            # Validate individual rolls
            for r in rest:
                if r < 0 or r > 10:
                    raise ValueError("invalid roll")

            first = rest[0]
            if first == 10:
                # strike on first ball of tenth -> need two bonus rolls to complete
                if len(rest) == 1:
                    return
                # second roll exists
                second = rest[1]
                if len(rest) == 2:
                    return
                # third roll exists
                third = rest[2]
                # validation: if second is not a strike, then second+third cannot exceed 10
                if second != 10:
                    if second + third > 10:
                        raise ValueError("invalid fill balls")
                # each bonus must be between 0 and 10 (checked above)
            else:
                # first != 10
                if len(rest) == 1:
                    return
                second = rest[1]
                if first + second > 10:
                    raise ValueError("two rolls in tenth frame cannot score more than 10 unless strike")
                if first + second == 10:
                    # spare: must have exactly one bonus roll to be complete
                    if len(rest) == 2:
                        return
                    if len(rest) > 3:
                        raise ValueError("too many rolls")
                else:
                    # open frame: should have exactly two rolls, no bonus
                    if len(rest) > 2:
                        raise ValueError("cannot roll after game is over")

    def _is_game_complete(self):
        # Determine if game has 10 complete frames
        rolls = self.rolls
        i = 0
        frame = 1
        n = len(rolls)
        while frame <= 9 and i < n:
            if rolls[i] == 10:
                i += 1
            else:
                if i + 1 >= n:
                    return False
                i += 2
            frame += 1
        if frame <= 9:
            return False
        # tenth frame
        if i >= n:
            return False
        first = rolls[i]
        rest = rolls[i:]
        if first == 10:
            # need two bonus rolls
            return len(rest) >= 3
        else:
            if len(rest) < 2:
                return False
            if rest[0] + rest[1] == 10:
                # spare needs one bonus
                return len(rest) >= 3
            else:
                return len(rest) == 2
