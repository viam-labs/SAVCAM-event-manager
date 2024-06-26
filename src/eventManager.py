from typing import ClassVar, Mapping, Sequence, Any, Dict, Optional, Tuple, Final, List, cast
from typing_extensions import Self
from typing import Final

from viam.module.types import Reconfigurable
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName, Vector3
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily

from viam.components.generic import Generic
from viam.utils import ValueTypes, struct_to_dict

from viam.logging import getLogger

from . import rules
from . import notifications
from . import triggered

import time
import asyncio
from enum import Enum

LOGGER = getLogger(__name__)

class Modes(Enum):
    home = 1
    away = 2

class Event():
    name: str
    is_triggered: bool = False
    last_triggered: float = 0
    modes: list = ["home"]
    debounce_interval_secs: int = 300
    rule_logic_type: str = 'AND'
    notifications: list[notifications.NotificationSMS|notifications.NotificationEmail|notifications.NotificationWebhookGET]
    rules: list[rules.RuleDetector|rules.RuleClassifier|rules.RuleTime]

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, list):
                if key == "notifications":
                    self.__dict__["notifications"] = []
                    for item in value:
                        if item["type"] == "sms":
                            self.__dict__[key].append(notifications.NotificationSMS(**item))
                        elif item["type"] == "email":
                            self.__dict__[key].append(notifications.NotificationEmail(**item))
                        elif item["type"] == "webhook_get":
                            self.__dict__[key].append(notifications.NotificationWebhookGET(**item))
                elif key == "rules":
                    self.__dict__["rules"] = []
                    for item in value:
                        if item["type"] == "detection":
                            self.__dict__[key].append(rules.RuleDetector(**item))
                        elif item["type"] == "classification":
                            self.__dict__[key].append(rules.RuleClassifier(**item))
                        elif item["type"] == "time":
                            self.__dict__[key].append(rules.RuleTime(**item))
                elif key == "modes":
                    self.__dict__["modes"] = []
                    for item in value:
                        self.__dict__[key].append(item)
            else:
                self.__dict__[key] = value

class eventManager(Generic, Reconfigurable):
    
    """
    Generic component, which represents any type of component that can executes arbitrary commands
    """


    MODEL: ClassVar[Model] = Model(ModelFamily("viam-labs", "savcam"), "event-manager")
    
    mode: Modes = "home"
    events = []
    robot_resources = {}
    run_loop = bool = True

    # Constructor
    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        my_class = cls(config.name)
        my_class.reconfigure(config, dependencies)
        return my_class

    # Validates JSON Configuration
    @classmethod
    def validate(cls, config: ComponentConfig):
        return

    # Handles attribute reconfiguration
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        self.run_loop = False
        attributes = struct_to_dict(config.attributes)
        if attributes.get("mode"):
            self.mode = attributes.get("mode")
        else:
            self.mode = 'home'

        self.events = []
        dict_events = attributes.get("events")
        if dict_events is not None:
            for e in dict_events:
                event = Event(**e)
                self.events.append(event)
        self.robot_resources['_deps'] = dependencies
        self.robot_resources['buffers'] = {}
        self.run_loop = True
        asyncio.ensure_future(self.manage_events())
        return

    async def manage_events(self):
        LOGGER.info("Starting SAVCAM event loop")
        while self.run_loop:
            event: Event
            for event in self.events:
                if ((self.mode in event.modes) and ((event.is_triggered == False) or ((event.is_triggered == True) and ((time.time() - event.last_triggered) >= event.debounce_interval_secs)))):
                    # reset trigger before evaluating
                    event.is_triggered = False
                    rule_results = []
                    for rule in event.rules:
                        result = await rules.eval_rule(rule, event.name, self.robot_resources)
                        rule_results.append(result)
                    if rules.logical_trigger(event.rule_logic_type, rule_results) == True:
                        event.is_triggered = True
                        event.last_triggered = time.time()
                        event_id = str(int(time.time()))
                        # sleep for a second in order to capture a bit more images
                        await asyncio.sleep(1)
                        # write image sequences leading up to event
                        rule_index = 0
                        for rule in event.rules:
                            if rule_results[rule_index] == True and hasattr(rule, 'cameras'):
                                for c in rule.cameras:
                                    triggered.copy_image_sequence(c, event.name, event_id)
                            rule_index = rule_index + 1
                        for n in event.notifications:
                            LOGGER.info(n.type)
                            notifications.notify(event.name, n)
                    await asyncio.sleep(.05)
                else:
                    await asyncio.sleep(.5)
    async def do_command(
                self,
                command: Mapping[str, ValueTypes],
                *,
                timeout: Optional[float] = None,
                **kwargs
            ) -> Mapping[str, ValueTypes]:
        result = {}
        for name, args in command.items():
            if name == "get_triggered":
                triggered_detail = await triggered.get_triggered(num=args.get("number",5), camera=args.get("camera",None), event=args.get("event",None))
                result["triggered"] = triggered_detail
            elif name == "clear_triggered":
                total = await triggered.delete(camera=args.get("camera",None), event=args.get("event",None), id=args.get("id",None))
                result["total"] = total
        return result  