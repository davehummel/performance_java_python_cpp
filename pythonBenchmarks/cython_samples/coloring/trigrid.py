class TriCell:
    id = None

    a = None
    b = None
    c = None

    state = None

    def __init__(self, x, y):
        self.__x = x
        self.__y = y

    def __repr__(self):
        return f"(x={self.__x},y={self.__y})"

    def __str__(self):
        return self.to_string_with_offset()

    def to_string_with_offset(self, offset: (int, int) = (0, 0)):
        if self.id is None:
            return f"<{self.__x + offset[0]:02},{self.__y + offset[1]:02}>"
        else:
            return f"<{self.id}|{self.__x + offset[0]:02},{self.__y + offset[1]:02}>"

    def adjacent(self, cell):
        return self.a == cell or self.b == cell or self.c == cell

    def xy(self, offset: (int, int) = None):
        if offset is None:
            return self.__x, self.__y
        else:
            return self.__x + offset[0], self.__y + offset[1]


class TriGrid:
    def __init__(self, height: int, up=True, view_source=None, offset: (int, int) = (0, 0)):
        if height < 1:
            raise ValueError("Height must be at least 1")
        if offset[0] < 0 or offset[1] < 0:
            raise ValueError("offset (x,y) must both be positive")

        self.height = height
        self.offset = offset
        self.up = up

        if view_source is None:
            if offset[0] != 0 or offset[1] != 0:
                raise ValueError("view_source parameter is not set."
                                 " Offset can only be non-zero with a provided view_source")

            self.grid_store = [[TriCell(0, 0)]]

            for level in range(1, height) if up else range(height_, 1, -1):
                next_level = [TriCell(x, level) for x in range(level * 2 + 1)]
                for cell in next_level:
                    cx, _ = cell.xy()
                    if cx > 0:
                        cell.a = next_level[cx - 1]
                        cell.a.b = cell
                    if cx % 2 == 1:
                        cell.c = self.grid_store[-1][cx - 1]
                        cell.c.c = cell
                self.grid_store.append(next_level)
        else:
            if offset[1] + height > view_source.height:
                raise ValueError(
                    f"height {height} + y offset {offset[1]} exceeds max height {view_source.height} of view_source")

            if up:
                if offset[0] + height > view_source.get_row_width(offset[1] + height -1):
                    raise ValueError(
                        f"width {height} + x offset {offset[0]} exceeds width at {view_source.get_row_width(offset[1] + height)}")
            else:
                if offset[0] + height > view_source.get_row_width(offset[1]) - 1:
                    raise ValueError(
                        f"width {height} + x offset {offset[0]} exceeds width at {view_source.get_row_width(offset[1])}")

            self.grid_store = view_source.grid_store

    def __repr__(self):
        return f"TriGrid(height={self.height},offset={self.offset},up={self.up})"

    def __str__(self):
        header = self.__repr__()
        body = "\n".join(" ".join(str(tri) for tri in self.triangles()))

        return header + "\n" + body

    def get_row_width(self, y: int) -> int:
        if y >= self.height:
            raise IndexError(f"y is out of range [0-{self.height - 1}]")
        if self.up:
            return y * 2 + 1
        else:
            return (self.height - y - 1) * 2 + 1

    def seed_count(self):
        return self._seed_count

    def get_seeds(self):
        if self._seeds_ is None:
            d = {tri.id: True for tri in self.triangles()}
            _seeds_ = d.keys()
        return self._seeds_

    def get(self, x: int, y: int):
        if x < 0 or y < 0:
            return None
        if y >= self.height:
            return None
        if x >= self.get_row_width(y):
            return None
        return self.grid_store[y + self.offset[1]][x + self.offset[0]]

    def set_all_state(self, state):
        for tri in self.triangles():
            tri.state = state

    def set_all_id(self, id):
        for tri in self.triangles():
            tri.id = id

    def find_cell_for_id(self, id: int):
        for tri in self.triangles():
            if tri.id == id:
                return cell
        return None

    def find_adjacent_ids(self, id: int):
        adj = {}
        for cell in self.triangles():
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

    def triangles(self):
        for y in range(self.height):
            for x in range(y * 2 + 1):
                yield self.get(x, y)

    def sub_divide(self):
        if self.up:
            return (
                TriGrid(self.height // 2, up=True, view_source=self, offset=(0, 0)),
                TriGrid(self.height // 2, up=True, view_source=self, offset=(0, self.height // 2)),
                TriGrid(self.height // 2, up=False, view_source=self, offset=(1, self.height // 2)),
                TriGrid(self.height // 2, up=True, view_source=self, offset=(self.height, self.height // 2)),
            )
