# Number Plate Detection System

## Overview

This project is a number plate detection system that uses OpenCV and Tesseract OCR to read and process vehicle number plates from live video feeds. The system interacts with ThingSpeak for data storage and management. It tracks entry and exit times, calculates parking duration, and generates the amount to be paid based on the duration.

## Features

- Real-time number plate detection using OpenCV and Tesseract OCR
- Integration with ThingSpeak for storing and retrieving data
- Calculation of parking duration and amount to be paid
- Handles both entry and exit of vehicles
- Validates number plates using a regex pattern

## Requirements

- Python 3.x
- `opencv-python` library
- `pytesseract` library
- `requests` library
- Tesseract OCR installed on your system

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/Number-Plate.git
