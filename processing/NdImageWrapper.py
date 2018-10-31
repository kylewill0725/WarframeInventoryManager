"""
The purpose of this class is to keep images in a convenient format (arrays with [x][y] indices)
while still functioning with opencv image requirements (arrays with [y][x] indices).
"""
import numpy as np


class ndimage():
    def __init__(self, img: np.ndarray):
        self._img = img

    def to_ndarray(self):
        return self._img
