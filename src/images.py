import os
import shutil
CAM_BUFFER_SIZE=150
ROOT_DIR = '/tmp'

def push_buffer(resources, cam_name, img):
    camera_buffer = _name_clean(cam_name)
    buffer_index_label = camera_buffer + '_buffer'
    if resources.get(buffer_index_label) == None:
        # set buffer position to 0
        resources[buffer_index_label] = 0
    else:
        resources[buffer_index_label] = resources[buffer_index_label] + 1
        if resources[buffer_index_label] >= CAM_BUFFER_SIZE:
            resources[buffer_index_label] = 0
    
    out_dir = ROOT_DIR + '/' + camera_buffer
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    img.save(out_dir + '/' + str(resources[buffer_index_label]) + '.jpg')

def copy_image_sequence(cam_name, event_name, event_id):
    camera_buffer = _name_clean(cam_name)
    src_dir = ROOT_DIR + '/' + camera_buffer
    out_dir = _name_clean(ROOT_DIR + '/' + event_name + '_' + camera_buffer + '_' + event_id)
    shutil.copytree(src_dir, out_dir)

def _name_clean(cam_name):
    return cam_name.replace(' ','_')