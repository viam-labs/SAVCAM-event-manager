import os
import shutil
import re
import asyncio
from PIL import Image 
import io

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
    return out_dir

async def send_data(cam_name, event_name, event_id, app_client, part_id, path):
    start_index = _get_oldest_image_index(path)
    end_index = _get_greatest_image_index(path)
    LOGGER.error(f"START {start_index} END {end_index}")
    index = start_index
    sent_all = False
    while sent_all == False:
        f = str(index) + '.jpg'
        im = Image.open(os.path.join(path, f))
        buf = io.BytesIO()
        im.save(buf, format='JPEG')
        await app_client.data_client.file_upload(part_id=part_id, file_extension=".jpg", tags=[_name_clean(f"SAVCAM--{event_name}--{cam_name}--{event_id}")], data=buf.getvalue())
        index = index + 1
        if index == start_index:
            sent_all = True 
        if index > end_index:
            index = 0
    shutil.rmtree(path)
    return

def _get_oldest_image_index(requested_dir):
    mtime = lambda f: os.stat(os.path.join(requested_dir, f)).st_mtime
    return int(os.path.splitext(list(sorted(os.listdir(requested_dir), key=mtime))[0])[0])

def _get_greatest_image_index(requested_dir):
    index = lambda f: int(os.path.splitext(os.path.basename(os.path.splitext(os.path.join(requested_dir, f))[0]))[0])
    return int(os.path.splitext(list(sorted(os.listdir(requested_dir), key=index))[-1])[0])
    
async def get_triggered(camera:str=None, event:str=None, num:int=5):
    pattern = _create_match_pattern(camera, event, None)

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

async def delete(camera:str=None, event:str=None, id:str=None):
    pattern = _create_match_pattern(camera, event, id)

    dsearch = lambda f: (os.path.isdir(f) and re.match(pattern, f))
    all_matched = list(filter(dsearch, [os.path.join(ROOT_DIR, f) for f in os.listdir(ROOT_DIR)]))
    for x in range(len(all_matched)):
        shutil.rmtree(all_matched[x])
    return len(all_matched)

def _name_clean(cam_name):
    return cam_name.replace(' ','_')

def _create_match_pattern(camera:str=None, event:str=None, id:str=None):
    pattern = ROOT_DIR + '/SAVCAM--'
    if event != None:
        pattern = pattern + event + "--"
    else:
        pattern = pattern + ".*--"
    if camera != None:
        pattern = pattern + camera + "--.*"
    else:
        pattern = pattern + ".*--.*"
    if id != None:
        pattern = ROOT_DIR + '/' + id
    return pattern