import boto3
from botocore.exceptions import ClientError
import logging
import subprocess
import string
import random
import time
import os
import sys
import time
import json
from ProgressPercentage import *
import logging
logging.basicConfig(filename='processQueue.log', level=logging.INFO)

PATH_DARKNET = "/home/ubuntu/darknet"
PATH_PROJ = "/home/ubuntu/CloudComputingProj1"

def downloadFile(BUCKET_NAME, OBJECT_NAME, FILE_NAME):
    global ACCESS_KEY
    global SECRET_KEY
    global SESSION_TOKEN
    global REGION
    # client = boto3.client('s3',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,aws_session_token=SESSION_TOKEN,region_name=REGION)
	# client.download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)
    client = boto3.client('s3', region_name=REGION)
    client.download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)

def generate_random_object_name(stringLength = 10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def handleVisibility(client, queue_url, reciept_handle, value):
    try:
        response = client.change_message_visibility(
            QueueUrl= queue_url,
            ReceiptHandle=reciept_handle,
            VisibilityTimeout=value
        )
        print(response)
    except Exception as e:
        print(e)

def upload_file(file_name, bucket, object_name=None):
    global ACCESS_KEY
    global SECRET_KEY
    global SESSION_TOKEN
    global REGION
    client = boto3.client('s3',region_name=REGION)
    # client = boto3.client('s3',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,aws_session_token=SESSION_TOKEN,region_name=REGION)
    try:
        response = client.upload_file(file_name, bucket, object_name, Callback=ProgressPercentage(file_name))
    except ClientError as e:
        logging.error(e)
        return False, {}
    return True, object_name


def get_objects(FILENAME):
    logging.info(os.getcwd())
    f = open(FILENAME, 'r')
    temp_data = f.read().split('\n')
    data = dict()
    currfps = 0
    obj_in_frame = []
    for lines in temp_data:
        lines = lines.replace('\n', "")
        if 'FPS' in lines:
            if currfps > 0 and len(obj_in_frame) > 0:
                data[currfps] = (obj_in_frame)
                obj_in_frame = []
            currfps += 1
        elif '%' in lines:
            obj_in_frame.append(lines)
    result = dict()

    for key in data:
        object_map = []
        for obj in data[key]:
            obj_name, obj_conf = obj.split()
            obj_name = (obj_name.replace(':',''))
            obj_conf = (int)(obj_conf.replace('%',''))
            object_map.append({obj_name:(obj_conf*1.0)/100})
        result[key] = (object_map)
    return {'results' : [result]}

def processMessages(obj, reciept_handle):
    global ACCESS_KEY
    global SECRET_KEY
    global SESSION_TOKEN
    global REGION
    client = boto3.client('sqs', region_name=REGION)
    firstTime = True
    # client = boto3.client('sqs',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,aws_session_token=SESSION_TOKEN,region_name=REGION)
    queue = ''
    try:
        queue = client.get_queue_url(QueueName='video-process')
    except Exception as e:
        handleVisibility(client, "https://sqs.us-east-1.amazonaws.com/056594258736/video-process", reciept_handle, 0)
        print(e)
        return
    results = dict()
    
    # Process messages by printing out body and optional author name
    while True:
        li = []
        if firstTime:
            li = [{'Body':obj, 'ReceiptHandle':reciept_handle}]
            firstTime = False
        else:
            try:
                print("Looking for messages")
                li = client.receive_message(QueueUrl=queue['QueueUrl'], VisibilityTimeout=600)['Messages']
                if not li or len(li) == 0:
                    return
            except Exception as e:
                return 
        print("Processing Messages")
        for message in li:
            logging.info(message)
            print(message)
            object_name, bucket_name = message['Body'].split(':')
            logging.info("Processing " + object_name + " " +bucket_name)
            temp_file_name = object_name + '.h264'
            try:
                downloadFile(bucket_name, object_name, temp_file_name)
                FILENAME = "results.txt"
                try:
                    command = "./darknet detector demo cfg/coco.data cfg/yolov3-tiny.cfg yolov3-tiny.weights " + temp_file_name + " > results.txt" 
                    # command="ping google.com"
                    logging.info("Darknet started " + command )
                    start_time = time.time()
                    process = subprocess.Popen(command, shell=True)
                    process.wait()
                    logging.info("Darknet finished")
                    logging.info("--- %s seconds ---" % (time.time() - start_time))
                    object_list = get_objects(FILENAME)
                    results[object_name] = object_list
                    yield True, {object_name:object_list}
                except Exception as e:
                    handleVisibility(client,queue['QueueUrl'], message['ReceiptHandle'], 0)
                    print(e)
                    logging.error(e)
                    yield False, {}
            except Exception as e:
                handleVisibility(client,queue['QueueUrl'], message['ReceiptHandle'], 0)
                print(e)
                logging.error(e)
                yield False, {}
            client.delete_message(QueueUrl=queue['QueueUrl'],ReceiptHandle=message['ReceiptHandle'])
            time.sleep(10)
        
if __name__ == '__main__':
    cred_file = "cred.json"
    ACCESS_KEY, SECRET_KEY, SESSION_TOKEN, REGION = "", "", "", ""
    # downloadFile("wormcredentials", cred_file, cred_file)
    with open(cred_file) as f:
        data = json.load(f)
        ACCESS_KEY = data['aws_access_key_id']
        SECRET_KEY = data['aws_secret_access_key']
        SESSION_TOKEN = data['aws_session_token']
        REGION = data['region']

    os.chdir(PATH_DARKNET)
    res = []
    
    BUCKET_NAME = "worm4047bucket2"
    print(sys.argv[1], sys.argv[2])
    for val in processMessages(sys.argv[1], sys.argv[2]):
        if val is None:
            print("Done processing")
            logging.info("Done Processing")
        elif(not val[0]):
            logging.info("Got Error")
        else:
            status, obj = val[0], val[1]
            for key in obj:
                with open(key+'.json', 'w') as outfile:
                    json.dump(obj, outfile)
                upload_file(key+'.json', BUCKET_NAME, key)

    os.chdir(PATH_PROJ)