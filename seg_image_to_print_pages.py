import argparse
import json
from os import makedirs, path
from skimage import io, morphology
import numpy as np
import matplotlib.pyplot as plt
from skimage.measure import label
from skimage.segmentation import find_boundaries
from skimage.transform import rescale
import imageio
from make_seg_image import compute_grayscale_thresholds

# adjust these as per your printer
PRINTER_DPI = 100


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
    cut_dir = path.join(args.out_dir, 'cuts')
    makedirs(cut_dir, exist_ok=True)
    fg_dir = path.join(args.out_dir, 'foreground')
    makedirs(fg_dir, exist_ok=True)

    # the first page is not cut, so the print page for it should only contain fiducials
    for paper_num, (color_name, color) in enumerate(colors.items()):
        (low_gray_val, _) = thresh_dict[color_name]

        fg_mask = gray >= low_gray_val
        fg_fn = path.join(fg_dir, f'{color_name}_fg.png')
        fg_mask = 255 * fg_mask.astype(np.uint8)
        print(f'Saving {color_name} foreground mask to {fg_fn}')
        imageio.imwrite(fg_fn, fg_mask, dpi=[PRINTER_DPI,PRINTER_DPI])  # my printer seems to ignore this, but I'll leave it in anyway

        cut_lines_im = ~find_boundaries(label(fg_mask))
        # add lines along image frame as fiducials
        cut_lines_im[:2] = 0
        cut_lines_im[-2:] = 0
        cut_lines_im[:,:2] = 0
        cut_lines_im[:,-2:] = 0
        cut_lines_im = 255 * cut_lines_im.astype(np.uint8)
        cut_fn = path.join(cut_dir, f'{color_name}_cuts.png')
        print(f'Saving {color_name} outline to {cut_fn}')
        imageio.imwrite(cut_fn, cut_lines_im, dpi=[PRINTER_DPI,PRINTER_DPI])
