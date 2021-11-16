cython: boundscheck=False
import numpy as np
cimport numpy as np


def forward_fill_cython(np.ndarray[np.float64_t, ndim=1] fill_value_map, np.ndarray[np.uint8_t, ndim=1] symbol_block, np.ndarray[np.float64_t, ndim=1] price_block):
    cdef int end = len(price_block)
    cdef double n_a_n = np.nan
    cdef unsigned char symbol_id
    with nogil:
        for i in range(end):
            symbol_id = symbol_block[i]
            if price_block[i] == n_a_n:
                price_block[i] = fill_value_map[symbol_id]
            else:
                fill_value_map[symbol_id] = price_block[i]



