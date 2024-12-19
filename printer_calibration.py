import argparse
import numpy as np
from os import path
import imageio

# adjust these as per your printer
PRINTER_DPI = 100

# a slightly-small estimate of a printed page's canvas size (page size minus margins)
PRINTER_CANVAS_SIZE = [  # in inches. order does not matter
    7.75,
    10.125
]


if __name__ == '__main__':

    parser = argparse.ArgumentParser('Print a rectangle to verify printer parameters')
    parser.add_argument('dest_image_path', nargs='?', default=path.join('printer-calibration', 'full-page-rectangle.png'))
    args = parser.parse_args()

    target_shape = np.round(np.array(PRINTER_CANVAS_SIZE) * PRINTER_DPI).astype(int)
    im = 255 * np.ones(target_shape, dtype=np.uint8)
    t = 4
    im[:t] = 0
    im[-t:] = 0
    im[:,:t] = 0
    im[:,-t:] = 0
    imageio.imwrite(args.dest_image_path, im)
