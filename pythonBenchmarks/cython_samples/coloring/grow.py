import itertools
import random
import time

from trigrid import TriGrid


def generate(entity_count: int, tri_grid: TriGrid, iter_limit=0,rnd_seed=0):
    if entity_count == 0:
        return
    random.seed(rnd_seed)
    origins = seed(entity_count, tri_grid)
    grow(origins, tri_grid, iter_limit)


def seed(count: int, tri_grid: TriGrid):
    origins = []
    if count == 0:
        return origins

    for c in range(count):
        r = random.randrange((tri_grid.height * 2 - 1) * tri_grid.height // 2)
        ry = 0
        rx = 0
        for ry in range(tri_grid.height):
            r = r - ry * 2 + 1
            if r < 0:
                rx = ry * 2 + 1 + r
                break

        cell = tri_grid.get(rx, ry)
        if cell.id is None:
            cell.id = c
            origins.append(cell)

    tri_grid._seed_count = count

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

        eval_side(s_cell.a)
        eval_side(s_cell.c)
        eval_side(s_cell.b)

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
