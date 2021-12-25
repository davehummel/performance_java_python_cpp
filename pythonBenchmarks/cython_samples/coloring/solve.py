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
            if adj_id > seed_id:
                graph.add_edge(seed_id, adj_id)

    return graph


def brute_force(grid: TriGrid):
    mapping = [[], [], []]
    cell = grid.get(0, 0)
    mapping[0].append(cell.id)
