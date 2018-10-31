import os
import time
import win32api
import win32gui

import cv2
import numpy as np
from PIL import ImageGrab
from virtual_keyboard import TapKey, KeyCodes
from image_parser import NdImage, showImg, saveTest, get_tess_data

def test():
    time.sleep(4)
    curs_loc = [(354, 704), (357, 817), (576, 826), (574, 708), (573, 590), (810, 591), (810, 715), (811, 835), (1058, 840), (1058, 717), (1059, 593), (1314, 593), (1313, 718), (1311, 842), (1564, 842), (1567, 719), (1569, 593)]
    # sleep = 480
    # TapKey(KeyCodes.RIGHT_ARROW)
    # for x in range(6):
    #     time.sleep(sleep / 1000)
    #     TapKey(KeyCodes.F6)
    #     _, _, pos = win32gui.GetCursorInfo()
    #     curs_loc.append(pos)
    #     time.sleep(200 / 1000)
    #     for y in range(2):
    #         print(x)
    #         if x % 2 == 0:
    #             TapKey(KeyCodes.DOWN_ARROW)
    #         else:
    #             TapKey(KeyCodes.UP_ARROW)
    #         time.sleep(sleep/1000)
    #         TapKey(KeyCodes.F6)
    #         _, _, pos = win32gui.GetCursorInfo()
    #         curs_loc.append(pos)
    #         time.sleep(200 / 1000)
    #     TapKey(KeyCodes.RIGHT_ARROW)

    files = os.listdir("C:\\Users\\kwill\\Pictures\\Warframe")[-1 * len(curs_loc):]
    for file in files:
        img = cv2.imread("C:\\Users\\kwill\\Pictures\\Warframe\\" + file)
        center = curs_loc.pop(0)
        topLeft = (center[0] - 120, center[1] - 190)
        botRight = (center[0] + 120, center[1] + 190)
        croppedImg = NdImage.crop(img, (topLeft[1], topLeft[0], botRight[1], botRight[0]))
        item = cv2.cvtColor(croppedImg, cv2.COLOR_BGR2HSV)
        # item = NdImage.rescale(item, 400 / 72.0)

        # hueMinTest = item[:, :, 0] >= (265 / 360 * 179)
        # hueMaxTest = item[:, :, 0] < (275 / 360 * 179)
        # hueTest = hueMinTest & hueMaxTest
        # satMinTest = item[:, :, 1] >= (18 / 100 * 255)
        # satMaxTest = item[:, :, 1] < (35 / 100 * 255)
        # satTest = satMinTest & satMaxTest
        # valMinTest = item[:, :, 2] >= (50 / 100 * 255)
        # valMaxTest = item[:, :, 2] < (100 / 100 * 255)
        # valTest = valMinTest & valMaxTest
        # hsvTest = ((hueTest & satTest & valTest) ^ 1) * 255
        # identityArraySize = list(item.shape)
        # identityArraySize[2] -= 1
        # identityArray = np.zeros(identityArraySize)
        # thresholdedImage = np.dstack((identityArray, hsvTest)).astype(np.uint8)
        data = get_tess_data(croppedImg)
        pass


def capture():
    time.sleep(5)
    images = []
    for x in range(40):
        time.sleep(300 / 1000)
        images.append(ImageGrab.grab())
        for y in range(4):
            win32api.mouse_event(0x0800, x, y, -1, 0)
            time.sleep(50 / 1000)
    return images


def save_items(images):
    i = 0
    for img in images:
        img.save(f'test{i}.png')
        i += 1
