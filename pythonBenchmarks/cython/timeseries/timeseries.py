import time
import ctypes
import multiprocessing
from functools import wraps, partial
from forward_fill import bulk_forward_fill

import numpy as np
import pandas as pd


def timed_void_fn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        out = fn(*args, **kwargs)
        if out is None:
            return time.time() - t1
        else:
            return out, time.time() - t1

    return measure_time


ITEMS_IN_ARRAY = 100_000_000
BLOCK_SIZE = 1_000_000

PROCESS_COUNT = 16


def explode_symbols(symbols):
    symbol_id = 0;
    for symbol in symbols:
        for i in range(symbol[1]):
            yield symbol_id, symbol[0]
        for i in range(symbol[2]):
            yield symbol_id, None
        symbol_id = symbol_id + 1


# Symbol tuple is (avg price, weighted prob of price update, weighted prob of as of request)
SYMBOLS = [(149.50, 13, 18), (119.33, 2, 1), (29.44, 9, 5), (6.60, 5, 10), (894, 20, 10)]

EXPLODED_SYMBOL_IDS = np.asarray([v[0] for v in list(explode_symbols(SYMBOLS))], dtype=np.uint8)
EXPLODED_SYMBOL_PRICES = np.asarray([v[1] for v in list(explode_symbols(SYMBOLS))], dtype=np.double)


@timed_void_fn
def build_local_times(start_index: int):
    random = np.random.lognormal(mean=2, sigma=.5, size=BLOCK_SIZE).astype(np.int64)
    random.cumsum(out=main_array[start_index:start_index + BLOCK_SIZE])
    boundary_array[start_index // BLOCK_SIZE] = main_array[start_index + BLOCK_SIZE - 1];


@timed_void_fn
def broadcast_boundary_times(start_index: int):
    boundary_value = boundary_array[start_index // BLOCK_SIZE - 1]
    np.add(main_array[start_index:start_index + BLOCK_SIZE], boundary_value,
           out=main_array[start_index:start_index + BLOCK_SIZE])


@timed_void_fn
def generate_symbol_prices(start_index: int):
    random = np.random.randint(0, len(EXPLODED_SYMBOL_IDS), size=BLOCK_SIZE)
    np.take(EXPLODED_SYMBOL_IDS, random, out=symbol_array[start_index:start_index + BLOCK_SIZE])
    price_variance = np.random.uniform(.8, 1.2, size=BLOCK_SIZE)
    np.take(EXPLODED_SYMBOL_PRICES, random, out=price_array[start_index:start_index + BLOCK_SIZE])
    np.multiply(price_variance, price_array[start_index:start_index + BLOCK_SIZE],
                out=price_array[start_index:start_index + BLOCK_SIZE])


# @timed_void_fn
# def bulk_forward_fill(start_index: int):
#     fill_value_map = np.empty(len(SYMBOLS), np.double)
#     fill_value_map[:] = np.NaN
#     for i in range(start_index, start_index + BLOCK_SIZE):
#         symbol_id = symbol_array[i]
#         if np.isnan(price_array[i]):
#             price_array[i] = fill_value_map[symbol_id]
#         else:
#             fill_value_map[symbol_id] = price_array[i]
#
#     return fill_value_map


@timed_void_fn
# @nb.jit(nopython=True)
def boundary_forward_fill(start_index: int, last_value_maps):
    last_value_map = last_value_maps[start_index // BLOCK_SIZE - 1]
    known_fills = np.empty(len(SYMBOLS), bool)
    known_fills[:] = False
    for i in range(start_index, start_index + BLOCK_SIZE):
        symbol_id = symbol_array[i]
        if np.isnan(price_array[i]):
            price_array[i] = last_value_map[symbol_id]
        else:
            if not known_fills[symbol_id]:
                known_fills[symbol_id] = True
                if sum(known_fills == False) == 0:
                    return


if __name__ == '__main__':
    print("Creating Arrays")

    main_array_base = multiprocessing.Array(ctypes.c_int64, ITEMS_IN_ARRAY, lock=False)
    symbol_array_base = multiprocessing.Array(ctypes.c_int8, ITEMS_IN_ARRAY, lock=False)
    price_array_base = multiprocessing.Array(ctypes.c_double, ITEMS_IN_ARRAY, lock=False)

    boundary_array_base = multiprocessing.Array(ctypes.c_int64, ITEMS_IN_ARRAY // BLOCK_SIZE, lock=False)

    main_array = np.frombuffer(main_array_base, dtype=ctypes.c_int64)
    symbol_array = np.frombuffer(symbol_array_base, dtype=ctypes.c_uint8)
    price_array = np.frombuffer(price_array_base, dtype=ctypes.c_double)

    boundary_array = np.frombuffer(boundary_array_base, dtype=ctypes.c_int64)

    worker_pool = multiprocessing.Pool(processes=PROCESS_COUNT)

    print("Running build_local_times")
    stage_start_time = start_time = time.time()
    worker_pool.map(build_local_times, range(0, ITEMS_IN_ARRAY, BLOCK_SIZE))
    print(time.time() - stage_start_time)

    print("Running broadcast_boundary_times")
    stage_start_time = time.time()
    boundary_array.cumsum(out=boundary_array)
    worker_pool.map(broadcast_boundary_times, range(BLOCK_SIZE, ITEMS_IN_ARRAY, BLOCK_SIZE))
    print(time.time() - stage_start_time)

    print("Running generate_symbol_prices")
    stage_start_time = time.time()
    worker_pool.map(generate_symbol_prices, range(0, ITEMS_IN_ARRAY, BLOCK_SIZE))
    print(time.time() - stage_start_time)
    print("Running bulk_forward_fill")
    stage_start_time = time.time()
    closure = partial(bulk_forward_fill, block_size=BLOCK_SIZE, symbol_count=int(len(SYMBOLS)), symbol_array=symbol_array,
                      price_array=price_array)
    bulk_out = worker_pool.map(closure, range(0, ITEMS_IN_ARRAY, BLOCK_SIZE))
    last_value_maps = [p[0] for p in bulk_out]
    print(time.time() - stage_start_time)
    closure = partial(boundary_forward_fill, last_value_maps=last_value_maps)
    print("Running boundary_forward_fill")
    stage_start_time = time.time()
    worker_pool.map(closure, range(BLOCK_SIZE, ITEMS_IN_ARRAY, BLOCK_SIZE))
    print(time.time() - stage_start_time)
    print(f"total time = {time.time() - start_time} seconds")

    # input("Press a key to exit...")
