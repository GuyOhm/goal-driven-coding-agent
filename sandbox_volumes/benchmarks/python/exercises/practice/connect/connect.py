class ConnectGame:
    def __init__(self, board):
        # parse board string into grid of tokens
        # Split lines, strip leading/trailing spaces, split by whitespace
        lines = [line.strip() for line in board.splitlines() if line.strip() != ""]
        self.grid = [line.split() for line in lines]
        # handle single-character board with no spaces (e.g. "X" or "O")
        if len(self.grid) == 1 and len(self.grid[0]) == 1 and len(lines) == 1:
            single = lines[0]
            if single in ("X", "O", "."):
                self.grid = [[single]]
        # dimensions
        self.rows = len(self.grid)
        self.cols = len(self.grid[0]) if self.rows > 0 else 0

    def _neighbors(self, r, c):
        # Hex neighbors for parallelogram representation
        deltas = [
            (0, -1),  # left
            (0, 1),   # right
            (-1, 0),  # up
            (1, 0),   # down
            (-1, 1),  # up-right
            (1, -1),  # down-left
        ]
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                yield nr, nc

    def _has_path(self, player):
        from collections import deque
        visited = [[False]*self.cols for _ in range(self.rows)]
        q = deque()
        if player == 'X':
            # start from left edge
            for r in range(self.rows):
                if self.grid[r][0] == 'X':
                    q.append((r, 0))
                    visited[r][0] = True
        else:
            # O: start from top edge
            for c in range(self.cols):
                if self.grid[0][c] == 'O':
                    q.append((0, c))
                    visited[0][c] = True
        target_reached = False
        while q:
            r, c = q.popleft()
            # check target
            if player == 'X' and c == self.cols - 1:
                return True
            if player == 'O' and r == self.rows - 1:
                return True
            for nr, nc in self._neighbors(r, c):
                if not visited[nr][nc] and self.grid[nr][nc] == player:
                    visited[nr][nc] = True
                    q.append((nr, nc))
        return False

    def get_winner(self):
        if self.rows == 0 or self.cols == 0:
            return ""
        # Check both players. According to rules only one can win, but check both.
        if self._has_path('X'):
            return 'X'
        if self._has_path('O'):
            return 'O'
        return ""
