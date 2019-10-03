# Multi-stage Automatic License Plate Recognition

## Description

This software analyzes frames extracted from a video, detects and classfies
vehicles and their license plates (if visible) and extracts the license plate
codes.

It performs post processing to improve the recognized text in the plates, by
taking into account the detections in a window of N future and past frames.

It operates in 4 separate stages:

1. **Vehicle detection**: performs detections of vehicles in a frame. Currently
   implemented with a YOLO-v3 network using pretrained weights (no fine tuning).

1. **License plate detection**: performed on the crops obtained at the previous
   step. Two possible variants:

  1. A simple one using another YOLO-v3 network for object detection (trained on
     a dataset specific for license plates).

  1. A more sophisticate one using the approach described in
     (http://sergiomsilva.com/pubs/alpr-unconstrained/), where the license plate
     crop is also *unwarped* in order to compensate for the distortion due to
     the angle of the car with respect to the picture. This latter approach uses
     a network implemented using the Keras framework.

1. **OCR on license plate crop**: using a custom network (currently implemented
   with the darknet framework), perform

1. **Post-processing**: due to the license plate being occluded or moving
   farther away from the camera, readings on some frame might be wrong. However,
   it is possible to correct at least some of them by using information coming
   from previous or (if the script is supposed to be running in batch mode)
   subsequent frames.
   The post processing improves license plate reading and stability (less frame
   flickering) in two ways:
   * Correcting the license plate by taking the most reliable one read in the
     selected time window (the criterion used to decide which plate among
     several is the most likely to be the correct one for a vehicle is a mixture
     of frequency, i.e. in how many frames that code has been seen and plate
     correctedness, i.e. if it matches the regex expression for plates).
   * For occlusions, look for plates which appear in neighbouring frames but do
     not appear in current one, then estimate the position with a simple
     interpolation.

This repository also contains the scripts and libraries to draw labels
over the input frames (the frame over every recognized vehicle, the symbol
corresponding to that vehicle and the license plate number read).

## Usage

The first step is of course extracting frames from a video using a tool such as
`ffmpeg` or similar. The following command will most likely work for most
scenarios:

```shell
ffmpeg -i /path/to/video.mp4 frame-%04.png
```

A shell script is included and will take care of launching all steps of the
pipeline.

A video is also created at the end of the pipeline.

```shell
./full_pipeline.sh /path/to/frames
```

Another script (which is actually used by the one above) does the analysis
without creating the video, has a slightly different syntax:

```shell
./run-simple.sh -i /path/to/frames
```
