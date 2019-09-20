#!/bin/bash

FRAMES_FOLDER=$1

# Create video starting from annotated frames
ffmpeg -r 25 \
    -start_number 26 \
    -i "${FRAMES_FOLDER}/frame%05d_output.png" -c:v \
    libx264 -vf fps=25 -pix_fmt yuv420p \
    "${FRAMES_FOLDER}/output_unique.mp4"

