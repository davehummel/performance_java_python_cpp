import itertools
import random
import time

from trigrid import TriGrid


def generate(entity_count: int, tri_grid: TriGrid, iter_limit=0, rnd_seed=0):
    jj_mode = rnd_seed < 0

    if entity_count == 0:
        return
    random.seed(rnd_seed)

    if jj_mode:
        inner_grid = TriGrid(tri_grid.height - 4)
        origins = seed(entity_count, inner_grid)
        grow(origins, inner_grid, iter_limit)
        tri_grid.set_all_id(inner_grid.get(0, 0).id)
        tri_grid._seed_count = inner_grid._seed_count
        i = 0
        j = 0
        while True:
            inner_tri = inner_grid.get(i, j)
            if inner_tri is None:
                j = j + 1
                if j > inner_grid.height:
                    break
                i = 0
            else:
                tri_grid.get(i + 2, j + 2).id = inner_tri.id
                i = i + 1
    else:
        origins = seed(entity_count, tri_grid)
        grow(origins, tri_grid, iter_limit)


def seed(seed_count: int, tri_grid: TriGrid):
    origins = []
    if seed_count == 0:
        return origins

    cell_count = tri_grid.height * tri_grid.height

    if seed_count > cell_count:
        print(f"More seeds then cells.  Limiting seed count to {cell_count}")
        seed_count = cell_count

    exclusions = []
    for c in range(seed_count):
        while True:
            r = random.randrange(cell_count)
            if r not in exclusions:
                break
        exclusions.append(r)
        ry = 0
        rx = 0
        for ry in range(tri_grid.height):
            r = r - (ry * 2 + 1)
            if r < 0:
                rx = ry * 2 + 1 + r
                break

        cell = tri_grid.get(rx, ry)
        if cell.id is None:
            cell.id = c
            origins.append(cell)

    tri_grid._seed_count = seed_count
    tri_grid._seeds_ = list(range(seed_count))

    return origins


def grow(origins, tri_grid, iter_limit=0):
    start = time.time()
    fill_left = tri_grid.height * tri_grid.height

    fill_left = fill_left - len(origins)

    bodies = [[seed] for seed in origins]
    iter_count = 0

    while fill_left > 0:
        iter_count = iter_count + 1
        if iter_limit == iter_count:
            return

        s = random.randint(0, len(bodies) - 1)
        body = bodies[s]
        s_cell = body[-1]
        options = []

        def eval_side(side):
            if side is not None:
                if side.id is None:
                    options.append(side)

        for adj in s_cell.lrv():
            eval_side(adj)

        if len(options) > 0:
            option = random.choice(options)
            option.id = s_cell.id
            fill_left = fill_left - 1
            body.append(option)
            if fill_left % 100 == 0:
                print(f"remaining={fill_left} after {iter_count}")
        else:
            body.pop(-1)
            if len(body) == 0:
                bodies.pop(s)
    print(f"grow time:{time.time() - start}s")
