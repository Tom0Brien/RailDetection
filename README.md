# Rail Detector

## Overview

Rail Detector is a program that uses LIDAR data to detect railway tracks and provides an interface for users to label, train, and interact with the data. The program is designed to make it easy to generate training data, interact with the results, and fix any issues in the detections.

## Features

- **Generation**: Generate unlabelled images of vertical projections of LIDAR data, extracted as grids from las files
- **Labelling**: Segmentation labelling tool for segmenting the unlabelled images
- **Training**: Tool to train neural network for detecting the rail lines
- **Interaction**: Tools for interacting with the detected rail lines and fixing of mis-detections and issues

## Installation

## Instructions

1. Add las files of rail track regions to the `data` folder.
2. Run `raildetector.py`