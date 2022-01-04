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


def find_3_color_hexes(grid: TriGrid):
    hexes = []
    triangles = grid.triangles()
    for triangle in triangles:
        if triangle.x % 2 == 0:
            continue
        hex_triangles = [triangle.a, triangle.b]
        if None in hex_triangles:
            continue
        hex_triangles.append(triangle.a.c)
        hex_triangles.append(triangle.b.c)
        if None in hex_triangles:
            continue
        hex_triangles.append(triangle.a.c.b)
        ids = [triangle.id]
        for hex_triangle in hex_triangles:
            if hex_triangle.id not in ids:
                ids.append(hex_triangle.id)

        if len(ids) == 3:
            hexes.append(triangle)
            ids.sort()
            triangle.state = ids
            print(f"[{ids[0]},{ids[1]},{ids[2]}]" + str(triangle) + "V" + " ".join(str(ht) for ht in hex_triangles))

    return hexes


def find_two_color_linked_hex_graph(three_id_hexes):
    unique_triples = {}
    pair_match_map = {}
    graph = nx.Graph()

    for hex in three_id_hexes:
        triplet = (hex.state[0], hex.state[1], hex.state[2])

        out = unique_triples.get(triplet)
        if out is None:
            unique_triples[triplet] = [hex]
        else:
            out.append(hex)
            print(f"Dropping duplicate hex [{out}]<{hex}>")
            continue

        pairs = ((triplet[0], triplet[1]), (triplet[0], triplet[2]), (triplet[1], triplet[2]))

        for pair in pairs:
            out = pair_match_map.get(pair)
            if out is None:
                pair_match_map[pair] = [triplet]
            else:
                out.append(triplet)

    for (triplet, hex_list) in unique_triples.items():
        graph.add_node(triplet, hex_list=hex_list)

    for pair, triplets in pair_match_map.items():
        for i in range(len(triplets)):
            for j in range(i + 1, len(triplets)):
                graph.add_edge(triplets[i], triplets[j], pair=pair)

    return graph


def simple_coloring(hex_graph: nx.Graph, three_id_hexes):
    color_map = [[], [], [], []]

    for hex in hex_graph.nodes:
        reserved_list = [None] * 4
        for id in hex.state:
            for color_num in range(len(color_map)):
                color_list = color_map[color_num]
                if id in color_list:
                    if reserved_list[color_num] is None:
                        reserved_list[color_num] = id
                    else:
                        print(
                            f"Coloring failed! Hex has forced color conflict between {id} and {reserved_list[color_num]}")
                    break

        for id in hex.state:
            if id not in reserved_list:
                unused_i = reserved_list.index(None)
                reserved_list[unused_i] = id
                color_map[unused_i].append(id)

    return color_map
