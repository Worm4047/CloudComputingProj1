import boto3
from botocore.exceptions import ClientError
import logging
import subprocess
import string
import random
import time
import os

PATH_DARKNET = "/home/ubuntu/darknet"
PATH_PROJ = "/home/ubuntu/CloudComputingProj1"

def downloadFile(BUCKET_NAME, OBJECT_NAME, FILE_NAME):
	s3 = boto3.client('s3')
	s3.download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)

def generate_random_object_name(stringLength = 10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def get_objects(FILENAME):
    print(os.getcwd())
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

def processMessages():
    print(os.getcwd())
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='video_queue')
    results = dict()
    # Process messages by printing out body and optional author name
    while True:
        for message in queue.receive_messages():
            object_name, bucket_name = message.body.split(':')
            print("Processing ", object_name, bucket_name)
            temp_file_name = object_name + '.h264'
            try:
                downloadFile(bucket_name, object_name, temp_file_name)
                FILENAME = "results.txt"
                try:
                    command = "./darknet detector demo cfg/coco.data cfg/yolov3-tiny.cfg yolov3-tiny.weights " + temp_file_name + " > results.txt" 
                    print("Darknet started ", command)
                    start_time = time.time()
                    process = subprocess.Popen(command, shell=True)
                    process.wait()
                    print("Darknet finished")
                    print("--- %s seconds ---" % (time.time() - start_time))
                    object_list = get_objects(FILENAME)
                    results[object_name] = object_list
                except Exception as e:
                    logging.error(e)
                    yield False, {}
            except Exception as e:
                logging.error(e)
                yield False, {}
            message.delete()
        yield True, results    
        

if __name__ == '__main__':
    # os.chdir(PATH_DARKNET)
    status, obj = processMessages()
    # os.chdir(PATH_PROJ)
    if(not status):
        print("Got Error")
    else:
        print(obj)
