import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Tuple

import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageFile


@dataclass
class TessData:
    result: str = ""
    level: str = ""
    page_num: int = ""
    block_num: int = 0
    paragraph_num: int = 0
    line_num: int = 0
    word_num: int = 0
    left: int = 0
    top: int = 0
    right: int = field(init=False)
    bottom: int = field(init=False)
    width: int = 0
    height: int = 0
    confidence: int = -1

    def __post_init__(self):
        self.right = self.left + self.width
        self.bottom = self.top + self.height

    def tostring(self):
        return f'{self.result}	{self.left}	{self.top}	{self.right}	{self.bottom}	' \
               + f'{self.confidence}'


class TessDataParser:
    def __init__(self, tess_result):
        (self.data, self.failed_data) = TessDataParser.parse(tess_result)

    @staticmethod
    def parse(tess_result: str):
        data = []
        failed_data = []
        rows = tess_result.split("\n")
        for row in rows:
            columns = row.split("\t")
            if columns[0].isdigit():
                tess = TessData(columns[-1], *[int(x) for x in columns[:-1]])
                if tess.confidence >= 0:
                    if tess.confidence >= 75:
                        match = re.match("[a-zA-Z0-9 &]+", tess.result)
                        if match is not None:
                            data.append(tess)
                        else:
                            failed_data.append(tess)
                    else:
                        failed_data.append(tess)
            pass

        return data, failed_data


@dataclass
class InventoryImageInfo:
    image: np.ndarray
    top_left_corner_x: int
    top_left_corner_y: int
    name_field_width: int
    name_field_height: int
    item_gap_x: int  # (x_gap, y_gap) in pixels from the corner of one item to the same corner of the next
    item_gap_y: int
    column_count: int
    row_count: int


def add_border(img: np.ndarray, pixels=0, multiplier=1.0):
    border_size = (np.array([img.shape[1], img.shape[0]]) * max(0., multiplier - 1) + pixels).astype(np.uint32)
    new_img = cv2.copyMakeBorder(img, border_size[1], border_size[1], border_size[0], border_size[0],
                                 cv2.BORDER_CONSTANT, value=(255, 255, 255))
    return new_img, (border_size[0], border_size[1])


def crop_failed_image(img: np.ndarray, failed_data: TessData):
    result = NdImage.crop(img, (
        failed_data.top,
        failed_data.left,
        failed_data.bottom,
        failed_data.right
    ))
    return result


def get_tess_data(img):
    data = pytesseract.image_to_data(img, config="-c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN" +
                                                 "OPQRSTUVWXYZ&")
    tess_data = TessDataParser(data)
    return tess_data


class BBoxes(Enum):
    LINE = 50
    WORD = 20
    LETTER = 0


def contour_bound_boxes(contours, selection: BBoxes = BBoxes.LINE):
    if len(contours) < 2:
        return [(0, 0, 0, 0)]

    boxes = []
    for cnt in contours[:-1]:
        bb = list(cv2.boundingRect(cnt))
        bb[2] += bb[0]
        bb[3] += bb[1]
        boxes.append(bb)
    boxes.sort(key=lambda x: x[0])

    result = [boxes[0]]
    for i in range(len(boxes[1:])):
        box = boxes[i]
        x_spacing = box[0] - result[-1][2]
        if x_spacing >= selection.value:
            result.append(box)
        else:
            result[-1] = (
                min(result[-1][0], box[0]),
                min(result[-1][1], box[1]),
                max(result[-1][2], box[2]),
                max(result[-1][3], box[3])
            )

    return result


def try_read_words(img: np.ndarray, failed_data):
    results = []
    failed_words = []

    eImg, contours, hierarchy = cv2.findContours(img, 1, 3)
    word_bounds = contour_bound_boxes(contours, BBoxes.WORD)

    for b in word_bounds:
        cropped_image, border_size = add_border(NdImage.crop(img, (b[1], b[0], b[3], b[2])), multiplier=1.1)
        data = get_tess_data(cropped_image)
        for d in data.data:
            results.append(d.result)
        if len(data.data) == 0:
            failed_words.append(b)

    return results, failed_words


def undo_word_wrap(img: np.ndarray):
    top_name_img = NdImage.crop(img, (0, 0, math.floor(img.shape[0] / 2.0), img.shape[1]))
    bot_name_img = NdImage.crop(img, (img.shape[0] - top_name_img.shape[0], 0, img.shape[0], img.shape[1]))
    imgs = [top_name_img, bot_name_img]
    for j in range(len(imgs)):
        i = imgs[j]
        boxes = contour_bound_boxes(cv2.findContours(i, 1, 3)[1], BBoxes.WORD)
        min_x = min(boxes, key=lambda x: x[0])[0]
        max_x = max(boxes, key=lambda x: x[2])[2]
        imgs[j] = NdImage.crop(i, (0, min_x - BBoxes.WORD.value, i.shape[0], max_x + BBoxes.WORD.value))

    return np.concatenate(tuple(imgs), axis=1)


def try_read_name(img: np.ndarray):
    results = []
    word_locations = {}
    single_line_img = undo_word_wrap(img)

    attempt_name = get_tess_data(single_line_img)
    for x in attempt_name.data:
        word_locations[x.result] = (x.left, x.top)
        results.append(x.result)

    for failed_name in attempt_name.failed_data:
        attempt_words, failed_bounds = try_read_words(single_line_img, failed_name)
        for failed_letter in attempt_words:
            # not implemented yet
            # attempt_letters = try_read_letters(attempt_words.failed_data)
            pass

    sorted_words = [y[0] for y in sorted(word_locations.items(), key=lambda x: x[1][0])]
    print(f'{" ".join(sorted_words)}')
    pass


@dataclass
class ColorFilter:
    f: Callable

    def filter(self, p):
        return self.f(p)


YELLOW_THEME_FILTER = ColorFilter(lambda p: p is not None)
RED_THEME_FILTER = ColorFilter(lambda p: p is not None)


def apply_interface_filter(item: np.ndarray, color_filter: ColorFilter):
    """Used to remove any pixel outside the supplied filter
       Currently not used.
    """

    hueMinTest = item[:, :, 0] >= (200 / 360 * 179)
    hueMaxTest = item[:, :, 0] < (210 / 360 * 179)
    hueTest = hueMinTest & hueMaxTest
    satMinTest = item[:, :, 1] >= (93 / 100 * 255)
    satMaxTest = item[:, :, 1] < (100 / 100 * 255)
    satTest = satMinTest & satMaxTest
    hsvTest = ((hueTest & satTest) ^ 1) * 255
    identityArraySize = list(item.shape)
    identityArraySize[2] -= 1
    identityArray = np.zeros(identityArraySize)
    thresholdedImage = np.dstack((identityArray, hsvTest)).astype(np.uint8)

    return thresholdedImage


def get_item_image_list(inv: InventoryImageInfo):
    """Returns a list of images which are cropped to the name of an item."""
    items = []
    for y in range(inv.row_count):
        for x in range(inv.column_count):
            if x + y * inv.column_count > 19 - 1:  # Skipping the first 0 items
                x_coord = inv.top_left_corner_x + x * inv.item_gap_x
                y_coord = inv.top_left_corner_y + y * inv.item_gap_y
                bounds = (y_coord, x_coord, y_coord + inv.name_field_height, x_coord + inv.name_field_width)
                item = NdImage.crop(inv.image, bounds)
                item = cv2.cvtColor(item, cv2.COLOR_BGR2HSV)
                item = NdImage.rescale(item, 400 / 72.0)
                item = apply_interface_filter(item, YELLOW_THEME_FILTER)
                item = cv2.cvtColor(item, cv2.COLOR_HSV2RGB)
                item = cv2.cvtColor(item, cv2.COLOR_RGB2GRAY)
                # item.show()
                items.append(item)
    return items


def detect_inventory_info(page: np.ndarray):
    """Barely implemented. Purpose is to detect screen size and calculate all the fields needed for
       InventoryImageInfo"""

    # uses parameter expansion to improve readability
    # Param order: Top left corner, text area, item gaps, item grid
    info = InventoryImageInfo(page, *(99, 319), *(165, 47), *(200, 199), *(6, 4))
    return info


def parse_item_page(item_page: np.ndarray):
    item_page_info = detect_inventory_info(item_page)
    items = get_item_image_list(item_page_info)

    for item in items:
        try_read_name(item)
    pass


class NdImage:
    @staticmethod
    def crop(image: np.ndarray, bounds) -> np.ndarray:
        return image[bounds[0]:bounds[2], bounds[1]:bounds[3]]

    @staticmethod
    def rescale(item: np.ndarray, scale: float) -> np.ndarray:
        return NdImage.rescale_xy(item, scale, scale)

    @staticmethod
    def rescale_xy(item: np.ndarray, scale_x: float, scale_y: float) -> np.ndarray:
        return cv2.resize(item, dsize=(0, 0), fx=scale_x, fy=scale_y)


def showImg(img):
    # img2 = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
    cv2.imshow('image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def saveTest(img: np.ndarray, conv: int = -1):
    if conv is not -1:
        img2 = cv2.cvtColor(img, conv)
    else:
        img2 = img
    cv2.imwrite('test.png', img2)
