import itertools
import random
import time

from trigrid import TriGrid


def generate(seed_count: int, tri_grid: TriGrid, iter_limit=0):
    if seed_count == 0:
        return
    origins = seed(seed_count, tri_grid)
    grow(origins, tri_grid, iter_limit)


def seed(count: int, tri_grid: TriGrid):
    origins = []
    if count == 0:
        return origins

    for c in range(count):
        ry = random.randrange(tri_grid.height)
        rx = random.randrange(ry * 2 + 1)
        cell = tri_grid.get(rx, ry)
        if cell.id is None:
            cell.id = c
            origins.append(cell)

    return origins


def grow(origins, tri_grid, iter_limit=0):
    start = time.time()
    fill_left = sum([v * 2 + 1 for v in range(tri_grid.height)])

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

        eval_side(s_cell.c)
        eval_side(s_cell.a)
        eval_side(s_cell.b)

        r = random.randint(0, 100)

        if len(options) > 0:
            option = options[r % len(options)]
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
