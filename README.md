# Collage Portraiture

Scripts for semi-automatically creating templates for cut-paper portraits.

## Install Depdendencies

* create a python 3.11 environment. using conda: `conda create -n portraits python=3.11 -y && conda activate portraits`
* `pip install -r requirements.txt`

## Color Calibration

The first step is to determine the colors of the papers that you'll be using as they appear in your camera under representative lighting conditions.

* Select papers. There should be at least 2 colors and they should form a harmonious color pallette. These scripts only deal with grayscale images; the colors are up to you. They should all be the same type/manufacturer so they expand and shrink together when the humidity changes.
* Take a calibration photo of the papers and save it as `color-calibration/papers.jpg`. Take the photo with the lighting conditions similar to those that you will use to display the final piece. Stack and spread the papers so they form parallel "bars" in the image frame. Ideally, you should use the same camera you'll use for the reference photo. 
* Use the notebook `color-calibration/Paper-Color-Calibration.ipynb` to create a set of colors for your papers. You'll need to edit the `rects` `dict` to select approprate the color patches from your photo.

After you've update the color `rects` and run the whole notebook, you should have a paper color file `color-calibration/paper-colors.json`.

## Printer Calibration

It is difficult to get a printer to print a given image file at a specified size. We want to break a large image into "tiles" which can be printed and assembled. Here's how I determined printer parameters necessary for tiling the image:

* print out `printer-calibration/big_tall_rectangle.png` in portrait mode. On the printed page, 2 of the rectangle's edges are as close as possible to the edge of the long size of the paper. This allows to determine your printer's maximum canvas size per page in one direction. Round it down a little.
* print out `printer-calibration/big_wide_rectangle.png` in landscape mode. On the printed page, 2 of the rectangle's edges are as close as possible to the edge of the short size of the paper. This allows to determine your printer's maximum canvas size per page in the other direction. Again, round it down a little.

Now you should have a conservative (slightly small) estimate of your printer's "canvas size" on a printed page. In `printer_calibration.py` edit `PRINTER_CANVAS_SIZE` with your canvas size. Run `python printer_calibration.py` to produce an image of a rectangle. Print this out and verify with a ruler that it matches your `PRINTER_CANVAS_SIZE`. If not, you may need to adjust `printer_calibration.PRINTER_DPI`.

## Prepare reference photo

Crop and edit the photo as you see fit. Adjust the contrast so it looks good and vivid. Use AI tools to erase objects you want to remove. I often use the smudge tool in GIMP to blur and demphasize the background. Remember it doesn't have to be perfect, since the whole photo is blurred as a processing step. That said, try to keep the face in focus and blur the background.

## Convert reference photo to segmentation image

The script `make_seg_image.py` rounds the pixels of the reference photo to the closest paper color. It produces a `segmentation.png` file which is a preview of your final piece. To run this script on the included image of my greyhound, Delilah:

`python make_seg_image.py --out-dir output-ims delilah.jpg`

## Convert segmentation image to outlines

You can edit the segmentation photo as you see fit using GIMP or photoshop or whatever. Make sure that you only use the paper colors that are included in the segmentation photo (i.e., don't use blurring or smudge tools that introduce new pixel values).

To print outline images for transferring cut lines to your paper:

`python seg_image_to_print_pages.py --target-len 12 --out-dir output-ims/print output-ims/segmentation-edited.png`

