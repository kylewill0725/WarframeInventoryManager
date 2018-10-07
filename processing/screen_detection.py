"""
Detects the resolution and theme of Warframe
"""
from enum import IntEnum, auto

import numpy as np


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
