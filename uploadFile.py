import logging
import boto3
from botocore.exceptions import ClientError
import random
import string
import time
from ProgressPercentage import *
import json
import logging
import cv2
import numpy as np
import os
logging.basicConfig(filename='processQueue.log')
import sys

 
from os.path import isfile, join

def convert_frames_to_video(pathIn,pathOut,fps):
    frame_array = []
    # files = [f for f in os.listdir(pathIn) if isfile(join(pathIn, f))]
    vc = cv2.VideoCapture(pathIn)

    count = 0
    if vc.isOpened():
        width = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(vc.get(cv2.CAP_PROP_FPS))
        rval, frame = vc.read()
        result = [frame]
        while rval:
            count += 1
            rval, frame = vc.read()
            if count%10 == 0:
                result.append(frame)
        vc.release()

    out = cv2.VideoWriter(pathOut,cv2.VideoWriter_fourcc(*'XVID'), int(fps/10), (width,height))
    # for sorting the file names properly
    # files.sort(key = lambda x: int(x[5:-4]))
    for i in range(len(result)):
        out.write(result[i])
    out.release()

def generate_random_object_name(stringLength = 10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))




def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    if object_name == None:
        object_name = generate_random_object_name()

    # Upload the file
    global ACCESS_KEY
    global SECRET_KEY
    global SESSION_TOKEN
    global REGION
    s3_client = boto3.client('s3',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,aws_session_token=SESSION_TOKEN,)

    # s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name, Callback=ProgressPercentage(file_name))
    except ClientError as e:
        logging.error(e)
        return False, {}
    return True, object_name

def addToSqs(object_name, bucket_name):
    global ACCESS_KEY
    global SECRET_KEY
    global SESSION_TOKEN
    global REGION
    sqs = boto3.client('sqs',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,aws_session_token=SESSION_TOKEN,)

    queue = sqs.get_queue_url(QueueName='video_queue')
    try:
        sqs.send_message(QueueUrl=queue['QueueUrl'], MessageBody=object_name + ':' + bucket_name)
    except Exception as e:
        logging.error(e)
        return False
    return True

if __name__ =='__main__':
    start_time = time.time()
    cred_file = "cred.json"
    ACCESS_KEY, SECRET_KEY, SESSION_TOKEN, REGION = "", "", "", ""
    # downloadFile("wormcredentials", cred_file, cred_file)
    with open(cred_file) as f:
        data = json.load(f)
        ACCESS_KEY = data['aws_access_key_id']
        SECRET_KEY = data['aws_secret_access_key']
        SESSION_TOKEN = data['aws_session_token']
        REGION = data['region']
    BUCKET_NAME = "worm4047bucket1"
    VIDEO_FILE = sys.argv[1]
    VIDEO_FILE2 = "temp2.avi"
    try:
        os.remove(VIDEO_FILE2)
    except OSError:
        pass
    convert_frames_to_video(VIDEO_FILE, VIDEO_FILE2, 10)
    logging.info("Uploading to S3")
    result, obj = upload_file(VIDEO_FILE2, BUCKET_NAME)
    if(result):
        logging.info("Uploading to sqs ", obj)
        addToSqs(obj, BUCKET_NAME)
    else:
        logging.info("Upload to S3 failed")
    logging.info("--- %s seconds ---" % (time.time() - start_time))
    
