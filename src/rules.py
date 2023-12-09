from . import logic

class TimeRange():
    start_hour: int
    end_hour: int

class RuleDetector():
    type: str="detector"
    detector: str
    cameras: list[str]
    class_regex: str

class RuleClassifier():
    type: str="classifier"
    classifier: str
    cameras: list[str]
    class_regex: str

class RuleTime():
    type: str="time"
    ranges: list[TimeRange]

def eval_rule(rule):
    return

def logical_trigger(logic_type, list):
    logic_function = getattr(logic, logic_type)
    return logic_function(list)

