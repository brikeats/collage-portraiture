import argparse
import json
from os import makedirs, path
from skimage import io, morphology
import numpy as np
import matplotlib.pyplot as plt
from skimage.measure import label
from skimage.segmentation import find_boundaries
import imageio

# adjust these as per your printer
PRINT_PAGE_HEIGHT_INCHES = 11
PRINT_PAGE_WIDTH_INCHES = 8.5
PRINT_PAGE_MARGIN_INCHES = 0.5


PRINT_CANVAS_SIZE = (
    PRINT_PAGE_HEIGHT_INCHES - PRINT_PAGE_MARGIN_INCHES,
    PRINT_PAGE_WIDTH_INCHES - PRINT_PAGE_MARGIN_INCHES
)
    

# https://imageio.readthedocs.io/en/stable/_autosummary/imageio.plugins.pillow_legacy.html

def make_image_tiles_for_printing(im):
    
    # transpose as needed
    print_canvas_ar = PRINT_CANVAS_SIZE[0] / PRINT_CANVAS_SIZE[1]  # height/width
    im_ar = im.shape[0] / im.shape[1]
    if im_ar < print_canvas_ar:
        im = im.T.copy()

    # TODO: 1) break into tiles 2) add fiducials for alignment

    return [im]


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--colors', '-c', default='color-calibration/paper-colors.json', help='JSON file with your papers\' color values')
    parser.add_argument('--out-dir', '-o', default='output-ims/print-pages')
    parser.add_argument('seg_file', help='Your edited segmentation photo')
    args = parser.parse_args()

    # inputs
    with open(args.colors) as f:
        colors = json.load(f)
    im = io.imread(args.seg_file)

    # outputs
    makedirs(args.out_dir, exist_ok=True)

    for color_name, color in colors.items():
        rgb_mask = im == color
        mask = np.all(rgb_mask, axis=-1)
        boundary_im = ~find_boundaries(label(mask))

        boundary_im = 255 * boundary_im.astype(np.uint8)
        color_dir = path.join(args.out_dir, str(color_name))
        makedirs(color_dir, exist_ok=True)

        tiles = make_image_tiles_for_printing(boundary_im)
        print(f'DEBUG {boundary_im.shape=}')
        for tile_num, tile in enumerate(tiles):
            out_fn = path.join(color_dir, f'{color_name}_{tile_num:02d}.png')
            imageio.imwrite(out_fn, tile, dpi=[100,100])
        break
