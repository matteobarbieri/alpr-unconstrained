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


if __name__ == '__main__':

    try:

        input_dir = sys.argv[1]
        output_dir = sys.argv[2]

        lp_threshold = .5

        lp_weights = b'data/simple-lp-detector/lapi.weights'
        lp_netcfg = b'data/simple-lp-detector/yolov3-lp.cfg'
        lp_dataset = b'data/simple-lp-detector/yolov3-lp.data'

        lp_net = dn.load_net(lp_netcfg, lp_weights, 0)
        lp_meta = dn.load_meta(lp_dataset)

        imgs_paths = image_files_from_folder(input_dir)
        # Filter only cropped car images
        imgs_paths.sort()

        if not isdir(output_dir):
            makedirs(output_dir)

        print('Searching for license plates in cropped cars using YOLO...')

        for i, img_path in enumerate(imgs_paths):

            print('\tScanning %s' % img_path)

            bname = basename(splitext(img_path)[0])

            R, _ = detect(
                lp_net, lp_meta,
                bytes(img_path, encoding='utf-8'),
                thresh=lp_threshold)

            # Only get "LP" classes (although there should be only that class)
            # R = [r for r in R if r[0] in [b'car', b'bus', b'truck']]
            R = [r for r in R if r[0] in [b'LP']]

            print('\t\t%d license plates found' % len(R))

            if len(R):

                Iorig = cv2.imread(img_path)
                WH = np.array(Iorig.shape[1::-1], dtype=float)
                Lcars = []

                for i, r in enumerate(R):

                    cx, cy, w, h = (
                        np.array(r[2])/np.concatenate((WH, WH))).tolist()
                    tl = np.array([cx - w/2., cy - h/2.])
                    br = np.array([cx + w/2., cy + h/2.])
                    label = Label(0, tl, br)
                    Icar = crop_region(Iorig, label)

                    Lcars.append(label)

                    cv2.imwrite(
                        '%s/%s_%d_lp.png' % (output_dir, bname, i), Icar)

                lwrite('%s/%s_lp.txt' % (output_dir, bname), Lcars)

    except:
        traceback.print_exc()
        sys.exit(1)

    sys.exit(0)
