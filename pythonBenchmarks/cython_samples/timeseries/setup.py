# from distutils.core import setup
# import numpy as np
#
# from Cython.Build import cythonize
# setup(ext_modules=cythonize("forward_fill.pyx", compiler_directives={"language_level": "3"}),
#         include_dirs=[np.get_include()])

from setuptools import setup
from Cython.Build import cythonize
import Cython.Compiler.Options
import numpy as np

Cython.Compiler.Options.annotate = True

setup(
    ext_modules=cythonize("forward_fill.pyx",compiler_directives={"language_level": "3"},annotate = True),
    include_dirs=[np.get_include()],
)
