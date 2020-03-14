def get_objects(FILENAME):
    f = open(FILENAME, 'r')
    temp_data = f.read().split('\n')
    temp_data.reverse()
    data = []
    for lines in temp_data:
        lines = lines.replace('\n', "")
        if 'Objects:' in lines:
            break
        if len(lines) > 0:
            data.append(lines)

    object_map = dict()
    for obj in data:
        obj_name, obj_conf = obj.split()
        obj_name = (obj_name.replace(':',''))
        obj_conf = (int)(obj_conf.replace('%',''))
        object_map[obj_name] = (obj_conf*1.0)/100
    print(object_map)
    return object_map
if __name__ == '__main__':  
    FILENAME = 'test_video.txt'
    object_map = get_objects(FILENAME)