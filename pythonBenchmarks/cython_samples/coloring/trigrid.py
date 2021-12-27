class TriCell:
    id = None

    a = None
    b = None
    c = None

    state = None

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
    grid_store = None

    _seed_count = 0

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
                    cell.c = self.grid_store[-1][cell.x - 1]
                    cell.c.c = cell
            self.grid_store.append(next_level)

    def __repr__(self):
        return f"TriGrid(height={self.height})"

    def __str__(self):
        header = self.__repr__()
        body = "\n".join(" ".join(str(self.grid_store[i][j]) for j in range(i * 2 + 1)) for i in range(self.height))

        return header + "\n" + body

    def seed_count(self):
        return self._seed_count

    def get(self, x: int, y: int):
        if x < 0 or y < 0:
            return None
        if (y >= self.height):
            return None
        if x >= y * 2 + 1:
            return None

        return self.grid_store[y][x]

    def set_all(self,state):
        for y in range(self.height):
            for x in range(y * 2 + 1):
                self.grid_store[y][x].state =state


    def find_cell_for_id(self, id: int):
        for row in self.grid_store:
            for cell in row:
                if cell.id == id:
                    return cell
        return None

    def find_adjacent_ids(self, id: int):
        adj = {}
        for row in self.grid_store:
            for cell in row:
                if cell.id == id:
                    if cell.a is not None:
                        if cell.a.id != id:
                            adj[cell.a.id] = True
                    if cell.b is not None:
                        if cell.b.id != id:
                            adj[cell.b.id] = True
                    if cell.c is not None:
                        if cell.c.id != id:
                            adj[cell.c.id] = True

        return adj.keys()
