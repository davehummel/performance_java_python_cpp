import array
import itertools


class TriCell:
    id = None

    a = None
    b = None
    c = None

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"(x={self.x},y={self.y})"

    def __str__(self):
        if self.id is None:
            return f"<{self.x:02},{self.y:02}>"
        else:
            return f"<{self.id}|{self.x:02},{self.y:02}>"

    def adjacent(self, cell):
        return self.a == cell or self.b == cell or self.c == cell


class TriGrid:
    first_cell = None
    grid_store = None

    def __init__(self, height: int):
        if height < 1:
            raise "Height must be at least 1"

        self.height = height

        self.grid_store = [[TriCell(0, 0)]]

        for level in range(1, height):
            next_level = [TriCell(x, level) for x in range(level * 2 + 1)]
            for cell in next_level:
                if cell.x > 0:
                    cell.a = next_level[cell.x - 1]
                    cell.a.b = cell
                if cell.x % 2 == 1:
                    cell.c = self.grid_store[-1][cell.x -1]
                    cell.c.c = cell
            self.grid_store.append(next_level)

    def __repr__(self):
        return f"TriGrid(height={self.height})"

    def __str__(self):
        header = self.__repr__()
        body = "\n".join(" ".join(str(self.grid_store[i][j]) for j in range(i * 2 + 1)) for i in range(self.height))

        return header + "\n" + body

    def get(self, x: int, y: int):
        if x < 0 or y < 0:
            return None
        if (y >= self.height):
            return None
        if x >= y * 2 + 1:
            return None

        return self.grid_store[y][x]
