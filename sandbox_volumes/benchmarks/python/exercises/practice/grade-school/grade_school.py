class School:
    def __init__(self):
        # map grade_number -> set of student names
        self._grades = {}
        # map name -> grade number (to prevent duplicates across grades)
        self._name_to_grade = {}
        # history of add_student results
        self._added_history = []

    def add_student(self, name, grade):
        """Add a student with name to a grade.
        Returns True if added, False if student already exists in roster (in any grade).
        Records the result in the added history.
        """
        if name in self._name_to_grade:
            result = False
        else:
            # add to grade set
            self._grades.setdefault(grade, set()).add(name)
            self._name_to_grade[name] = grade
            result = True
        self._added_history.append(result)
        return result

    def roster(self):
        """Return a list of all students sorted by grade then name."""
        roster_list = []
        for grade in sorted(self._grades.keys()):
            names = sorted(self._grades.get(grade, []))
            roster_list.extend(names)
        return roster_list

    def grade(self, grade_number):
        """Return sorted list of students in the given grade."""
        return sorted(self._grades.get(grade_number, []))

    def added(self):
        """Return the history list of booleans for add_student operations."""
        return list(self._added_history)
