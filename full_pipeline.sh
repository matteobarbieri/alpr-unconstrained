#!/bin/bash

#VIDEO=$1
FRAMES_FOLDER=$1

# Create images with detections
./run-simple.sh -i $FRAMES_FOLDER -o "${FRAMES_FOLDER}_out" -c /tmp/aaa.csv

# Create video starting from annotated frames
ffmpeg -r 25 -i "${FRAMES_FOLDER}_out/frame%05d_output.png" -c:v \
    libx264 -vf fps=25 -pix_fmt yuv420p \
    "${FRAMES_FOLDER}_out/output.mp4"

