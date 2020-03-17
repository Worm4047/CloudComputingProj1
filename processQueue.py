import boto3
from botocore.exceptions import ClientError
import logging
import subprocess
import string
import random
import time
import os
import time
import json
from ProgressPercentage import *
import logging
logging.basicConfig(filename='processQueue.log', level=logging.INFO)

PATH_DARKNET = "/home/ubuntu/darknet"
PATH_PROJ = "/home/ubuntu/CloudComputingProj1"


def download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME):
    s3 = boto3.client('s3')
    s3.download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)


def downloadFile(BUCKET_NAME, OBJECT_NAME, FILE_NAME):
    global ACCESS_KEY
    global SECRET_KEY
    global SESSION_TOKEN
    global REGION
    client = boto3.client('s3',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,aws_session_token=SESSION_TOKEN,region_name=REGION)
	# client.download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)
    client.download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)

def generate_random_object_name(stringLength = 10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def upload_file(file_name, bucket, object_name=None):
    global ACCESS_KEY
    global SECRET_KEY
    global SESSION_TOKEN
    global REGION
    client = boto3.client('s3',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,aws_session_token=SESSION_TOKEN,region_name=REGION)
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

def exportDisplay():
    command = 'Xvfb :1 & export DISPLAY=:1'
    process = subprocess.Popen(command, shell=True)
    process.wait()

def processMessages():
    
    download_file("wormcredentials", "cred.json", "cred.json")
    global ACCESS_KEY
    global SECRET_KEY
    global SESSION_TOKEN
    global REGION
    client = boto3.client('sqs',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,aws_session_token=SESSION_TOKEN,region_name=REGION)
    queue = client.get_queue_url(QueueName='video_queue')
    results = dict()
    # Process messages by printing out body and optional author name
    while True:
        li = []
        try:
            li = client.receive_message(QueueUrl=queue['QueueUrl'])['Messages']
            print(li)
        except Exception as e:
            pass
        for message in li:
            logging.info(message)
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
                    logging.error(e)
                    yield False, {}
            except Exception as e:
                logging.error(e)
                yield False, {}
            client.delete_message(QueueUrl=queue['QueueUrl'],ReceiptHandle=message['ReceiptHandle'])
        
            
        

if __name__ == '__main__':
    exportDisplay()
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
    for status, obj in processMessages():
        if(not status):
            logging.info("Got Error")
        else:
            for key in obj:
                with open(key+'.json', 'w') as outfile:
                    json.dump(obj, outfile)
                upload_file(key+'.json', BUCKET_NAME, key)

    os.chdir(PATH_PROJ)
