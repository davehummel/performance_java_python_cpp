"""Julia set generator without optional PIL-based image drawing"""
import time
# from cythonfn import calculate_z
import cythonfn

# area of complex space to investigate
x1, x2, y1, y2 = -1.8, 1.8, -1.8, 1.8
c_real, c_imag = -0.62772, -.42193


def calc_pure_python(desired_width, max_iterations):
    """Create a list of complex co-ordinates (zs) and complex parameters (cs), build Julia set and display"""
    # refactored from book example to something without float error accumulation issues

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
    cs = []
    for ycoord in y:
        for xcoord in x:
            zs.append(complex(xcoord, ycoord))
            cs.append(complex(c_real, c_imag))

    print("Length of x:", len(x))
    print("Total elements:", len(zs))
    start_time = time.time()
    output = cythonfn.calculate_z(max_iterations, zs, cs)
    end_time = time.time()
    secs = end_time - start_time
    print(f"Took {secs:0.2f} seconds")

    print(sum(output))  # this sum is expected for 1000^2 grid with 300 iterations


# Calculate the Julia set using a pure Python solution with
# reasonable defaults for a laptop
calc_pure_python(desired_width=4000, max_iterations=300)
