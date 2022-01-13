import sys

import networkx as nx

from trigrid import TriGrid


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


def depth_greedy_traverse_hex(hex_graph: nx.Graph, start_hexes: []):
    traversed_set = {}
    depth_stack = start_hexes

    while depth_stack:
        current_hex = depth_stack.pop()
        if current_hex in traversed_set:
            continue
        traversed_set[current_hex] = True
        for next_hex in hex_graph.neighbors(current_hex):
            if next_hex not in traversed_set:
                depth_stack.append(next_hex)
        yield current_hex


def build_min_connected_nodes(hex_graph: nx.Graph) -> list:
    start_hexes = []
    start_level_hexes = []
    min_n_count = 0
    for cur_hex in hex_graph.nodes:
        n_count = sum(1 for _ in hex_graph.neighbors(cur_hex))
        if n_count == 0:
            start_hexes.append(cur_hex)
            continue

        if min_n_count == 0 or n_count <= min_n_count:
            if n_count < min_n_count:
                start_level_hexes.clear()

            min_n_count = n_count
            start_level_hexes.append(cur_hex)

    start_hexes.extend(start_level_hexes)

    return start_hexes


class ColorMap:
    def __init__(self):
        self.cmap = ([], [], [], [], [])
        self.color_count = 4

    def find(self, id: int) -> int:
        for color_num in range(self.color_count):
            id_list = self.cmap[color_num]
            if id in id_list:
                return color_num
        return None

    def remove(self, id: int, color: int):
        self.cmap[color].remove(id)

    def add(self, id: int, target_colors: [int] = [0, 1, 2, 3], adjacent_ids: [int] = []) -> bool:
        i = 0
        for target in target_colors:
            color_list = self.cmap[target]
            has_adjacent = False
            for adjacent_id in adjacent_ids:
                if adjacent_id in color_list:
                    has_adjacent = True
                    break
            if not has_adjacent:
                color_list.append(id)
                return i
            i = i + 1

        return -1

    def fail(self, id:int):
        self.cmap[self.color_count].append(id)


def coloring_simple(hex_graph: nx.Graph, color_map=None):
    if color_map is None:
        color_map = ColorMap()

    start_hexes = build_min_connected_nodes(hex_graph)

    print(f"Starting hexes:{start_hexes}")

    for cur_hex in depth_greedy_traverse_hex(hex_graph, start_hexes):
        reserved_list = [None] * 4
        for id in cur_hex:
            color_num = color_map.find(id)
            if color_num is not None:
                if reserved_list[color_num] is None:
                    reserved_list[color_num] = id
                else:
                    print(
                        f"Coloring blocked (color #{color_num})! Hex has forced color conflict between {id} and {reserved_list[color_num]}")
                    color_map.remove(id, color_num)
                    color_map.add(id, [3])
                    reserved_list[3] = id
                    break

        for id in cur_hex:
            if id not in reserved_list:
                unused_i = reserved_list.index(None)
                reserved_list[unused_i] = id
                color_map.add(id, [unused_i])

        print(f"Coloring hex:{cur_hex}:{reserved_list}")

    return color_map.cmap


def build_adjacency_map(node_list: []) -> {int: [int]}:
    amap = {}
    for triple in node_list:
        for v in triple:
            colors = amap.get(v)
            if colors is None:
                colors = [c for c in triple if c != v]
                amap[v] = colors
            else:
                for c in triple:
                    if not (c == v or c in colors):
                        colors.append(c)

    return amap


def coloring_odd_cycle_hex(hex_graph: nx.Graph, color_map=None):
    class Cycle:
        def __init__(self, nx_cycle):
            self.cycle = nx_cycle
            self.size = len(self.cycle)
            self.is_odd = self.size % 2 != 0
            self.all_ids = []
            core_ids = [x for x in self.cycle[0]]
            for triple in self.cycle:
                for id in triple:
                    if id not in self.all_ids:
                        self.all_ids.append(id)
            for triple in self.cycle:
                for id in core_ids:
                    if id not in triple:
                        core_ids.remove(id)
                if len(core_ids) == 1:
                    break
            self.core_id = core_ids[0]

        def __repr__(self):
            return str(self.cycle)

    if color_map is None:
        color_map = ColorMap()

    cycles = [Cycle(x) for x in nx.minimum_cycle_basis(hex_graph)]
    hex_map = {}
    hex_stack = []
    for cycle in cycles:
        for hex in cycle.cycle:
            cycle_list = hex_map.get(hex)
            if cycle_list is None:
                cycle_list = [cycle]
                hex_map[hex] = cycle_list
            else:
                cycle_list.append(cycle)

    def get_largest_cycle(cycle_list):
        while cycle_list:
            largest_cycle = cycle_list[0]
            for cycle in cycle_list[1:]:
                if len(cycle.cycle) > len(largest_cycle.cycle):
                    largest_cycle = cycle
            yield largest_cycle


    def process_cycle(cycle):
        try:
            cycles.remove(cycle)
        except ValueError:
            print(f"Double processing {cycle}")
            return False
        result = color_map.add(cycle.core_id, adjacent_ids=cycle.all_ids)
        print(f"looking at {cycle.core_id} with adj {cycle.all_ids}")
        print(f"color {result} for cycle {cycle}")
        if result == -1:
            print("Coloring Failed", file=sys.stderr)
            color_map.fail(cycle.core_id)
            failed_cycles.append(cycle)

        empty_hex_list = []

        for hex, cycle_list in hex_map.items():
            try:
                cycle_list.remove(cycle)
                if len(cycle_list) == 0:
                    empty_hex_list.append(hex)
            except ValueError:
                pass
        for hex in empty_hex_list:
            del hex_map[hex]
        return True

    failed_cycles = []

    for next_cycle in get_largest_cycle(cycles):
        cycle_stack = [next_cycle]
        # while cycle_stack:
            # next_cycle = cycle_stack.pop(0)
        for next_cycle in get_largest_cycle(cycle_stack):
            if process_cycle(next_cycle):
                hex_stack.extend(next_cycle.cycle)
                while hex_stack:
                    hex = hex_stack.pop(0)
                    if hex in hex_map:
                        cycle_list = hex_map.get(hex)
                        del hex_map[hex]
                        cycle_stack.extend(cycle_list)
            else:
                cycle_stack.remove(next_cycle)


    # coloring_simple(hex_graph, color_map)

    print(f"Failed cycles:{failed_cycles}", file=sys.stderr)

    return color_map.cmap
