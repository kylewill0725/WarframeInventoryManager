import math
import re
from dataclasses import dataclass

import pytesseract
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
    width: int = 0
    height: int = 0
    confidence: int = -1

    def tostring(self):
        return f'{self.result}	{self.left}	{self.top}	{self.width+self.left}	{self.height+self.height}	' \
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
                    if tess.confidence > 75:
                        match = re.match("[a-zA-Z0-9 &]+", tess.result)
                        if match is not None:
                            data.append(tess)
                        else:
                            failed_data.append(tess)
                    else:
                        failed_data.append(tess)
            pass

        return data, failed_data


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'


@dataclass
class InventoryImageInfo:
    image: ImageFile.Image
    top_left_corner_x: int
    top_left_corner_y: int
    name_field_width: int
    name_field_height: int
    item_gap_x: int  # (x_gap, y_gap) in pixels from the corner of one item to the same corner of the next
    item_gap_y: int
    column_count: int
    row_count: int


@dataclass
class ScaledImage:
    """Tracks changes of scale for an image. Needed due to frequent rescaling when using tesseract"""

    image: ImageFile.Image
    scale_x: float = 1
    scale_y: float = 1
    corner_x: int = 0
    corner_y: int = 0

    def rescale(self, multiplier: float):
        return self.rescale_xy(multiplier, multiplier)

    def rescale_xy(self, multiplier_x: float, multiplier_y: float):
        self.scale_x *= multiplier_x
        self.scale_y *= multiplier_y
        return ScaledImage(self.image.resize(((self.image.width * multiplier_x), (self.image.height * multiplier_y)),
                                             Image.BILINEAR), self.scale_x, self.scale_y)

    def invalidate_scale(self):
        """Used to say that the scale is unreliable. Used when adding a border as tracking the current border size seems
        unnecessary"""
        self.scale_x = -1
        self.scale_y = -1


def add_border(img: ScaledImage, pixels=0, multiplier=1.0):
    new_size = (math.floor(img.image.width * multiplier + pixels), math.floor(img.image.height * multiplier + pixels))
    new_img = ScaledImage(Image.new(img.image.mode, new_size))
    new_img.invalidate_scale()
    new_img.image.paste(img.image, (math.floor((new_img.image.width - img.image.width) / 2)
                                    , math.ceil((new_img.image.height - img.image.height) / 2)))
    return new_img


def crop_failed_image(img: ScaledImage, failed_data: TessData):
    result = img.image.crop((
        failed_data.left,
        failed_data.top,
        failed_data.left + failed_data.width,
        failed_data.top + failed_data.height
    ))
    return ScaledImage(result, img.scale_x, img.scale_y)


def try_read_words(img: ScaledImage, failed_data):
    results = []

    cropped_image = crop_failed_image(img, failed_data)
    attempt_words_image = add_border(cropped_image.rescale(4), multiplier=1.2)

    data = pytesseract.image_to_data(attempt_words_image.image)
    tess_data = TessDataParser(data)
    for x in tess_data.data:
        results.append(x.result)

    return results, tess_data.failed_data


def try_read_name(img: ScaledImage):
    results = []
    scale = 1
    top_name_img = ScaledImage(img.image.crop(
        (0,
         0,
         img.image.width,
         math.floor(img.image.height / 2.0)
         )
    ), img.scale_x, img.scale_y)

    bot_name_img = ScaledImage(img.image.crop(
        (0,
         img.image.height - top_name_img.image.height,
         img.image.width,
         img.image.height
         )
    ), img.scale_x, img.scale_y)

    imgs = [top_name_img, bot_name_img]
    for i in imgs:
        i2 = i.rescale(scale)
        attempt_name_image = add_border(i2, multiplier=1.1)
        attempt_name = pytesseract.image_to_data(attempt_name_image.image)
        attempt_name = TessDataParser(attempt_name)
        for x in attempt_name.data:
            results.append(x.result)

        for failed_name in attempt_name.failed_data:
            attempt_words = try_read_words(attempt_name_image, failed_name)
            for failed_letter in attempt_words:
                # not implemented yet
                # attempt_letters = try_read_letters(attempt_words.failed_data)
                pass

    print(f'{" ".join(results)}')
    pass


@dataclass
class ColorFilter:
    max_rgb: (int, int, int)
    min_rbg: (int, int, int)


def apply_interface_filter(item, color_filter: ColorFilter):
    """Used to remove any pixel outside the supplied filter
       Currently not used.
    """

    bands = item.split()
    for b in range(2):
        bands[b + 1].paste(bands[b + 1].point(lambda p: 0))
    item = Image.merge(item.mode, bands).convert("L")
    item = item.point(lambda p: 0 if p < 30 else 255 - p)
    return item


def get_item_image_list(inv: InventoryImageInfo):
    """Returns a list of images which are cropped to the name of an item."""
    items = []
    for y in range(inv.row_count):
        for x in range(inv.column_count):
            if x + y * inv.column_count > 0 - 1:  # Skipping the first 0 items
                x_coord = inv.top_left_corner_x + x * inv.item_gap_x
                y_coord = inv.top_left_corner_y + y * inv.item_gap_y
                bounds = (x_coord, y_coord, x_coord + inv.name_field_width, y_coord + inv.name_field_height)
                item = ScaledImage(inv.image.crop(bounds))
                item = item.rescale(4)
                # item = apply_interface_filter(item)
                # item.show()
                items.append(item)
    return items


def detect_inventory_info(page: ImageFile.Image):
    """Barely implemented. Purpose is to detect screen size and calculate all the fields needed for
       InventoryImageInfo"""

    # uses parameter expansion to improve readability
    info = InventoryImageInfo(page, *(98, 331), *(166, 35), *(200, 199), *(6, 4))
    return info


def parse_item_page(item_page: ImageFile.ImageFile):
    item_page_info = detect_inventory_info(item_page)
    items = get_item_image_list(item_page_info)

    for item in items:
        try_read_name(item)
    pass
