import argparse
from os import path, makedirs
import json
import numpy as np
from skimage import io
from skimage.transform import rescale
from skimage.morphology import remove_small_holes, remove_small_objects
from skimage.filters import gaussian


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--colors', '-c', default='color-calibration/paper-colors.json', help='JSON file with your papers\' color values')
    parser.add_argument('--sigma', '-s', default=2, help='Blurring radius. Higher means smoother, simpler shapes')
    # parser.add_argument('--min-size', type=int, default=50, help='minimim size of objects/holes')
    parser.add_argument('--debug', action='store_true', help='Save intermediate images for debugging')
    parser.add_argument('--out-dir', '-o', default='output-ims')
    parser.add_argument('im_file', help='Your prepared reference photo')
    args = parser.parse_args()

    # read inputs
    with open(args.colors) as f:
        colors = json.load(f)

    im = io.imread(args.im_file)[:,:,:3]

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
    gray_colors = {name: sum(color)/3 for name, color in colors.items()}
    grays = list(gray_colors.values())
    thresholds = [0] + [(c1+c2)/2 for c1, c2 in zip(grays[:-1], grays[1:])] + [255]
    names = gray_colors.keys()
    thresh_dict = {
        color: (sta, end) 
        for color, (sta, end) in zip(names, zip(thresholds[:-1], thresholds[1:]))
    }
    for color, (sta, end) in thresh_dict.items():
        print(f'{color} values: {sta:.1f} - {end:.1f} (width {end-sta:.1f})')

    # create actual segmentation image. reference photo pixels are rounded to the nearest paper color
    seg_im = np.empty(im.shape, np.uint8)
    for (low, hi), rgb in zip(thresh_dict.values(), colors.values()):
        mask = np.logical_and(blurred>=low, blurred<hi)
        # mask = remove_small_holes(mask, args.min_size)  # usually not a good idea: removes important face details
        # mask = remove_small_objects(mask, args.min_size)
        value = int(round((low+hi)/2))
        seg_im[mask] = rgb
    seg_fn = path.join(args.out_dir, 'segmentation.png')  # use png; jpeg shows artifacts
    io.imsave(seg_fn, seg_im)
    