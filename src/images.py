import os
import shutil
CAM_BUFFER_SIZE=150

def push_buffer(resources, camera, img, event_name):
    camera_buffer = _camera_buffer_dir(camera, event_name)
    if resources.get(camera_buffer) == None:
        # set buffer position to 0
        resources[camera_buffer] = 0
    else:
        resources[camera_buffer] = resources[camera_buffer] + 1
        if resources[camera_buffer] >= CAM_BUFFER_SIZE:
            resources[camera_buffer] = 0
    
    out_dir = '/tmp/' + camera_buffer
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    img.save(out_dir + '/' + str(resources[camera_buffer]) + '.jpg')

def copy_image_sequence(camera, event_name, event_id):
    camera_buffer = _camera_buffer_dir(camera, event_name)
    src_dir = '/tmp/' + camera_buffer
    out_dir = src_dir + '_' + event_id
    shutil.copytree(src_dir, out_dir)

def _camera_buffer_dir(camera, event_name):
    return (event_name + '_' + camera).replace(' ','_')