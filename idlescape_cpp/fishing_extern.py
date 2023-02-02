import ctypes as ct
import os
import numpy as np
from glob import glob

c_int = ct.c_int
c_double = ct.c_double
c_float = ct.c_float
c_void_p = ct.c_void_p
c_char_p = ct.c_char_p
c_double_pointer = ct.POINTER(c_double)
c_int_pointer = ct.POINTER(c_int)
libname = glob(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fishing.*.so')
)[0]

class fishing_extern:
    def __init__(self):
        self.lib = ct.cdll.LoadLibrary(libname)
        self._init_functions()

    def _init_functions(self):
        self._calc_resources = self.lib.calc_resources
        self._calc_resources.restype = c_double
        self._calc_resources.argtypes = [c_int, c_int, c_int, c_double, c_double, c_int]

        self._average_trials = self.lib.average_trials
        self._average_trials.restype = c_double
        self._average_trials.argtypes = [c_double, c_int, c_int, c_int, c_double, c_double, c_int, c_int]

    def calc_resources(self, zone_level, min_base, max_base, fishing_level, bait_power, trials):
        return self._calc_resources(zone_level, min_base, max_base, fishing_level, bait_power, trials)

    def average_trials(self, base_chance, zone_level, min_base, max_base, fishing_level, bait_power, fishing, trials):
        return self._average_trials(base_chance, zone_level, min_base, max_base, fishing_level, bait_power, fishing, trials)
