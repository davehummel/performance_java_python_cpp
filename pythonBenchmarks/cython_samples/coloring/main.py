import math
import time
import tkinter as tk
import re
from PIL import Image, ImageTk, ImageDraw
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import grow as gr
import trigrid as tg
import solve as sv

matplotlib.use("TkAgg")

color_palette = [item for set in zip(plt.get_cmap("tab20b").colors, plt.get_cmap("tab20c").colors) for item in set]
color_palette = [color_palette[i // 5 + i % 5 * 8] for i in range(40)]
four_color_palette = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (.9, .9, 1)]


def color_convert(color):
    # return f"#{int(255 * color[0]):02X}{int(255 * color[1]):02X}{int(255 * color[2]):02X}"
    return int(255 * color[0]), int(255 * color[1]), int(255 * color[2])


tri_grid = None
graph_model = None
three_id_hexes = None
hex_graph = None
coloring_solution = None


# The main window of the animation
def create_main_window():
    main_window = tk.Tk()
    main_window.title("Coloring")

    def on_closing():
        main_window.quit()

    main_window.protocol("WM_DELETE_WINDOW", on_closing)
    return main_window


def create_grow_controls(window):
    def whole_num_validate(input_text):
        return input_text.isdigit()

    decimal_regex = re.compile(r"0(?:\.\d*)?")

    def decimal_num_validate(input_text):
        return decimal_regex.fullmatch(input_text) is not None

    input_row = tk.Frame(window)
    label = tk.Label(input_row, text="Side count: ", anchor='e')
    label.pack(side=tk.LEFT, padx=5)

    validate_command = input_row.register(whole_num_validate)
    cell_count_input = tk.Entry(input_row, width=12, validate="key", validatecommand=(validate_command, '%S'))
    cell_count_input.insert(0, "100")
    cell_count_input.pack(side=tk.LEFT)

    label = tk.Label(input_row, text="Entity count: ", anchor='e')
    label.pack(side=tk.LEFT, padx=5, )

    entity_count_input = tk.Entry(input_row, width=16, validate="key", validatecommand=(validate_command, '%S'))
    entity_count_input.insert(0, "12")
    entity_count_input.pack(side=tk.LEFT)

    label = tk.Label(input_row, text="Iter limit: ", anchor='e')
    label.pack(side=tk.LEFT, padx=5, )
    iter_limit_input = tk.Entry(input_row, width=16, validate="key", validatecommand=(validate_command, '%S'))
    iter_limit_input.insert(0, "0")
    iter_limit_input.pack(side=tk.LEFT)

    label = tk.Label(input_row, text="Rnd Seed: ", anchor='e')
    label.pack(side=tk.LEFT, padx=5, )

    seed_input = tk.Entry(input_row, width=16)
    seed_input.pack(side=tk.LEFT)

    seed_text_rdonly = tk.StringVar()
    label = tk.Entry(input_row, state='readonly', textvariable=seed_text_rdonly)
    label.pack(side=tk.LEFT, padx=1)

    def submit_action():
        if len(seed_input.get()) == 0:
            rnd_seed = math.floor(time.time() * 1000)
        else:
            rnd_seed = int(seed_input.get())
        seed_text_rdonly.set(str(rnd_seed))

        grow_action(int(cell_count_input.get()), int(entity_count_input.get()), int(iter_limit_input.get()), rnd_seed)

    submit = tk.Button(input_row, text="grow",
                       command=submit_action)

    submit.pack(side=tk.RIGHT)

    input_row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)


def create_grow_canvas(window):
    canvas = tk.Canvas(window, width=800, height=600, background="white")
    canvas.bind("<Button-1>", lambda c: render_grow_canvas(tri_grid, three_id_hexes, canvas))
    canvas.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
    return canvas


def render_grow_canvas(grid, hexes, canvas):
    canvas.delete("all")
    width = canvas.winfo_width() - 4
    height = canvas.winfo_height() - 4

    print(f"Rendering grow canvas at ({width},{height})")

    if coloring_solution is None:
        colors = color_palette[0:grid.seed_count()]
    else:
        colors = []
        for i in range(grid.seed_count()):
            found = False
            for c in range(len(coloring_solution)):
                if i in coloring_solution[c]:
                    colors.append(four_color_palette[c])
                    found = True
                    break

            if not found:
                colors.append(color_palette[i % len(color_palette)])

    if grid is None:
        return

    canvas.pil_image = Image.new(mode="RGB", size=(width, height), color="black")
    draw = ImageDraw.Draw(canvas.pil_image)

    x_step = width / grid.height
    y_step = height / grid.height
    for j in range(grid.height):
        x_start = width * ((grid.height - j) / (2 * grid.height))
        for i in range(j * 2 + 1):
            tri_cell = grid.get(i, j)
            m = i % 2
            if m == 0:
                coords = [x_start + (i - 1) / 2 * x_step, (j + 1) * y_step, x_start + (i + 1) / 2 * x_step,
                          (j + 1) * y_step, x_start + i / 2 * x_step, j * y_step]
            else:
                coords = [x_start + (i - 1) / 2 * x_step, j * y_step, x_start + (i + 1) / 2 * x_step, j * y_step,
                          x_start + i / 2 * x_step, (j + 1) * y_step]

            draw.polygon(coords, outline="grey" if x_step > 10 else None,
                         fill='black' if tri_cell.id is None else color_convert(colors[tri_cell.id % len(colors)]))
    # draw boundry between countries
    for j in range(grid.height):
        x_start = width * ((grid.height - j) / (2 * grid.height))
        for i in range(1, j * 2 + 1, 2):
            tri_cell = grid.get(i, j)
            l, r, v = tri_cell.lrv()
            if v is not None and v.id != tri_cell.id:
                draw.line((x_start + (i - 1) / 2 * x_step, j * y_step, x_start + (i + 1) / 2 * x_step, j * y_step),
                          fill="black")
            if l is not None and l.id != tri_cell.id:
                draw.line((x_start + (i - 1) / 2 * x_step, j * y_step, x_start + i / 2 * x_step, (j + 1) * y_step),
                          fill="black")
            if r is not None and r.id != tri_cell.id:
                draw.line(
                    (x_start + (i + 1) / 2 * x_step, j * y_step, x_start + i / 2 * x_step, (j + 1) * y_step),
                    fill="black")

    if hexes is not None:
        for hex_top in hexes:
            hex_top_x, hex_top_y = hex_top.xy()
            x_start = width * ((grid.height -  hex_top_y) / (2 * grid.height))
            y_start = hex_top_y * y_step
            coords = [x_start + x_step * (hex_top_x - 1) / 2, y_start,
                      x_start + x_step * (hex_top_x + 1) / 2, y_start,
                      x_start + x_step * (hex_top_x + 2) / 2, y_start + y_step,
                      x_start + x_step * (hex_top_x+ 1) / 2, y_start + 2 * y_step,
                      x_start + x_step * (hex_top_x - 1) / 2, y_start + 2 * y_step,
                      x_start + x_step * (hex_top_x- 2) / 2, y_start + y_step]
            draw.polygon(coords, outline='white')
            draw.text((x_start + x_step * (hex_top_x + 2) / 2, y_start + y_step),
                      f"{hex_top.state[0]},{hex_top.state[1]},{hex_top.state[2]}", fill="white")

    canvas.tk_image = ImageTk.PhotoImage(canvas.pil_image)
    canvas.create_image((2, 2), anchor=tk.NW, image=canvas.tk_image)


def create_graph_controls(window):
    input_row = tk.Frame(window)

    graph_submit = tk.Button(input_row, text="Graph", command=graph_action)
    graph_submit.pack(side=tk.LEFT, padx=3)

    hex_submit = tk.Button(input_row, text="Find 3 hexes", command=hex_action)
    hex_submit.pack(side=tk.LEFT, padx=30)

    algo_selection = tk.StringVar()

    def submit_action():
        color_action(algo_selection.get())

    color_submit = tk.Button(input_row, text="Color", command=submit_action)
    color_submit.pack(side=tk.RIGHT, padx=3)
    options = [x[9:] for x in filter(lambda a: a.startswith("coloring"), dir(sv))]
    algo_selection.set(options[0])
    popup_menu = tk.OptionMenu(input_row, algo_selection, *options)
    popup_menu.pack(side=tk.RIGHT, padx=3)

    input_row.pack(side=tk.TOP,
                   fill=tk.X,
                   padx=5,
                   pady=5)


def render_graph_canvas(graph, model, canvas):
    global coloring_solution
    fig = canvas.figure
    fig.clear()

    if coloring_solution is None:
        colors = [color_palette[a % len(color_palette)] for a in range(len(graph.nodes))]
    else:
        colors = []
        for i in range(len(graph.nodes)):
            found = False
            for c in range(len(coloring_solution)):
                if i in coloring_solution[c]:
                    colors.append(four_color_palette[c])
                    found = True
                    break

            if not found:
                colors.append(color_palette[i % len(color_palette)])

    options = {
        "node_size": 200,
        "edgecolors": (.5, .5, .5, .5),
        "linewidths": 3,
        "width": 2,
        "node_color": colors,
        "font_size": 7,
        "font_color": "black",
        "with_labels": True,
    }

    ax1 = fig.add_subplot()

    nx.draw_kamada_kawai(graph, **options, ax=ax1)

    plt.tight_layout(pad=.1)
    canvas.draw()


def render_hex_canvas(graph, canvas):
    fig = canvas.figure
    fig.clear()

    pos = nx.kamada_kawai_layout(graph)

    ax2 = fig.add_subplot()

    nx.draw_networkx_nodes(graph, pos, node_size=200, node_color=[(.85, .9, 1)], edgecolors=(.5, .5, .5, .5), ax=ax2)
    nx.draw_networkx_edges(graph, pos, edge_color=(.5, .5, .5, .5), ax=ax2)
    nx.draw_networkx_labels(graph, pos, font_size=6, ax=ax2)

    plt.tight_layout(pad=.1)
    canvas.draw()


def create_graph_canvas(window):
    fig1 = plt.figure()
    canvas1 = FigureCanvasTkAgg(fig1, master=window)

    def callback(event):
        plt.show()

    fig1.canvas.callbacks.connect('button_press_event', callback)

    fig2 = plt.figure()
    canvas2 = FigureCanvasTkAgg(fig2, master=window)

    fig2.canvas.callbacks.connect('button_press_event', callback)

    canvas1.get_tk_widget().pack(side=tk.LEFT, expand=True, fill=tk.X)
    canvas2.get_tk_widget().pack(side=tk.RIGHT, expand=True, fill=tk.X)
    return canvas1, canvas2


def grow_action(side_length, entity_count, iter_limit, seed):
    global tri_grid
    global graph_model
    global three_id_hexes
    global hex_graph
    global coloring_solution

    tri_grid = tg.TriGrid(side_length)
    graph_model = None
    three_id_hexes = None
    hex_graph = None
    coloring_solution = None

    gr.generate(entity_count, tri_grid, iter_limit, seed)
    render_grow_canvas(tri_grid, three_id_hexes, grow_canvas)


def graph_action():
    global tri_grid
    global graph_model
    if tri_grid is None:
        tk.messagebox.showinfo(title="Graph not ready", message="Must grow a map before converting to graph")
        return
    graph_model = sv.build_graph(tri_grid)
    render_graph_canvas(graph_model, tri_grid, graph_canvas)


def hex_action():
    global tri_grid
    global graph_model
    global three_id_hexes
    global hex_graph
    if graph_model is None:
        graph_action()
    three_id_hexes = sv.find_3_color_hexes(tri_grid)
    render_grow_canvas(tri_grid, three_id_hexes, grow_canvas)

    hex_graph = sv.find_two_color_linked_hex_graph(three_id_hexes)
    render_hex_canvas(hex_graph, hex_canvas)


def color_action(algo_name: str):
    global tri_grid
    global graph_model
    global three_id_hexes
    global hex_graph
    global coloring_solution
    if hex_graph is None:
        hex_action()

    coloring_solution = eval("sv.coloring_" + algo_name + "(tri_grid,hex_graph)")

    render_grow_canvas(tri_grid, three_id_hexes, grow_canvas)
    render_graph_canvas(graph_model, tri_grid, graph_canvas)


if __name__ == '__main__':
    print("Initializing application")
    window = create_main_window()
    grow_frame = tk.LabelFrame(window, text="Generation")
    grow_frame.pack(side=tk.TOP, padx=3, pady=3, expand=True, fill=tk.BOTH)
    create_grow_controls(grow_frame)
    grow_canvas = create_grow_canvas(grow_frame)
    graph_frame = tk.LabelFrame(window, text="Graph Coloring")
    graph_frame.pack(side=tk.BOTTOM, padx=3, pady=3, expand=False, fill=tk.X)
    create_graph_controls(graph_frame)
    graph_canvas, hex_canvas = create_graph_canvas(graph_frame)
    window.mainloop()
