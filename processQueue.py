import boto3
from botocore.exceptions import ClientError
import logging
import subprocess


def downloadFile(BUCKET_NAME, OBJECT_NAME, FILE_NAME):
    s3 = boto3.client('s3')
    s3.download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)


def get_objects(FILENAME):
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
        object_map = dict()
        for obj in data[key]:
            obj_name, obj_conf = obj.split()
            obj_name = (obj_name.replace(':',''))
            obj_conf = (int)(obj_conf.replace('%',''))
            object_map[obj_name] = (obj_conf*1.0)/100
        result[key] = (object_map)
    return result

def processMessages():
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='video_queue')
    results = dict()
    # Process messages by printing out body and optional author name
    for message in queue.receive_messages():
        object_name, bucket_name = message.body.split(':')
        print("Processing ", object_name, bucket_name)
        temp_file_name = object_name + '.h264'
        try:
            # downloadFile(bucket_name, object_name, temp_file_name)
            FILENAME = 'test_video.txt'
            try:
                print("Darknet started")
                process = subprocess.Popen("ping google.com", shell=False)
                process.wait()
                print("Darknet finished")
                object_list = get_objects(FILENAME)
                results[object_name] = object_list
                pass
            except Exception as e:
                logging.error(" Error with get_objects " + e)
                return False, {}
        except Exception as e:
            logging.error(" Error with download File " + e)
            return False, {}
    return True, results    
        # message.delete()

if __name__ == '__main__':
    status, obj = processMessages()
    if(not status):
        print("Got Error")
    else:
        print(obj)