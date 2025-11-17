import random
import string


class Robot:
    # Keep track of assigned names
    _assigned_names = set()

    def __init__(self):
        # Name is generated lazily
        self._name = None

    @property
    def name(self):
        if self._name is None:
            self._name = self._generate_name()
            Robot._assigned_names.add(self._name)
        return self._name

    def reset(self):
        """Reset robot to factory settings. Generate a new unique name.
        The old name is kept reserved while generating a new one to avoid
        generating the same name again when RNG is reseeded to the same state.
        """
        old = self._name
        # If robot has no name yet, just generate one
        if old is None:
            self._name = self._generate_name()
            Robot._assigned_names.add(self._name)
            return

        # Keep old name reserved to prevent reassigning it
        # Generate a new unique name
        new_name = self._generate_name(exclude={old})
        # Replace assignment
        Robot._assigned_names.add(new_name)
        self._name = new_name
        # Remove old name from assigned set
        Robot._assigned_names.discard(old)

    def _generate_name(self, exclude=None):
        if exclude is None:
            exclude = set()
        # generate until find one not in assigned and not in exclude
        while True:
            letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(2))
            numbers = ''.join(random.choice(string.digits) for _ in range(3))
            candidate = letters + numbers
            if candidate in Robot._assigned_names:
                continue
            if candidate in exclude:
                continue
            return candidate
