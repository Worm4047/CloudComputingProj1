#!/usr/bin/python

'''
SETUP:

    -   -->     GND     -->     PIN6
    +   -->     5V      -->     PIN4
    S   -->     GPIO18  -->     PIN12

'''

import RPi.GPIO as GPIO
import subprocess
import time
import sys
import os

sensor = 12
PATH_CLOUD = "/home/pi/CloudComputingProj1"
PATH_FACEDETECT = "/home/pi/facedetect"
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(sensor, GPIO.IN)

on = 0
off = 0
flag = 0
while True:
    time.sleep(5)
    i=GPIO.input(sensor)
    if i == 0:
        off = time.time()
        diff = off - on
        print 'time: ' + str(diff%60) + ' sec'
        print ''
        print "No intruders"
        time.sleep(1)
    elif i == 1:
        print "Intruder detected"
        on = time.time()
        flag = 1
        process = subprocess.Popen('python take_snapshot.py v.h264', shell=True)
        process.wait()
        os.chdir(PATH_CLOUD)
        process = subprocess.Popen('python uploadFile.py ' + PATH_FACEDETECT+'/v.h264', shell=True)
        process.wait()
        os.chdir(PATH_FACEDETECT)
        time.sleep(0.1)
