"""Julia set generator without optional PIL-based image drawing"""
import numba
from matplotlib import pyplot as plt
from numba import jit
import time
import numpy as np

# area of complex space to investigate
from numba import cuda

x1, x2, y1, y2 = -1.8, 1.8, -1.8, 1.8
c_real, c_imag = -0.62772, -.42193


@cuda.jit
def calculate_z(maxiter, zs, c, output):
    """Calculate output list using Julia update rule"""

    i = cuda.threadIdx.x + cuda.blockIdx.x * cuda.blockDim.x

    n = 0
    z = zs[i]

    while n < maxiter and (z.real * z.real + z.imag * z.imag) < 4:
        z = z * z + c
        n += 1
    output[i] = n


def calc_cuda(desired_width, max_iterations):
    """Create a list of complex co-ordinates (zs) and complex parameters (cs), build Julia set and display"""
    x = []
    for i in range(desired_width):
        x.append((x1 * desired_width + (x2 - x1) * float(i)) / desired_width)

    y = []
    for i in range(desired_width):
        y.append((y1 * desired_width + (y2 - y1) * float(i)) / desired_width)

    # build a list of co-ordinates and the initial condition for each cell.
    # Note that our initial condition is a constant and could easily be removed,
    # we use it to simulate a real-world scenario with several inputs to our function
    zs = []

    for ycoord in y:
        for xcoord in x:
            zs.append(complex(xcoord, ycoord))

    print("Length of x:", len(x))
    print("Total elements:", len(zs))
    zs2 = np.array(zs, np.complex128)
    device_input = cuda.to_device(zs2)
    output = np.zeros_like(zs2, dtype=np.uint16)
    blockdim = 512
    griddim = (desired_width * desired_width) // blockdim
    start_time = time.time()
    device_output = cuda.to_device(output)
    calculate_z[griddim, blockdim](max_iterations, device_input, complex(c_real, c_imag), device_output)
    device_output.copy_to_host(output);
    end_time = time.time()
    secs = end_time - start_time
    print("took", secs, "seconds")

    print("Doing second run to test warm-up")
    start_time = time.time()
    device_output = cuda.to_device(output)
    calculate_z[griddim, blockdim](max_iterations, device_input, complex(c_real, c_imag), device_output)
    device_output.copy_to_host(output);
    end_time = time.time()
    secs = end_time - start_time
    print("took", secs, "seconds")

    print("Doing third run to test warm-up")
    start_time = time.time()
    device_output = cuda.to_device(output)
    calculate_z[griddim, blockdim](max_iterations, device_input, complex(c_real, c_imag), device_output)
    device_output.copy_to_host(output);
    end_time = time.time()
    secs = end_time - start_time
    print("took", secs, "seconds")

    validation_sum = sum(output)
    print("Total sum of elements (for validation):", validation_sum)
    image = output.reshape(-1, desired_width)
    plt.imsave(fname="julia_cuda.png", arr=image)
    with open("julia_cuda_jit_output.txt", "w") as file_out:
        calculate_z.inspect_types(file_out)


# Calculate the Julia set using a pure Python solution with
# reasonable defaults for a laptop
# set draw_output to True to use PIL to draw an image
calc_cuda(desired_width=4000, max_iterations=300)
