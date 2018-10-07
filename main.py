import time

import numpy as np

from pytesseract import pytesseract

from test import img_cap_test

try:
    import Image, ImageGrab
except ImportError:
    from PIL import Image, ImageGrab, ImageFile, ImageFilter
from image_parser import parse_item_page, TessDataParser, NdImage
from matplotlib import pyplot as plt
import cv2


pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR-3\tesseract.exe'


def image_parse_test():
    img_path = "example_data/inventory_pics/test3.png"
    # img_path = "test.png"
    demoPage = cv2.imread(img_path)

    # attempt_name = pytesseract.image_to_data(demoPage)
    # attempt_name = TessDataParser(attempt_name)
    parse_item_page(demoPage)


def showImg(img):
    # img2 = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
    cv2.imshow('image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    # image_parse_test()
    time.sleep(5)
    img_cap_test()
