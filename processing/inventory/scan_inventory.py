import numpy as np

from processing.screen_detection import ScreenInfo


def scan_inventory_names(item_pages: np.ndarray):
    """
    :param item_pages: Numpy array of inventory screenshots in BGR
    :return: List of item names
    """
    for item_page in item_pages:
        screen_info = ScreenInfo(item_page)
        item_name_imgs = get_item_image_list(screen_info)

        for item in item_name_imgs:
            try_read_name(item)


