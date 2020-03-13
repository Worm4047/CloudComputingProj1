import logging
import boto3
from botocore.exceptions import ClientError
import random
import string
import time
from ProgressPercentage import *

def download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME):
    s3 = boto3.client('s3')
    s3.download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)

if __name__ =='__main__':
    start_time = time.time()
    BUCKET_NAME = "worm4047bucket1"
    FILE_NAME = "video1_downloaded.mp4"
    OBJECT_NAME = "kcyrdjyulz"
    download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)
    