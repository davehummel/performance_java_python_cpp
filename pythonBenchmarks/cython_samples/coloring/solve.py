import sys

import networkx as nx

from trigrid import TriGrid, TriCell


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

    def add(self, id: int, target_colors: [int] = [0, 1, 2, 3], adjacent_ids: [int] = []) -> int:
        for target in target_colors:
            color_list = self.cmap[target]
            has_adjacent = False
            for adjacent_id in adjacent_ids:
                if adjacent_id in color_list:
                    has_adjacent = True
                    break
            if not has_adjacent:
                color_list.append(id)
                return target

        return -1

    def fail(self, id: int):
        self.cmap[self.color_count].append(id)


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


def coloring_simple(tri_grid: TriGrid, hex_graph: nx.Graph, color_map=None):
    if color_map is None:
        color_map = ColorMap()

    start_hexes = build_min_connected_nodes(hex_graph)
    adjacency_map = build_adjacency_map(hex_graph.nodes)

    print(f"Starting hexes:{start_hexes}")

    for cur_hex in depth_greedy_traverse_hex(hex_graph, start_hexes):
        reserved_list = [None] * 5
        for id in cur_hex:
            color_num = color_map.find(id)
            print(f"Found existing color {color_num} for id {id}")
            if color_num is not None:
                if reserved_list[color_num] is None:
                    reserved_list[color_num] = id
                else:
                    alt_colors = list(filter(lambda a: reserved_list[a] is None, range(4)))
                    color_map.remove(id, color_num)
                    alt_color = color_map.add(id, alt_colors, adjacency_map[id])
                    print(f"Coloring blocked for {cur_hex}(id {id} on color {color_num})!")
                    print(f" id conflict [{id} , {reserved_list[color_num]}]")
                    print(f" Moved id {id} to {alt_color} from available colors {alt_colors}")
                    if alt_color > -1:
                        reserved_list[alt_color] = id
                    else:
                        print("Color choice failed!")
                        reserved_list[4] = id
                        color_map.add(id, [4])

        for id in cur_hex:
            if id not in reserved_list:
                unused_i = reserved_list.index(None)
                reserved_list[unused_i] = id
                color_map.add(id, [unused_i])

        print(f"Coloring hex:{cur_hex}:{reserved_list}")
        print(color_map.cmap)

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


def build_hex_to_cycle_map(all_cycles: [Cycle]) -> {}:
    hex_map = {}
    for cycle in all_cycles:
        for hex in cycle.cycle:
            cycle_list = hex_map.get(hex)
            if cycle_list is None:
                cycle_list = [cycle]
                hex_map[hex] = cycle_list
            else:
                cycle_list.append(cycle)
    return hex_map


def build_cycle_to_cycle_map(all_cycles: [Cycle]) -> {}:
    map = {}
    for cycle in all_cycles:
        neighbors = []
        for id in cycle.all_ids:
            for potential in all_cycles:
                if potential is cycle:
                    continue
                if potential.core_id == id:
                    neighbors.append(potential)
            map[cycle] = neighbors
    return map


def build_hex_cycles_by_common_id(hex_graph: nx.Graph):
    id_map = {}
    for hex in hex_graph.nodes:
        for id in hex:
            hex_list = id_map.get(id)
            if hex_list is None:
                hex_list = [hex]
                id_map[id] = hex_list
            else:
                hex_list.append(hex)
    cycle_list = []

    for id, hex_list in id_map.items():
        subgraph = hex_graph.subgraph(hex_list)
        if nx.is_k_edge_connected(subgraph, 2):
            cycle_list.append(Cycle(hex_list))

    return cycle_list


def coloring_neighbored_hex_cycle(tri_grid: TriGrid, hex_graph: nx.Graph, color_map=None):
    if color_map is None:
        color_map = ColorMap()
    # cycles = [Cycle(x) for x in nx.minimum_cycle_basis(hex_graph)]
    cycles = build_hex_cycles_by_common_id(hex_graph)
    cycle_neighbor_map = build_cycle_to_cycle_map(cycles)

    def emit_minimally_neighbored_cycle(cycle_list: [Cycle]):
        while cycle_list:
            min_cycle = None
            min_neighbor_count = sys.maxsize
            for cycle in cycle_list:
                neighbor_count = len(cycle_neighbor_map.get(cycle))
                if neighbor_count < min_neighbor_count:
                    min_neighbor_count = neighbor_count
                    min_cycle = cycle
            yield min_cycle

    def get_highest_contention_cycle(cycle_list: [Cycle]) -> Cycle:
        max_contention = None
        max_colored_count = 0
        for cycle in cycle_list:
            neighbors = cycle_neighbor_map.get(cycle)
            colored_neighbor_count = 0
            for neighbor in neighbors:
                if color_map.find(neighbor.core_id):
                    colored_neighbor_count = colored_neighbor_count + 1
            print(f"Contention on cycle {neighbors} is {colored_neighbor_count}")
            if colored_neighbor_count > max_colored_count:
                max_contention = cycle
                max_colored_count = colored_neighbor_count
        return max_contention

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
            print("!!Coloring Failed!!")
            color_map.fail(cycle.core_id)
            failed_cycles.append(cycle)

        return True

    failed_cycles = []

    for next_cycle in emit_minimally_neighbored_cycle(cycles):
        process_cycle(next_cycle)
        while True:
            next_cycle = get_highest_contention_cycle(cycles)
            if next_cycle is None:
                break
            process_cycle(next_cycle)

    # coloring_simple(hex_graph, color_map)

    print(f"Failed cycles:{failed_cycles}")

    return color_map.cmap


def coloring_large_hex_cycle(tri_grid: TriGrid, hex_graph: nx.Graph, color_map=None):
    if color_map is None:
        color_map = ColorMap()

    cycles = [Cycle(x) for x in nx.minimum_cycle_basis(hex_graph)]
    hex_cycle_map = build_hex_to_cycle_map(cycles)
    hex_stack = []
    for cycle in cycles:
        for hex in cycle.cycle:
            cycle_list = hex_cycle_map.get(hex)
            if cycle_list is None:
                cycle_list = [cycle]
                hex_cycle_map[hex] = cycle_list
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
            print("!!Coloring Failed!!")
            color_map.fail(cycle.core_id)
            failed_cycles.append(cycle)

        empty_hex_list = []

        for hex, cycle_list in hex_cycle_map.items():
            try:
                cycle_list.remove(cycle)
                if len(cycle_list) == 0:
                    empty_hex_list.append(hex)
            except ValueError:
                pass
        for hex in empty_hex_list:
            del hex_cycle_map[hex]
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
                    if hex in hex_cycle_map:
                        cycle_list = hex_cycle_map.get(hex)
                        del hex_cycle_map[hex]
                        cycle_stack.extend(cycle_list)
            else:
                cycle_stack.remove(next_cycle)

    # coloring_simple(hex_graph, color_map)

    print(f"Failed cycles:{failed_cycles}")

    return color_map.cmap


def coloring_recursive_triangulation(tri_grid: TriGrid, hex_graph: nx.Graph, color_map=None):
    if color_map is not None:
        raise Exception("Recursive triangulation cannot take existing color map")
    color_map = ColorMap()

    def solve_constraints(constraint_list):
        rel_nots = []
        rel_eqs = []
        abs_nots = []
        abs_eq = None
        unconstrained = True
        for adj in (self.a, self.b, self.c):
            if adj is not None:
                unconstrained = False

        if unconstrained:
            return None
        else:
            return (abs_eq,abs_nots,rel_eqs,rel_nots)



    def resolve(cell: TriCell):
        if len(cell.id) == 1:
            constraints = build_constraints(cell)
            color = solve_constraints(constraints)
            color_map.add(cell.id[0], [color])
            cell.state = color
        else:
            # Todo: subdivide
            pass

    div_size = tri_grid.height

    while div_size > 2:
        div_size = div_size / 2
    if div_size != 2 and div_size != 1:
        raise Exception("Recursive triangulation only applies to grids that are sizes of 2^n for whole n")

    tri_root = TriCell(0, 0)
    tri_root.id = list(range(tri_grid.seed_count()))
    tri_root.state = tri_grid()

    resolve(tri_root)

    return color_map.cmap
