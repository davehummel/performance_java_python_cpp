import networkx as nx

from cython_samples.coloring.trigrid import TriGrid


def build_graph(grid: TriGrid):
    graph = nx.Graph()
    seed_count = grid.seed_count()
    if seed_count is None or seed_count == 0:
        return graph

    graph.add_nodes_from(range(seed_count))

    for seed_id in range(seed_count):
        adj_ids = grid.find_adjacent_ids(seed_id)
        for adj_id in adj_ids:
            if adj_id is None:
                continue
            if adj_id > seed_id:
                graph.add_edge(seed_id, adj_id)

    return graph


def directional_color_map(grid: TriGrid):
    mapping = {0: [], 1: [], 2: [], 3: []}
    mapped = [False for n in range(grid.seed_count())]
    grid.set_all(None)

    def expand(cur_cell, prev_cell):
        if cur_cell is None:
            return
        if cur_cell.state == True:
            return

        if not mapped[cur_cell.id]:
            mapped[cur_cell.id] = True
            if cur_cell.y == prev_cell.y:
                if cur_cell.x < prev_cell.x:
                    mapping[1].append(cur_cell.id)
                else:
                    mapping[3].append(cur_cell.id)
            else:
                if cur_cell.y < prev_cell.y:
                    mapping[0].append(cur_cell.id)
                else:
                    mapping[2].append(cur_cell.id)

        cur_cell.state = True

        expand(cur_cell.a, cur_cell)
        expand(cur_cell.b, cur_cell)
        expand(cur_cell.c, cur_cell)

    cell = grid.get(0, 0)
    mapping[0].append(cell.id)
    mapped[cell.id] = True
    expand(cell, cell.c)  # Assume we at least have a second row
    return mapping


def find_3_color_hex(grid: TriGrid):
    mapping = [[], [], []]
    cell = grid.get(0, 0)
    mapping[0].append(cell.id)
