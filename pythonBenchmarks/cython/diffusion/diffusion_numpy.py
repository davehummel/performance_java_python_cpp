import time
from PIL import Image, ImageDraw
from matplotlib import cm

import numpy as np

from numexpr import evaluate, set_num_threads
from numpy import copyto, multiply, zeros

import simp

simp.add(1,2)

try:
    profile
except NameError:
    profile = lambda x: x

grid_shape = (1024, 1024)
render_gif = False
if render_gif:
    images = []


def sumCheck(grid):
    sum = 0.0
    for x in range(grid_shape[0]):
        for y in range(grid_shape[1]):
            sum = sum + grid[x, y] * (x + y)
    return sum


def roll_add(rollee, shift, axis, out):
    if shift == 1 and axis == 0:
        out[1:, :] += rollee[:-1, :]
        out[0, :] += rollee[-1, :]
    elif shift == -1 and axis == 0:
        out[:-1, :] += rollee[1:, :]
        out[-1, :] += rollee[0, :]
    elif shift == 1 and axis == 1:
        out[:, 1:] += rollee[:, :-1]
        out[:, 0] += rollee[:, -1]
    elif shift == -1 and axis == 1:
        out[:, :-1] += rollee[:, 1:]
        out[:, -1] += rollee[:, 0]


def laplacian(grid, out):
    copyto(out, grid)
    multiply(out, -4.0, out)
    roll_add(grid, +1, 0, out)
    roll_add(grid, -1, 0, out)
    roll_add(grid, +1, 1, out)
    roll_add(grid, -1, 1, out)


@profile
def evolve(grid, out, dt, D=1):
    laplacian(grid, out)
    evaluate("out*D*dt+grid", out=out)


def render_grid(grid):
    img = Image.fromarray(np.uint8((cm.gist_heat(grid) * 255)))
    return img


def run_experiment(num_iterations):
    previous_threads = set_num_threads(8)
    scratch = np.zeros(grid_shape)
    grid = np.zeros(grid_shape)

    block_low = int(grid_shape[0] * 0.4)
    block_high = int(grid_shape[0] * 0.5)
    grid[block_low:block_high, block_low:block_high] = 1
    if render_gif:
        images.append(render_grid(grid))

    start = time.time()
    for i in range(num_iterations):
        evolve(grid, scratch, .2)
        grid, scratch = scratch, grid
        if render_gif:
            images.append(render_grid(grid))

    run_time = time.time() - start
    set_num_threads(previous_threads)
    print("Sum Check:", sumCheck(grid))
    return run_time


print(run_experiment(5000))
if render_gif:
    images[0].save('anim.apng', save_all=True, append_images=images[1:], optimize=True, duration=2, loop=0)

exit()
