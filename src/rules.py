import re
import os
import time
from datetime import datetime
from typing import cast
from PIL import Image
from . import logic

from viam.components.camera import Camera
from viam.services.vision import VisionClient, Detection, Classification
from viam.logging import getLogger

LOGGER = getLogger(__name__)
CAM_BUFFER_SIZE = 150

class TimeRange():
    start_hour: int
    end_hour: int
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__dict__[key] = value

class RuleDetector():
    type: str="detection"
    detector: str
    cameras: list[str]
    class_regex: str
    confidence_pct: float
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__dict__[key] = value
class RuleClassifier():
    type: str="classification"
    classifier: str
    cameras: list[str]
    class_regex: str
    confidence_pct: float
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__dict__[key] = value

class RuleTime():
    type: str="time"
    ranges: list[TimeRange]
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, list):
                self.__dict__[key] = []
                for item in value:
                     self.__dict__[key].append(TimeRange(**item))
            else:
                self.__dict__[key] = value

async def eval_rule(rule:RuleTime|RuleDetector|RuleClassifier, event_name, resources):
    triggered = False

    match rule.type:
        case "time":
            curr_time = datetime.now()
            for r in rule.ranges:
                if (curr_time.hour >= r.start_hour) and (curr_time.hour < r.end_hour):
                    LOGGER.debug("Time triggered")
                    triggered = True   
        case "detection":
            detector = _get_vision_service(rule.detector, resources)
            for camera in rule.cameras:
                cam = _get_camera(camera, resources)
                img = await cam.get_image()
                _push_buffer(resources, camera, img, event_name)

                detections = await resources[detector].get_detections(img)
                d: Detection
                for d in detections:
                    if (d.confidence >= rule.confidence_pct) and re.search(rule.class_regex, d.class_name):
                        LOGGER.debug("Detection triggered")
                        triggered = True
        case "classification":
            classifier = _get_vision_service(rule.classifier, resources)
            for camera in rule.cameras:
                cam = _get_camera(camera, resources)
                img = await cam.get_image()
                _push_buffer(resources, camera, img, event_name)

                classifications = await resources[classifier].get_classifications(img, 3)
                c: Classification
                for c in classifications:
                    if (c.confidence >= rule.confidence_pct) and re.search(rule.class_regex, c.class_name):
                        LOGGER.debug("Classification triggered")
                        triggered = True

    return triggered

def logical_trigger(logic_type, list):
    logic_function = getattr(logic, logic_type)
    return logic_function(list)

def _get_camera(camera, resources):
    actual_camera = resources['_deps'][Camera.get_resource_name(camera)]
    if resources.get(actual_camera) == None:
        # initialize camera if it is not already
        resources[actual_camera] = cast(Camera, actual_camera)
    return resources[actual_camera]

def _get_vision_service(name, resources):
    actual = resources['_deps'][VisionClient.get_resource_name(name)]
    if resources.get(actual) == None:
        # initialize if it is not already
        resources[actual] = cast(VisionClient, actual)
    return resources[actual]

def _push_buffer(resources, camera, img, event_name):
    camera_buffer = (camera + event_name + "_buffer").replace(' ','_')
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
    img.save(out_dir + '/' + camera_buffer + '_' + str(resources[camera_buffer]) + '.jpg')
