def get_objects(FILENAME):
    f = open(FILENAME, 'r')
    temp_data = f.read().split('\n')
    data = dict()
    currfps = 0
    obj_in_frame = []
    for lines in temp_data:
        lines = lines.replace('\n', "")
        if 'FPS' in lines:
            if currfps > 0:
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
if __name__ == '__main__':  
    FILENAME = 'test_video.txt'
    result = get_objects(FILENAME)
    fr = 0
    for key in result:
        for obj in result[key]:
            print(key, obj, result[key][obj])