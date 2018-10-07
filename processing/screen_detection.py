"""
Detects the resolution and theme of Warframe
"""
from enum import IntEnum, auto

import numpy as np


"""
Image Width, Image Height, TL X, TL Y, Width, Height, Gap X, Gap Y
1280, 720, 67, 135, 108, 109, 23, 24
1366, 768, 71, 144, 116, 115, 27, 27
1600, 900, 82, 168, 136, 137, 31, 31
1920, 1080, 99, 201, 165, 165, 35, 35
2048, 1152, 105, 214, 177, 176, 36, 36
"""


class Themes(IntEnum):
    HIGH_CONTRAST = auto()


def get_theme(page: np.ndarray):
    """
    Gets the theme of an image as an enum.
    :param page:
    :return:
    """
    return Themes.HIGH_CONTRAST


class ScreenInfo:
    def __init__(self, page: np.ndarray):
        self.x = page.shape[1]
        self.y = page.shape[0]
        self.theme = get_theme(page)
