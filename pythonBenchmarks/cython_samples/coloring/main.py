import tkinter as tk
import re

import grow
# width of the animation window
window_width = 510
# height of the animation window
window_height = 1200


# The main window of the animation
def create_main_window():
    window = tk.Tk()
    # window.geometry(f'{window_width}x{window_height}')
    window.title("Coloring")

    return window


def create_grow_controls(window):
    def whole_num_validate(input_text):
        return input_text.isdigit()

    decimal_regex = re.compile(r"0(?:\.\d*)?")
    def decimal_num_validate(input_text):
        return decimal_regex.fullmatch(input_text) is not None

    input_row = tk.Frame(window)
    label = tk.Label(input_row,  text="Cell count: ", anchor='w')
    label.pack(side=tk.LEFT)

    validate_command = input_row.register(whole_num_validate)
    cell_count_input = tk.Entry(input_row,width=16,validate="key",validatecommand=(validate_command, '%S'))
    cell_count_input.insert(0,"0")
    cell_count_input.pack(side=tk.LEFT)

    label = tk.Label(input_row, text="Random influence [0-1): ", anchor='w')
    label.pack(side=tk.LEFT)

    validate_command = input_row.register(decimal_num_validate)
    random_prob_input = tk.Entry(input_row,width=16,validate="key",validatecommand=(validate_command, '%S'))
    random_prob_input.insert(0,"0.0")
    random_prob_input.pack(side=tk.LEFT)


    submit = tk.Button(input_row, text="grow" )
    submit.pack(side=tk.RIGHT)

    submit['command'] = grow.generate(count = int(cell_count_input.get()), random = float(random_prob_input.get()))

    input_row.pack(side=tk.TOP,
             fill=tk.X,
             padx=5,
             pady=5)



def create_grow_canvas(window):
    canvas = tk.Canvas(window, width= 500, height= 500, background= "#000000")
    canvas.configure()
    canvas.pack(side = tk.TOP, expand=False)
    return canvas

def create_graph_controls(window):

    input_row = tk.Frame(window)

    submit = tk.Button(input_row, text="Graph" )
    submit.pack(side=tk.LEFT,padx = 3)

    submit = tk.Button(input_row, text="Color" )
    submit.pack(side=tk.LEFT,padx = 3)


    input_row.pack(side=tk.TOP,
             fill=tk.X,
             padx=5,
             pady=5)



def create_graph_canvas(window):
    canvas = tk.Canvas(window, width= 500, height= 500, background= "#000000")
    canvas.configure()
    canvas.pack(side = tk.TOP, expand=False)
    return canvas



if __name__ == '__main__':
    print("Initializing application")
window = create_main_window()
grow_frame = tk.LabelFrame(window,text="Generation")
grow_frame.pack(side = tk.TOP,padx = 3, pady = 3)
create_grow_controls(grow_frame)
create_grow_canvas(grow_frame)
graph_frame = tk.LabelFrame(window,text="Graph Coloring")
graph_frame.pack(side = tk.TOP,padx = 3, pady = 3)
create_graph_controls(graph_frame)
create_graph_canvas(graph_frame)
window.mainloop()

