cython: boundscheck=False
import numpy as np
cimport numpy as np


def bulk_forward_fill(start_index: int, block_size:int, symbol_count: int,np.uint8_t[:] symbol_array, double[:] price_array):
    cdef np.ndarray[np.float64_t, ndim=1] fill_value_map = np.empty(symbol_count, dtype = np.double)
    fill_value_map[:] = np.NaN
    cdef int i = start_index
    cdef int end = start_index + block_size
    cdef double n_a_n = np.nan
    cdef unsigned char symbol_id
    with nogil:
        while i < end:
            symbol_id = symbol_array[i]
            if price_array[i] == n_a_n:
                price_array[i] = fill_value_map[symbol_id]
            else:
                fill_value_map[symbol_id] = price_array[i]
            i= i + 1

    return fill_value_map


# def bulk_forward_fill(start_index: int, block_size:int, symbol_count: int,np.ndarray[np.uint8_t, ndim=1] symbol_array, np.ndarray[np.float64_t, ndim=1] price_array):
#     cdef np.ndarray[np.float64_t, ndim=1] fill_value_map = np.empty(symbol_count, np.double)
#     fill_value_map[:] = np.NaN
#     for i in range(start_index, start_index + block_size):
#         symbol_id = symbol_array[i]
#         if np.isnan(price_array[i]):
#             price_array[i] = fill_value_map[symbol_id]
#         else:
#             fill_value_map[symbol_id] = price_array[i]
#
#     return fill_value_map
