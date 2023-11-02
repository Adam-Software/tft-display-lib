#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import time
import logging
import RPi.GPIO as GPIO
import spidev as SPI
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import LCD_1inch28

class RobotEyeDisplay:
    def __init__(self):
        """
        Initialize the RobotEyeDisplay class.

        This class controls the robotic eye display on a Raspberry Pi.
        """
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(7, GPIO.OUT)
        GPIO.setup(24, GPIO.OUT)
        GPIO.output(7, 0)
        GPIO.output(24, 0)

        # LCD Configuration
        self.RST = 27
        self.DC = 25
        self.BL = 18
        self.bus = 0
        self.device = 0
        self.log = logging.getLogger(__name__)
        self.disp = self.init_display()

        image1 = Image.new("RGB", (self.disp.width, self.disp.height), color="Black")
        self.disp.ShowImage(image1)

    def init_display(self):
        """
        Initialize the LCD display using SPI.

        Returns:
            LCD_1inch28: Initialized LCD display object.
        """
        try:
            self.log.info("Initializing display...")
            disp = LCD_1inch28.LCD_1inch28(spi=SPI.SpiDev(self.bus, self.device))
            disp.Init()
            disp.clear()
            GPIO.output(7, 0)
            GPIO.output(24, 0)   
            self.log.info("Display initialized successfully.")
            return disp
        except Exception as e:
            self.log.error(f"Error initializing display: {e}")
            sys.exit(1)

    def load_frames(self, gif_path):
        """
        Load frames from a GIF.

        Args:
            gif_path (str): Path to the GIF file.

        Returns:
            list: List of frames from the GIF.
        """
        gif = Image.open(gif_path)
        frames = [frame.copy() for frame in ImageSequence.Iterator(gif)]
        return frames

    def display_frames(self, frames_R, frames_L):
        """
        Display frames on the robotic eyes.

        Args:
            frames_R (list): List of frames for the right eye.
            frames_L (list): List of frames for the left eye.
        """
        try:
            time.sleep(2.0)
            max_frames = max(len(frames_L), len(frames_R))

            for i in range(max_frames):
                if i < len(frames_L):
                    self.left_eye(frames_L[i])
                if i < len(frames_R):
                    self.right_eye(frames_R[i])

            time.sleep(3.0)
            GPIO.output(7, 0)
            GPIO.output(24, 0)

            self.log.info("Display closed.")
        except Exception as e:
            self.log.error(f"Error displaying frames: {e}")

    def right_eye(self, frame_R):
        """
        Display a frame on the right eye.

        Args:
            frame_R (PIL.Image.Image): Frame to display on the right eye.
        """
        frame_rgb_R = frame_R.convert('RGB')
        GPIO.output(7, 0)
        GPIO.output(24, 1)
        self.disp.ShowImage(frame_rgb_R)

    def left_eye(self, frame_L):
        """
        Display a frame on the left eye.

        Args:
            frame_L (PIL.Image.Image): Frame to display on the left eye.
        """
        GPIO.output(7, 1)
        GPIO.output(24, 0)
        frame_rgb_L = frame_L.convert('RGB')
        self.disp.ShowImage(frame_rgb_L)

    def run(self, gif_paths_R, gif_paths_L):
        """
        Run the robotic eye display animation.

        Args:
            gif_paths_R (list): List of paths to GIFs for the right eye.
            gif_paths_L (list): List of paths to GIFs for the left eye.
        """
        try:
            frames_R = [self.load_frames(gif_path) for gif_path in gif_paths_R]
            frames_L = [self.load_frames(gif_path) for gif_path in gif_paths_L]
            print(f'Number of frames in GIF: {len(frames_L)}, {len(frames_R)}')

            max_frames = max(len(frames_L), len(frames_R))

            for i in range(max_frames):
                if i < len(frames_R):
                    frames_R_set = frames_R[i]
                else:
                    frames_R_set = []

                if i < len(frames_L):
                    frames_L_set = frames_L[i]
                else:
                    frames_L_set = []

                self.display_frames(frames_R_set, frames_L_set)
        except KeyboardInterrupt:
            self.log.info("Keyboard interrupt detected. Exiting...")
        except Exception as e:
            self.log.error(f"An error occurred: {e}")
