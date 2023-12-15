import re
from datetime import datetime
from typing import cast
from . import logic

from viam.components.camera import Camera
from viam.services.vision import VisionClient, Detection, Classification

class TimeRange():
    start_hour: int
    end_hour: int

class RuleDetector():
    type: str="detector"
    detector: str
    cameras: list[str]
    class_regex: str
    confidence_pct: float

class RuleClassifier():
    type: str="classifier"
    classifier: str
    cameras: list[str]
    class_regex: str
    confidence_pct: float

class RuleTime():
    type: str="time"
    ranges: list[TimeRange]

async def eval_rule(rule:RuleTime|RuleDetector|RuleClassifier, resources):
    triggered = False

    match rule.type:
        case "time":
            curr_time = datetime.now()
            for r in rule.ranges:
                if (curr_time.hour >= r.start_hour) and (curr_time.hour < r.end_hour):
                    triggered = True   
        case "detector":
            if resources.get(rule.detector) == None:
                # initialize detector if it is not already
                actual_detector = resources['_deps'][VisionClient.get_resource_name(rule.detector)]
                resources[rule.detector] = cast(VisionClient, actual_detector)
            for camera in rule.cameras:
                if resources.get(camera) == None:
                    # initialize camera if it is not already
                    actual_camera = resources['_deps'][Camera.get_resource_name(camera)]
                    resources[camera] = cast(Camera, actual_camera)
                img = await resources[camera].get_image()
                detections = await resources[rule.detector].get_detections(img)

                d: Detection
                for d in detections:
                    if (d.confidence >= rule.confidence_pct) and re.search(rule.class_regex, d.class_name):
                        triggered = True
        case "classifier":
            if resources.get(rule.classifier) == None:
                # initialize classifier if it is not already
                actual_classifier = resources['_deps'][VisionClient.get_resource_name(rule.classifier)]
                resources[rule.classifier] = cast(VisionClient, actual_classifier)
            for camera in rule.cameras:
                if resources.get(camera) == None:
                    # initialize camera if it is not already
                    actual_camera = resources['_deps'][Camera.get_resource_name(camera)]
                    resources[camera] = cast(Camera, actual_camera)
                img = await resources[camera].get_image()
                classifications = await resources[rule.classifier].get_classifications(img, 3)

                c: Classification
                for c in classifications:
                    if (c.confidence >= rule.confidence_pct) and re.search(rule.class_regex, c.class_name):
                        triggered = True
    return triggered

def logical_trigger(logic_type, list):
    logic_function = getattr(logic, logic_type)
    return logic_function(list)

