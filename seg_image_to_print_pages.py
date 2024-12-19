import argparse
import json
from os import makedirs, path
from skimage import io
import numpy as np
from skimage.measure import label
from skimage.segmentation import find_boundaries
from skimage.transform import rescale
import imageio
from make_seg_image import compute_grayscale_thresholds
from printer_calibration import PRINTER_DPI, PRINTER_CANVAS_SIZE


def tile_image(im, tile_frame_thickness=2):
    # im should be a 2d 8-bit image array
    page_size_px = np.round(np.array(PRINTER_CANVAS_SIZE) * PRINTER_DPI).astype(int)
    grid_shape = np.ceil(np.array(im.shape[:2]) / page_size_px).astype(int)
    t = tile_frame_thickness
    tiles = []
    for i in range(grid_shape[0]):
        ista = i * page_size_px[0]
        iend = min(ista+page_size_px[0], im.shape[0])
        tile_row = []
        for j in range(grid_shape[1]):
            jsta = j * page_size_px[1]
            jend = min(jsta+page_size_px[1], im.shape[1])
            tile_src = im[ista:iend, jsta:jend]
            tile_src[:t] = 0
            tile_src[-t:] = 0
            tile_src[:,:t] = 0
            tile_src[:,-t:] = 0
            tile = 255 * np.ones(page_size_px, dtype=im.dtype)
            iend_dst = min(page_size_px[0], tile_src.shape[0])
            jend_dst = min(page_size_px[1], tile_src.shape[1])
            tile[:iend_dst, :jend_dst] = tile_src
            tile_row.append(tile)
        tiles.append(tile_row)
    return tiles
        

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--colors', '-c', default='color-calibration/paper-colors.json', help='JSON file with your papers\' color values')
    parser.add_argument('--out-dir', '-o', default='output-ims/print-pages')
    parser.add_argument('--target-len', '-l', type=float, default=12)
    parser.add_argument('seg_file', help='Your edited segmentation photo')
    args = parser.parse_args()

    # inputs
    with open(args.colors) as f:
        colors = json.load(f)
    thresh_dict = compute_grayscale_thresholds(colors)
    im = io.imread(args.seg_file)[:,:,:3]

    target_num_pixels = PRINTER_DPI * args.target_len
    scale_factor = target_num_pixels / max(im.shape[:2])
    gray = im.sum(-1) / 3
    gray = np.round(rescale(gray, scale_factor, preserve_range=True)).astype(np.uint8)
    physical_size = np.array(gray.shape[:2]) / PRINTER_DPI
    print(f'Final size of piece: {physical_size[0]:.1f} tall X {physical_size[1]:.1f} inches wide')

    # outputs
    makedirs(args.out_dir, exist_ok=True)

    # the first page is not cut, so the print page for it should only contain fiducials
    for paper_num, (color_name, color) in enumerate(colors.items()):
        (low_gray_val, _) = thresh_dict[color_name]
        fg_mask = gray >= low_gray_val
        cut_lines_im = ~find_boundaries(label(fg_mask))
        cut_lines_im = 255 * cut_lines_im.astype(np.uint8)
        tile_grid = tile_image(cut_lines_im)
        for row_num, tile_row in enumerate(tile_grid):
            for col_num, tile in enumerate(tile_row):
                tile_fn = path.join(args.out_dir, f'{color_name}_cuts_row{row_num+1}_col{col_num+1}.png')
                print(f'Saving {color_name} outline tile to {tile_fn}')
                imageio.imwrite(tile_fn, tile, dpi=[PRINTER_DPI,PRINTER_DPI])
