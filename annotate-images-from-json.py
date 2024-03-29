import argparse

import os

from PIL import Image, ImageDraw, ImageFont

# from glob import glob

# Module which contains functions to draw annotations on image
from annotation_utils import draw_corners, annotate_object

import json

import time

from utils import guess_last_frame

# Import parameters such as symbols and colors from separate file
from constants import (
    LINE_WIDTH, VEHICLE_SYMBOLS, VEHICLE_COLORS, TEXT_FG_COLOR, SCALE)


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'input_folder',
        help="The folder containing the original input images.")

    parser.add_argument(
        'aux_folder',
        help="The folder containing auxiliary files generated by the "
        "pipeline.")

    parser.add_argument(
        '--start_frame',
        type=int,
        default=1,
        help="The starting frame.")

    parser.add_argument(
        '--end_frame',
        type=int,
        # required=True,
        help="The ending frame.")

    parser.add_argument(
        '--window',
        type=int,
        default=5,
        help="The number of frame to use to improve plates detection")

    args = parser.parse_args()
    if args.end_frame is None:
        args.end_frame = guess_last_frame(args.input_folder)

    # Correct start and end frame based on the window parameter
    args.start_frame += args.window
    args.end_frame -= args.window

    return args


def outline_bounding_box(x, y, w, h, pil_draw, color):
    """
    Draw an outline for a bounding box
    """

    # Determine which is the shorter side
    min_len = min(h, h)

    # Determine segment length
    segment_length = min(min_len/3, 50)

    # Draw corners
    draw_corners(x, y, w, h, segment_length, pil_draw, color=color,
                 width=LINE_WIDTH)


def annotate_image(img_path, annotations, font, font_large, args):
    """
    Take as input the path of one input image and the arguments passed to the
    script and proceeds to retrieving all required information to display the
    license plate number close to the car.
    """

    # Extract filename
    base_image_name = os.path.basename(img_path)

    # Load the entire image
    img_full = Image.open(img_path)

    # pil_draw = ImageDraw.Draw(img_full)
    pil_draw = ImageDraw.Draw(img_full, mode='RGBA')

    tic = time.time()

    for car in annotations['cars']:

        # Unpack coordinates for bounding box
        car_crop_x, car_crop_y, car_crop_w, car_crop_h = car['bounding_box']

        vehicle_category = car['category']

        # Draw a cool outline of the vehicle
        outline_bounding_box(
            car_crop_x, car_crop_y, car_crop_w, car_crop_h,
            pil_draw, (255, 255, 255))

        for lp in car['plates']:

            # Beautify license plate text
            lp_text = lp['plate_text']

            lp_crop_x_absolute, lp_crop_y_absolute, lp_crop_w, lp_crop_h = \
                lp['bounding_box']

            # Actually annotate object
            annotate_object(
                lp_crop_x_absolute, lp_crop_y_absolute,
                lp_crop_w, lp_crop_h, lp_text, pil_draw,
                font,
                10,  # padding
                0.15,  # segment_ratio
                0.4,  # line_length_ratio
                LINE_WIDTH,
                VEHICLE_COLORS[vehicle_category],  # outline color
                TEXT_FG_COLOR,  # text color
                (255, 255, 255),  # bg color
                SCALE,
                object_symbol=VEHICLE_SYMBOLS[vehicle_category],
                font_symbol=font_large,
                bg_color_symbol=VEHICLE_COLORS[vehicle_category])

    toc = time.time()

    print("Done, elapsed time = {}".format(toc-tic))
    print("Done, writing image")

    # Save the image with bb
    img_full.save(
        os.path.join(
            args.aux_folder,
            'results',
            base_image_name[:-4]+"_output.png"),
        "PNG")

    return


def main():

    args = parse_args()

    font_filename = \
        "OpenSans-Regular.ttf"

    font_icons_filename = \
        "DejaVu Sans Mono Nerd Font Complete Mono.ttf"

    # Load the font used to write license plates text above actual recognized
    # plates.
    font = ImageFont.truetype(
        os.path.join('data', 'fonts', font_filename), size=SCALE*30)

    # Load a second copy of the font for symbols
    font_large = ImageFont.truetype(
        os.path.join('data', 'fonts', font_icons_filename), size=SCALE*40)

    for t in range(args.start_frame, args.end_frame+1):

        annotations_file = os.path.join(
            args.aux_folder,
            "frame{:05d}_annotations_unique.json".format(t))

        img_path = os.path.join(
            args.input_folder,
            "frame{:05d}.png".format(t))

        # Load annotations from json file
        with open(annotations_file, 'r') as jf:
            annotations = json.load(jf)

        print("Annotating image {}".format(os.path.basename(img_path)))

        annotate_image(img_path, annotations, font, font_large, args)


if __name__ == "__main__":
    main()
