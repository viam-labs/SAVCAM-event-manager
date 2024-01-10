import os
import shutil
import re
from viam.logging import getLogger

LOGGER = getLogger(__name__)

CAM_BUFFER_SIZE=75
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
    out_dir = _name_clean(ROOT_DIR + '/SAVCAM--' + event_name + '--' + camera_buffer + '--' + event_id)
    shutil.copytree(src_dir, out_dir)

async def get_triggered(camera:str=None, event:str=None, num:int=5):
    pattern = ROOT_DIR + '/SAVCAM--.*'
    if event != None:
        pattern = pattern + "--" + event + "--.*"
    if camera != None:
        pattern = pattern + "--" + camera + "--.*"

    dsearch = lambda f: (os.path.isdir(f) and re.match(pattern, f))
    ctime = lambda f: os.stat(os.path.join(ROOT_DIR, f)).st_ctime
    all_matched = sorted(filter(dsearch, [os.path.join(ROOT_DIR, f) for f in os.listdir(ROOT_DIR)]), key=ctime, reverse=True)
    matched = []
    if len(all_matched) < num:
        num = len(all_matched)
    for x in range(int(num)):
        spl = all_matched[x].split('--')
        matched.append({"event": spl[1].replace('_', ' '), "camera": spl[2], "time": spl[3], "id": all_matched[x].replace(ROOT_DIR + '/', '') })
    return matched

async def delete(camera:str=None, event:str=None):
    pattern = ROOT_DIR + '/SAVCAM--.*'
    if event != None:
        pattern = pattern + "--" + event + "--.*"
    if camera != None:
        pattern = pattern + "--" + camera + "--.*"

    dsearch = lambda f: (os.path.isdir(f) and re.match(pattern, f))
    all_matched = list(filter(dsearch, [os.path.join(ROOT_DIR, f) for f in os.listdir(ROOT_DIR)]))
    for x in range(len(all_matched)):
        shutil.rmtree(all_matched[x])
    return len(all_matched)

def _name_clean(cam_name):
    return cam_name.replace(' ','_')