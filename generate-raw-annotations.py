import argparse

import os

from PIL import Image

from src.utils import image_files_from_folder

import pandas as pd

import time

import json

# Import parameters such as symbols and colors from separate file
# from constants import (
    # LINE_WIDTH, VEHICLE_SYMBOLS, VEHICLE_COLORS,  # noqa
    # TEXT_FG_COLOR, SCALE)  # noqa

# TODO move somewhere else
import re

LP_PATTERN = re.compile("[A-FZ][A-Z][\d]{3}[A-Z]{2}")  # noqa


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
        '--width',
        type=int,
        help="The width of the original image")

    parser.add_argument(
        '--height',
        type=int,
        help="The height of the original image")

    return parser.parse_args()


def validate_lp_text(lp_text):
    """
    Optional step to validate license plate
    E.g.: italian ones should be two letters, three digits and two letters
    """

    return LP_PATTERN.match(lp_text) is not None


def get_annotations_from_car_crop(car_id, car_row, base_image_name,
                                  w, h, args):
    """
    w, h : int
        Size of original image (needed to compute absolute coordinates)
    """

    # Prepare dictionary for output
    out = dict()

    # Reconstruct crop coordinates and size
    car_crop_w = car_row.w * w
    car_crop_h = car_row.h * h

    car_crop_x = car_row.x * w - car_crop_w/2
    car_crop_y = car_row.y * h - car_crop_h/2

    # Extract category of the vehicle
    vehicle_category = car_row.category

    # Save category and bounding box
    out['category'] = vehicle_category
    out['bounding_box'] = (car_crop_x, car_crop_y, car_crop_w, car_crop_h)

    # Initialize list to save recognized plates
    out['plates'] = list()

    # Look for all detected licence plates for that car (most of the time
    # it's just one)
    try:
        car_lp_detections_file = os.path.join(
            args.aux_folder,
            "{}_car_{}_lp.txt".format(base_image_name[:-4], car_id))

        lp_df = pd.read_csv(
            car_lp_detections_file,
            header=None, sep=' ',
            names=['cc', 'x', 'y', 'w', 'h'])

        for lp_id, lp_row in lp_df.iterrows():

            # Compute coordinates of lp crop (these are with respect to the car
            # crop)
            lp_crop_w = lp_row.w * car_crop_w
            lp_crop_h = lp_row.h * car_crop_h

            lp_crop_x = lp_row.x * car_crop_w - lp_crop_w/2
            lp_crop_y = lp_row.y * car_crop_h - lp_crop_h/2

            # Compute absolute coordinates of the lp crop
            lp_crop_x_absolute = lp_crop_x + car_crop_x
            lp_crop_y_absolute = lp_crop_y + car_crop_y

            # Create dictionary for license plate data
            lp_dict = dict()

            # Save coordinates of the bounding box of the licencse plate
            plate_bounding_box = (
                lp_crop_x_absolute, lp_crop_y_absolute,
                lp_crop_w, lp_crop_h)

            lp_dict['bounding_box'] = plate_bounding_box

            # Fill fields with invalid values, will be replaced by valid ones
            lp_dict['plate_text'] = None
            lp_dict['valid_plate'] = False

            try:

                car_lp_ocrout_file = os.path.join(
                    args.aux_folder,
                    "{}_car_{}_{}_lp_str.txt".format(
                        base_image_name[:-4], car_id, lp_id))

                with open(car_lp_ocrout_file, 'r') as lp_ocr_f:
                    lp_text = lp_ocr_f.read().strip()

                # If there was recognized plate_text, save it in the dictionary
                lp_dict['plate_text'] = lp_text

                if validate_lp_text(lp_text):

                    # Plate number has been recognized as valid
                    lp_dict['valid_plate'] = True


            except Exception as e:  # noqa
                # print(e)
                pass

            # List Add the license plate to the list of recognized ones
            out['plates'].append(lp_dict)

    except Exception as e:  # noqa
        # print(e)
        pass

    return out


def process_image(img_path, args):
    """
    Take as input the path of one input image and the arguments passed to the
    script and proceeds to retrieving all required information to display the
    license plate number close to the car.
    """

    # Extract filename
    base_image_name = os.path.basename(img_path)

    # In case width and height are not specified, retrieve from image
    if args.width is None or args.height is None:
        # Load the entire image
        img_full = Image.open(img_path)
        w, h = img_full.size
    else:
        w, h = args.width, args.height

    tic = time.time()

    # Prepare output dictionary
    annotations = dict()
    annotations['cars'] = list()

    try:

        # First get the list of cars
        cars_df = pd.read_csv(
            os.path.join(
                args.aux_folder, "{}_cars.txt".format(base_image_name[:-4])),
            header=None, sep=' ',
            names=['cc', 'x', 'y', 'w', 'h', 'category'])

        # for car_id, car_row in enumerate(cars_df.iterrows()):
        for car_id, car_row in cars_df.iterrows():

            car_annotations = get_annotations_from_car_crop(
                car_id, car_row, base_image_name, w, h, args)

            annotations['cars'].append(car_annotations)

    except Exception as e:  # noqa
        pass

    with open(
            os.path.join(
                args.aux_folder,
                "{}_annotations.json".format(base_image_name[:-4])),
            'w') as jf:

        json.dump(annotations, jf, indent=4)

    toc = time.time()

    print("Done, elapsed time = {}".format(toc-tic))

    return


def main():

    args = parse_args()

    # Retrieve the names of the input images
    imgs_paths = image_files_from_folder(args.input_folder)

    for img_path in imgs_paths:
        # Process each image individually
        process_image(img_path, args)


if __name__ == "__main__":
    main()
