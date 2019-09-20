#!/bin/bash

#VIDEO=$1
FRAMES_FOLDER=$1

# Create images with detections
#./run-simple.sh -i $FRAMES_FOLDER -o "${FRAMES_FOLDER}_out" -d
./run-simple.sh -i $FRAMES_FOLDER -d

# Create video starting from annotated frames
./create-video-from-frames.sh "${FRAMES_FOLDER}_out/results"
