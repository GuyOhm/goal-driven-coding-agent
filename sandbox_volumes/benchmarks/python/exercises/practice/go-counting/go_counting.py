BLACK = 'B'
WHITE = 'W'
NONE = ''

class Board:
    """Count territories of each player in a Go game

    Args:
        board (list[str]): A two-dimensional Go board
    """

    def __init__(self, board):
        # store board as list of strings
        self.board = board
        self.height = len(board)
        self.width = len(board[0]) if self.height > 0 else 0

    def _in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def territory(self, x, y):
        """Find the owner and the territories given a coordinate on
           the board
        """
        # validate coordinates
        if not self._in_bounds(x, y):
            raise ValueError('Invalid coordinate')

        ch = self.board[y][x]
        # if it's a stone, not a territory
        if ch == BLACK or ch == WHITE:
            return (NONE, set())

        # flood fill empty region
        to_visit = [(x, y)]
        visited = set()
        bordering = set()

        while to_visit:
            cx, cy = to_visit.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))

            # explore neighbors
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if not self._in_bounds(nx, ny):
                    # edge of board - doesn't add a bordering stone
                    continue
                neighbor = self.board[ny][nx]
                if neighbor == ' ':
                    if (nx, ny) not in visited:
                        to_visit.append((nx, ny))
                elif neighbor == BLACK:
                    bordering.add(BLACK)
                elif neighbor == WHITE:
                    bordering.add(WHITE)
                # other characters are ignored

        # determine owner
        if bordering == {BLACK}:
            owner = BLACK
        elif bordering == {WHITE}:
            owner = WHITE
        else:
            owner = NONE

        return (owner, visited)

    def territories(self):
        """Find the owners and the territories of the whole board"""
        result = {BLACK: set(), WHITE: set(), NONE: set()}
        seen = set()

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in seen:
                    continue
                ch = self.board[y][x]
                if ch == ' ':
                    owner, region = self.territory(x, y)
                    # add region to owner and mark seen
                    result[owner].update(region)
                    seen.update(region)
                else:
                    # stones are not territories
                    seen.add((x, y))

        return result
