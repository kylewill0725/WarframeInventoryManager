import time
import win32api

from PIL import ImageGrab


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

    img = Image.open("test0.png")
    parseItemPage(img)
