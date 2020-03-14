import logging
import boto3
from botocore.exceptions import ClientError
import random
import string
import time
from ProgressPercentage import *


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
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name, Callback=ProgressPercentage(file_name))
    except ClientError as e:
        logging.error(e)
        return False, {}
    return True, object_name

def addToSqs(object_name, bucket_name):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='video_queue')
    try:
        queue.send_message(MessageBody=object_name + ':' + bucket_name)
    except Exception as e:
        logging.error(e)
        return False
    return True

if __name__ =='__main__':
    start_time = time.time()
    BUCKET_NAME = "worm4047bucket1"
    VIDEO_FILE = "temp.h264"
    print("Uploading to S3")
    result, obj = upload_file(VIDEO_FILE, BUCKET_NAME)
    if(result):
        print("Uploading to sqs ", obj)
        addToSqs(obj, BUCKET_NAME)
    else:
        print("Upload to S3 failed")
    print("--- %s seconds ---" % (time.time() - start_time))
    
