try:
    import Image, ImageGrab
except ImportError:
    from PIL import Image, ImageGrab, ImageFile, ImageFilter
from image_parser import parseItemPage


def image_parse_test():
    demoPage = Image.open("example_data/inventory_pics/test0.png")
    parseItemPage(demoPage)


if __name__ == '__main__':
    image_parse_test()
