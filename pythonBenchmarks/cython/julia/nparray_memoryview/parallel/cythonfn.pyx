#cython: boundscheck=False
from cython.parallel import parallel, prange
import numpy as np
cimport numpy as np

def calculate_z(int maxiter, double complex[:] zs, double complex cs):
    """Calculate output list using Julia update rule"""
    cdef unsigned int i, length
    cdef double complex z
    cdef int[:] output = np.empty(len(zs), dtype=np.int32)
    length = len(zs)
    with nogil, parallel():
        for i in prange(length, schedule="guided"):
            z = zs[i]

            output[i] = 0
            while output[i] < maxiter and (z.real * z.real + z.imag * z.imag) < 4:
                z = z * z + cs
                output[i] += 1
    return output
