import tkinter as tk
import re
from PIL import Image, ImageTk, ImageDraw
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

import seaborn as sns

import grow as gr
import trigrid as tg
import solve as sv

matplotlib.use("TkAgg")

color_palette = sns.color_palette("pastel") + sns.color_palette('bright')


def get_color(i):
    return color_convert(color_palette[i])


def color_convert(color):
    # return f"#{int(255 * color[0]):02X}{int(255 * color[1]):02X}{int(255 * color[2]):02X}"
    return int(255 * color[0]), int(255 * color[1]), int(255 * color[2])


tri_grid = None
graph_model = None


# The main window of the animation
def create_main_window():
    main_window = tk.Tk()
    main_window.title("Coloring")

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
    cell_count_input.insert(0, "40")
    cell_count_input.pack(side=tk.LEFT)

    label = tk.Label(input_row, text="Seed count: ", anchor='e')
    label.pack(side=tk.LEFT, padx=5, )

    seed_count_input = tk.Entry(input_row, width=16, validate="key", validatecommand=(validate_command, '%S'))
    seed_count_input.insert(0, "8")
    seed_count_input.pack(side=tk.LEFT)

    label = tk.Label(input_row, text="Iter limit: ", anchor='e')
    label.pack(side=tk.LEFT, padx=5, )
    iter_limit_input = tk.Entry(input_row, width=16, validate="key", validatecommand=(validate_command, '%S'))
    iter_limit_input.insert(0, "0")
    iter_limit_input.pack(side=tk.LEFT)

    def submit_action():
        grow_action(int(cell_count_input.get()), int(seed_count_input.get()), int(iter_limit_input.get()))

    submit = tk.Button(input_row, text="grow",
                       command=submit_action)

    submit.pack(side=tk.RIGHT)

    input_row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)


def create_grow_canvas(window):
    canvas = tk.Canvas(window, width=800, height=400, background="white")
    canvas.bind("<Button-1>", lambda c: render_grow_canvas(tri_grid, canvas))
    canvas.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
    return canvas


def render_grow_canvas(grid, canvas):
    canvas.delete("all")
    width = canvas.winfo_width() - 4
    height = canvas.winfo_height() - 4

    print(f"Rendering grow canvas at ({width},{height})")

    if grid is None:
        return

    canvas.pil_image = Image.new(mode="RGB", size=(width, height), color="white")
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
            draw.polygon(coords,
                         fill='black' if tri_cell.id is None else get_color(tri_cell.id))
            # outline='black' if tri_cell.id is None else get_color(tri_cell.id))

    canvas.tk_image = ImageTk.PhotoImage(canvas.pil_image)

    # canvas.pil_image.show()

    canvas.create_image((2, 2), anchor=tk.NW, image=canvas.tk_image)


def create_graph_controls(window):
    input_row = tk.Frame(window)

    graph_submit = tk.Button(input_row, text="Graph", command=graph_action)
    graph_submit.pack(side=tk.LEFT, padx=3)

    color_submit = tk.Button(input_row, text="Color", command=color_action)
    color_submit.pack(side=tk.RIGHT, padx=3)

    input_row.pack(side=tk.TOP,
                   fill=tk.X,
                   padx=5,
                   pady=5)


def render_graph_canvas(graph, model, canvas):
    fig = canvas.figure
    fig.clear()
    options = {
        "node_size": 400,
        "edgecolors": (.5, .5, .5, .5),
        "linewidths": 3,
        "width": 2,
        "node_color": color_palette[0:model.seed_count()]

    }

    ax1 = fig.add_subplot()

    nx.draw_kamada_kawai(graph, **options, ax=ax1)

    plt.tight_layout(pad=.1)
    canvas.draw()


def render_coloring_canvas(graph, mapping, canvas):
    fig = canvas.figure
    fig.clear()
    id_to_color = [None] * graph.number_of_nodes()
    for coloring, ids in mapping.items():
        for id in ids:
            id_to_color[id] = color_palette[coloring]

    options = {
        "node_size": 400,
        "edgecolors": (.5, .5, .5, .5),
        "linewidths": 3,
        "width": 2,
        "node_color": id_to_color
    }

    ax2 = fig.add_subplot()

    nx.draw_kamada_kawai(graph, **options, ax=ax2)

    plt.tight_layout(pad=.1)
    canvas.draw()


def create_graph_canvas(window):
    fig1 = plt.figure(figsize=(5, 4))
    canvas1 = FigureCanvasTkAgg(fig1, master=window)
    fig2 = plt.figure(figsize=(5, 4))
    canvas2 = FigureCanvasTkAgg(fig2, master=window)

    # canvas.bind("<Configure>", lambda c: render_graph_canvas(tri_grid, canvas))
    canvas1.get_tk_widget().pack(side=tk.LEFT, expand=True, fill=tk.X)
    canvas2.get_tk_widget().pack(side=tk.RIGHT, expand=True, fill=tk.X)
    return canvas1,canvas2


def grow_action(side_length, seed_count, iter_limit):
    global tri_grid
    global graph_model
    tri_grid = tg.TriGrid(side_length)
    gr.generate(seed_count, tri_grid, iter_limit)
    render_grow_canvas(tri_grid, grow_canvas)
    graph_model = None


def graph_action():
    global tri_grid
    global graph_model
    if tri_grid is None:
        tk.messagebox.showinfo(title="Graph not ready", message="Must grow a map before converting to graph")
        return
    graph_model = sv.build_graph(tri_grid)
    render_graph_canvas(graph_model, tri_grid, graph_canvas)


def color_action():
    global tri_grid
    global graph_model
    if graph_model is None:
        graph_action()
    color_map = sv.directional_color_map(tri_grid)
    render_coloring_canvas(graph_model, color_map, color_canvas)


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
    graph_canvas,color_canvas = create_graph_canvas(graph_frame)
    window.mainloop()
