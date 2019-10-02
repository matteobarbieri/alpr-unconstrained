import sys
import cv2
import numpy as np
import traceback

import darknet.python.darknet as dn

from src.label import Label, lwrite
from os.path import splitext, basename, isdir
from os import makedirs
from src.utils import crop_region, image_files_from_folder
from darknet.python.darknet import detect

import argparse


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('input_dir')
    parser.add_argument('output_dir')

    parser.add_argument(
        '--vehicle_threshold', type=float, default=0.5)

    return parser.parse_args()


if __name__ == '__main__':

    try:

        args = parse_args()

        input_dir = args.input_dir
        output_dir = args.output_dir

        vehicle_threshold = args.vehicle_threshold

        vehicle_weights = b'data/vehicle-detector/yolov3.weights'
        vehicle_netcfg = b'data/vehicle-detector/yolov3.cfg'
        # vehicle_netcfg = b'darknet/cfg/yolov3.cfg'
        vehicle_dataset = b'data/vehicle-detector/coco.data'

        vehicle_net = dn.load_net(vehicle_netcfg, vehicle_weights, 0)
        vehicle_meta = dn.load_meta(vehicle_dataset)

        imgs_paths = image_files_from_folder(input_dir)
        imgs_paths.sort()

        if not isdir(output_dir):
            makedirs(output_dir)

        print('Searching for vehicles using YOLO...')

        for i, img_path in enumerate(imgs_paths):

            print('\tScanning %s' % img_path)

            bname = basename(splitext(img_path)[0])

            R, _ = detect(
                vehicle_net, vehicle_meta,
                bytes(img_path, encoding='utf-8'),
                thresh=vehicle_threshold)

            R = [r for r in R if r[0] in [
                b'car', b'bus', b'truck']]
                # b'car', b'bus', b'truck', b'motorbike']]

            print('\t\t%d vehicles found' % len(R))

            if len(R):

                Iorig = cv2.imread(img_path)
                WH = np.array(Iorig.shape[1::-1], dtype=float)
                Lcars = []

                for i, r in enumerate(R):

                    cx, cy, w, h = (
                        np.array(r[2])/np.concatenate((WH, WH))).tolist()
                    tl = np.array([cx - w/2., cy - h/2.])
                    br = np.array([cx + w/2., cy + h/2.])
                    label = Label(0, tl, br, category=r[0].decode("utf-8"))
                    Icar = crop_region(Iorig, label)

                    Lcars.append(label)

                    cv2.imwrite(
                        # '%s/%s_%dcar.png' % (output_dir, bname, i), Icar)
                        '%s/%s_car_%d.png' % (output_dir, bname, i), Icar)

                lwrite(
                    '%s/%s_cars.txt' % (output_dir, bname),
                    Lcars, write_category_names=True)

    except:
        traceback.print_exc()
        sys.exit(1)

    sys.exit(0)
