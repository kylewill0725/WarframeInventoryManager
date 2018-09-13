from Recurse import recurse, tail_recursive

try:
    import Image, ImageGrab
except ImportError:
    from PIL import Image, ImageGrab, ImageFile, ImageFilter
import pytesseract
import re
import win32api
from win32api import *
import time
import math


class TessData:
    def __init__(self, result="", level="", page_num=0, block_num=0, par_num=0, line_num=0, word_num=0, left=0, top=0,
                 width=0, height=0, conf=-1):
        self.result = result
        self.level = level
        self.page_num = page_num
        self.block_num = block_num
        self.par_num = par_num
        self.line_num = line_num
        self.word_num = word_num
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.conf = conf

    def tostring(self):
        return f'{self.result}	{self.left}	{self.top}	{self.width+self.left}	{self.height+self.height}	{self.conf}'


class TessDataParser:
    def __init__(self, str):
        (self.data, self.failed_data) = self.parse(str)

    def parse(self, str):
        data = []
        failedData = []
        rows = str.split("\n")
        for row in rows:
            columns = row.split("\t")
            if columns[0].isdigit():
                tess = TessData(columns[-1], *[int(x) for x in columns[:-1]])
                if tess.conf >= 0:
                    if tess.conf > 75:
                        match = re.match("[a-zA-Z0-9 &]+", tess.result)
                        if match is not None:
                            data.append(tess)
                        else:
                            failedData.append(tess)
                    else:
                        failedData.append(tess)
            pass

        return (data, failedData)


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'


def addborder(img, pixels=0, multiplier=1.0):
    newSize = (math.floor(img.width * multiplier + pixels), math.floor(img.height * multiplier + pixels))
    newImg = Image.new(img.mode, newSize)
    newImg.paste(img, (math.floor((newImg.width - img.width) / 2)
                       , math.ceil((newImg.height - img.height) / 2)))
    return newImg


@tail_recursive
def fixFailedData(img, failedData, successes=[], rounds=0):
    tessData = TessDataParser("")
    if rounds is 0:
        bounds = [img.width, img.height, 0, 0]
        for f in failedData:
            left = math.ceil(f.left * 0.95)
            top = math.ceil(f.top * 0.95)
            right = math.floor((f.left + f.width) * 1.05)
            bot = math.floor((f.top + f.height) * 1.05)
            if left < bounds[0]:
                bounds[0] = left
            if top < bounds[1]:
                bounds[1] = top
            if right > bounds[2]:
                bounds[2] = right
            if bot > bounds[3]:
                bounds[3] = bot
        newImg = img.crop(bounds)
        newImg = newImg.resize((newImg.width * 2, newImg.height * 2), Image.BILINEAR)
        newImg = addborder(newImg, multiplier=1.1)
        data = pytesseract.image_to_data(newImg)
        tessData = TessDataParser(data)
    successes += tessData.data
    if len(tessData.failed_data) > 0:
        return recurse(newImg, tessData.failed_data, successes, rounds)
    return successes


def parseText(img: ImageFile.ImageFile):
    tessData = TessDataParser("")
    scale = 8
    topImg = img.crop((0, 0, img.width, math.floor(img.height / 2.0)))
    botImg = img.crop((0, img.height - math.floor(img.height / 2.0), img.width, img.height))
    imgs = [topImg, botImg]
    for i in imgs:
        newSize = (i.width * scale, i.height * scale)
        i2 = i.resize(newSize, Image.BILINEAR)
        newImg = Image.new(i.mode, (math.ceil(i2.width * 1.1), math.ceil(i2.height * 1.1)))
        newImg.paste(i2, (math.floor((newImg.width - i2.width) / 2)
                          , math.ceil((newImg.height - i2.height) / 2)))
        data = pytesseract.image_to_data(newImg)
        data = TessDataParser(data)
        tessData.data += data.data
        if len(data.failed_data) > 0:
            tessData.data += fixFailedData(newImg, data.failed_data)
        pass
    # for d in tessData.data:
    #     d.top /= scale
    #     d.left /= scale
    #     d.height /= scale
    #     d.width /= scale
    #
    # for d in tessData.failed_data:
    #     d.top /= scale
    #     d.left /= scale
    #     d.height /= scale
    #     d.width /= scale

    imgMidPoint = math.ceil(newImg.height * 0.9 / 2)
    if len(tessData.failed_data) > 0:
        fixFailedData(tessData)
        # groups = {'top': [], 'bot': []}
        #
        # for t in tessData.failed_data:
        #     if t.top < imgMidPoint:
        #         groups['top'].append(t)
        #     else:
        #         groups['bot'].append(t)
        #
        # if len(groups['top']) > 0:
        #     topBounds = [newImg.width,0,0,imgMidPoint]
        #     for t in groups['top']:
        #         if t.left < topBounds[0]:
        #             topBounds[0] = t.left
        #         if t.width + t.left > topBounds[2]:
        #             topBounds[2] = t.width + t.left
        #
        #     topImg = newImg.crop(topBounds)
        #     topTessData = TessDataParser(pytesseract.image_to_data(topImg))
        #
        # if len(groups['bot']) > 0:
        #     botBounds = [newImg.width, imgMidPoint, 0, newImg.height]
        #     for t in groups['bot']:
        #         left = t.left * 0.95
        #         right = (t.width + t.left) * 1.05
        #         if left < botBounds[0]:
        #             botBounds[0] = left
        #         if right > botBounds[2]:
        #             botBounds[2] = right
        #
        #     thisScale = 4
        #     botImg = newImg.crop(botBounds)
        #     botImg = botImg.resize((math.floor(botImg.width * thisScale * 1.2), botImg.height * thisScale))
        #     botTesData = TessDataParser(pytesseract.image_to_data(botImg))
        #
        # t = tessData.failed_data[0]
        # tessData.failed_data.remove(t)
        #
        # left = math.ceil(t.left * 0.9)
        # width = math.floor(t.width * 1.1) + (t.left - left)
        # if t.top >= imgMidPoint:
        #     top = imgMidPoint
        #     height = newImg.height - top
        # else:
        #     top = 0
        #     height = imgMidPoint
        #
        # bounds = (left, top, left + width, top + height)
        # newImg = newImg.crop(bounds)
        # newImg = newImg.resize((newImg.width * scale, newImg.height * scale))
        # data = pytesseract.image_to_data(newImg)
        # newTessData = TessDataParser(data)
        # tessData.data += newTessData.data
        # tessData.failed_data += newTessData.failed_data

    print(f'{" ".join([x.result for x in tessData.data])}')
    pass


def loadItems():
    time.sleep(5)
    (x, y) = win32api.GetCursorPos()
    images = []
    for x in range(40):
        time.sleep(300 / 1000)
        images.append(ImageGrab.grab())
        for y in range(4):
            win32api.mouse_event(0x0800, x, y, -1, 0)
            time.sleep(50 / 1000)
    return images


def saveItems(images):
    i = 0
    for img in images:
        img.save(f'test{i}.png')
        i += 1


def parseItem(item):
    pass


def pointFun(point):
    pass


def parseItemPage(itemPage: ImageFile.ImageFile):
    # crop items

    xOffset = 98
    yOffset = 331

    textWidth = 166
    textHeight = 35

    xSpace = 200
    ySpace = 199

    wCount = 6
    hCount = 4
    items = []
    for y in range(hCount):
        for x in range(wCount):
            if x + 6*y > 8:
                xCoord = xOffset + x * xSpace
                yCoord = yOffset + y * ySpace
                bounds = (xCoord, yCoord, xCoord + textWidth, yCoord + textHeight)
                item = itemPage.crop(bounds)
                item = item.resize(((item.width * 4), (item.height * 2)), Image.BILINEAR)
                bands = item.split()
                for b in range(2):
                    bands[b + 1].paste(bands[b + 1].point(lambda p: 0))
                item = Image.merge(item.mode, bands).convert("L")
                item = item.point(lambda x: 0 if x < 30 else 255-x)
                # item.show()
                items.append(item)

    # attempt to read
    for item in items:
        parseText(item)
    pass
