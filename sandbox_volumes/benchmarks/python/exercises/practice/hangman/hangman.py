# Game status categories
# Change the values as you see fit
STATUS_WIN = 'win'
STATUS_LOSE = 'lose'
STATUS_ONGOING = 'ongoing'


class Hangman:
    def __init__(self, word):
        self.word = word
        self.guessed = set()
        self.remaining_guesses = 9
        self.status = STATUS_ONGOING

    def guess(self, char):
        # If the game has already ended, raise ValueError with required message
        if self.status != STATUS_ONGOING:
            raise ValueError("The game has already ended.")

        # If letter was already guessed, count as a failure
        if char in self.guessed:
            self.remaining_guesses -= 1
            if self.remaining_guesses < 0:
                self.status = STATUS_LOSE
            return

        # mark as guessed
        self.guessed.add(char)

        # If guess is not in the word, decrement remaining guesses
        if char not in self.word:
            self.remaining_guesses -= 1
            if self.remaining_guesses < 0:
                self.status = STATUS_LOSE
            return

        # If guess is correct, check for win
        # If all letters revealed, set status to win
        if all(ch in self.guessed for ch in self.word):
            self.status = STATUS_WIN

    def get_masked_word(self):
        return ''.join(c if c in self.guessed else '_' for c in self.word)

    def get_status(self):
        return self.status
