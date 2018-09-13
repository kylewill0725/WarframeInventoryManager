try:
    import Image, ImageGrab
except ImportError:
    from PIL import Image, ImageGrab, ImageFile, ImageFilter
from image_parser import parse_item_page


def image_parse_test():
    demoPage = Image.open("example_data/inventory_pics/test0.png")
    parse_item_page(demoPage)


if __name__ == '__main__':
    image_parse_test()
