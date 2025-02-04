import argparse
from os import path, makedirs
import json
import numpy as np
from skimage import io
from skimage.transform import rescale
from skimage.filters import gaussian


def compute_grayscale_thresholds(color_dict):
    gray_colors = {name: sum(color)/3 for name, color in color_dict.items()}
    grays = list(gray_colors.values())
    thresholds = [0] + [(c1+c2)/2 for c1, c2 in zip(grays[:-1], grays[1:])] + [255]
    names = gray_colors.keys()
    thresh_dict = {
        color: (sta, end) 
        for color, (sta, end) in zip(names, zip(thresholds[:-1], thresholds[1:]))
    }
    return thresh_dict



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--colors', '-c', default='color-calibration/paper-colors.json', help='JSON file with your papers\' color values')
    parser.add_argument('--sigma', '-s', default=2, type=float, help='Blurring radius. Higher means smoother, simpler shapes. Default=2')
    # parser.add_argument('--min-size', type=int, default=50, help='minimim size of objects/holes')
    parser.add_argument('--debug', action='store_true', help='Save intermediate images for debugging')
    parser.add_argument('--out-dir', '-o', default='output-ims')
    parser.add_argument('im_file', nargs='+', help='Your prepared reference photo')
    args = parser.parse_args()

    # read inputs
    with open(args.colors) as f:
        colors = json.load(f)

    for im_fn in args.im_file:
        print(f'Segmenting {im_fn}')

        im = io.imread(im_fn)[:,:,:3]

        # prepare output
        makedirs(args.out_dir, exist_ok=True)

        # scale such that the longer image dimension is 800
        scale = 800 / max(im.shape[:2])
        im = np.round(rescale(im, scale, channel_axis=-1, preserve_range=True)).astype(np.uint8)
        if args.debug:
            rescaled_fn = path.join(args.out_dir, 'rescaled.jpg')
            io.imsave(rescaled_fn, im)
        
        # mean over color channels
        gray = np.round(im.sum(-1)/3).astype(np.uint8)
        if args.debug:
            gray_fn = path.join(args.out_dir, 'gray.jpg')
            io.imsave(gray_fn, gray)

        # blur. otherwise you get way too much detail
        blurred = np.round(gaussian(gray, sigma=args.sigma, preserve_range=True)).astype(np.uint8)
        if args.debug:
            gray_fn = path.join(args.out_dir, 'blurred.jpg')
            io.imsave(gray_fn, blurred)

        # set thresholds to lie halfway between paper colors
        thresh_dict = compute_grayscale_thresholds(colors)
        # for color, (sta, end) in thresh_dict.items():
        #     print(f'{color} values: {sta:.1f} - {end:.1f} (width {end-sta:.1f})')

        # create actual segmentation image. reference photo pixels are rounded to the nearest paper color
        seg_im = np.empty(im.shape, np.uint8)
        for (low, hi), rgb in zip(thresh_dict.values(), colors.values()):
            mask = np.logical_and(blurred>=low, blurred<hi)
            print(low, hi, rgb, mask.sum())
            value = int(round((low+hi)/2))
            seg_im[mask] = rgb

        base_input_fn = path.basename(path.splitext(im_fn)[0])
        seg_fn = path.join(args.out_dir, f'{base_input_fn}.png')  # use png; jpeg shows artifacts
        io.imsave(seg_fn, seg_im)
    