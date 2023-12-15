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
    last_triggered: time = time.gmtime(0)
    modes: list = ["home"]
    debounce_interval_secs: int = 300
    rule_logic_type: str = 'AND'
    notifications: list[notifications.NotificationSMS|notifications.NotificationEmail|notifications.NotificationWebhookGET]
    rules: list[rules.RuleDetector|rules.RuleClassifier|rules.RuleTime]

class eventManager(Generic, Reconfigurable):
    
    """
    Generic component, which represents any type of component that can executes arbitrary commands
    """


    MODEL: ClassVar[Model] = Model(ModelFamily("viam-labs", "savcam"), "event-manager")
    
    mode: Modes = "home"
    events: list[Event]
    robot_resources: dict

    # Constructor
    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        my_class = cls(config.name)
        my_class.reconfigure(config, dependencies)
        return my_class

    # Validates JSON Configuration
    @classmethod
    def validate(cls, config: ComponentConfig):
        try:
            mode = Modes[config.attributes.fields["mode"].string_value]
        except:
            raise Exception("mode is invalid")
        return

    # Handles attribute reconfiguration
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        attributes = struct_to_dict(config.attributes)
        self.mode = Modes[attributes.get("mode")]
        self.events = attributes.get("events")
        self.robot_resources["_deps"] = dependencies
        asyncio.ensure_future(self.manage_events())
        return

    async def manage_events(self):
        while True:
            for event in self.events:
                if ((self.mode in event.modes) and ((event.is_triggered == False) or ((event.is_triggered == True) and ((time.time - event.last_triggered) >= event.debounce_interval_secs)))):
                    # reset trigger before evaluating
                    event.is_triggered = False
                    rule_results = []
                    for rule in event.rules:
                        rule_results.append(await rules.eval_rule(rule, self.robot_resources))
                    if rules.logical_trigger(event.rule_logic_type, rule_results):
                        event.is_triggered = True
                        event.last_triggered = time.time
                        for n in event.notifications:
                            notifications.notify(event.name, n)
                            return
        return
    
    async def do_command(
                self,
                command: Mapping[str, ValueTypes],
                *,
                timeout: Optional[float] = None,
                **kwargs
            ) -> Mapping[str, ValueTypes]:
        return