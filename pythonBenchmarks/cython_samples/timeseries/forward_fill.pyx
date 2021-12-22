#cython: boundscheck=False,

import numpy as np
cimport numpy as np

def forward_fill_cython(int start,int end,np.ndarray[np.float64_t, ndim=1]  fill_value_map, np.float64_t[:] price_block,np.uint8_t[:] symbol_block):
    cdef unsigned char symbol_id


    with nogil:
        for i in range(end):
            symbol_id = symbol_block[i]
            if price_block[i] == 0:
                price_block[i] = fill_value_map[symbol_id]
            else:
                fill_value_map[symbol_id] = price_block[i]



