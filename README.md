# SAVCAM event-manager modular service

*event-manager* is a Viam modular component that provides eventing capabilities for SAVCAM (Smart AI Viam Camera) using the generic component API.

The model this module makes available is viam-labs:savcam:event-manager

The SAVCAM event manager is normally used in conjunction with the [SAVCAM mobile app[(https://github.com/viam-labs/SAVCAM-app), which provides a user interface for configuring events, viewing camera feeds, and viewing alerts.

## Prerequisites

None

## API

The event-manager resource implements the [rdk generic API](https://github.com/viamrobotics/api/blob/main/proto/viam/component/generic/v1/generic.proto).

### do_command()

Examples:

```python
await em.do_command({"get_triggered": {"number": 5}}) # get 5 most recent triggered across all configured events
await em.do_command({"get_triggered": {"number": 5, "camera": "ipcam"}}) # get 5 most recent triggered for "ipcam" across all configured events
await em.do_command({"get_triggered": {"number": 5, "event": "Pets out at night"}}) # get 5 most recent triggers for event "Pets out at night"

await em.do_command({"clear_triggered": {}}) # clear all triggered cross all configured events
await em.do_command({"clear_triggered": {"id": "SAVCAM--my_event--ipcam--1705448784"}}) # clear a specific triggered event
await em.do_command({"clear_triggered": {"camera": "ipcam"}}) # clear all triggered for "ipcam" across all configured events
await em.do_command({"clear_triggered": {"event": "Pets out at night"}}) # clear all triggered for event "Pets out at night"
```

#### get_triggered

Return details for triggered events in the following format:

```json
{ "triggered": 
    [
        {
            "event": "Pets out at night",
            "camera": "ipcam",
            "time": 1703172467,
            "id": "Pets_out_at_night_ipcam_1703172467"
        }
    ] 
}
```

Note that "id" can be passed to a properly configured Viam [image-dir-cam](https://app.viam.com/module/viam-labs/image-dir-cam) as the "dir" *extra* param in order to view the captured camera stream.

The following arguments are supported:

*number* integer

Number of triggered to return - default 5

*camera* string

Name of camera to return triggered for.  If not specified, will return triggered across all cameras.

*event* string

Name of event to return triggered for.  If not specified, will return triggered across all events.

#### clear_triggered

Clear triggered events, returning results details in the following format:

```json
{
  "total": 10
}
```

The following arguments are supported:

*camera* string

Name of camera to delete triggered for.  If not specified, will delete triggered across all cameras.

*event* string

Name of event to delete triggered for.  If not specified, will delete triggered across all events.

*id* string

ID of event to delete triggered for. If not specified, will delete triggered across all events and cameras (depending on what is passed for *event* and *camera*)

## Viam Service Configuration

The service configuration uses JSON to describe rules around events.
The following example configures a single event named "Pets out at night" that triggers when an configured Vision services sees a cat or dog at night, sending an SMS and IFTTT webhook.

```json
{
    "mode": "home",
    "use_data_management": true,
    "part_id": "mhj127",
    "app_api_key": "my_app_key",
    "app_api_key_id": "my_api_key_id",
    "events": [
        {
            "name": "Pets out at night",
            "modes": ["home", "away"],
            "debounce_interval_secs": 300,
            "rule_logic_type": "AND",
            "notifications": [
                {
                    "type": "webhook_get",
                    "url": "https://maker.ifttt.com/trigger/person_seen/json/with/key/cg5po9SnvoE98ahpZ7j-JE"
                },
                {
                    "type": "sms",
                    "carrier": "att",
                    "phone": "9175550100"
                }
            ],
            "rules": [
                {
                    "type": "detection",
                    "detector": "effdet",
                    "confidence_pct": 0.8,
                    "class_regex": "cat|dog",                    
                    "cameras": ["cam1", "cam2"]
                },
                {
                    "type": "time",
                    "ranges": [
                        {
                            "start_hour": 0,
                            "end_hour": 8 
                        }
                    ]
                }
            ]
        }
    ]
}
```

Note that you will need to include specified required cameras or other components/services in the `depends_on` array for the configuration, for example:

```json
      "depends_on": [
        "cam1", "cam2"
      ]
```

### mode

*enum home|away (default: "home")*

Event manager mode, which is used in event evaluation based on configured event [modes](#modes)

### use_data_management

*boolean (default:false)*

If set to true, will store image data and read image metadata from Viam data management.
If false, will use disk storage.
If true "part_id", "app_api_key", "app_api_key_id" must all be set.

### events

*list*

Any number of events can be configured, and will be repeatedly evaluated.
If an event evaluates to true, it will be tracked, and any configured notifications will occur.

### name

*string (required)*

Label for the configured event.
Used in logging and notifications.

#### modes

*list[enum home|away] (required)*

The list of modes in which this event will be evaluated.

#### rule_logic_type

*enum AND|OR|XOR|NOR|NAND|XNOR (default AND)*

The [logic gate](https://www.techtarget.com/whatis/definition/logic-gate-AND-OR-XOR-NOT-NAND-NOR-and-XNOR) to use with configured rules.
For example, if *NOR* was set and there were two rules configured that both evaluated false, the event would trigger.

#### debounce_interval_secs

*integer (default 300)*

After an event is triggered, how long (in seconds) before it can trigger again.

#### notifications

*list*

Notifications define actions to take when an event triggers.

##### notification type

*enum webhook_get|sms|email (required)*

If type is **webhook_get**, *url* must be provided, which is an HTTP(S) URL that will be called via GET to trigger a webhook.

If type is **email**, *address* must be provided, which is a valid email address.

If type is **sms**, *carrier* and *phone* must be provided. *carrier* supports att|verizon|sprint|tmobile|boost|metropcs via [email-to-sms](https://avtech.com/articles/138/list-of-email-to-sms-addresses/)

#### rules

*list*

Rules define what is evaluated in order to trigger event logging and notifications.
Any number of rules can be configured for a given event.

##### rule type

*enum detection|classification|time*

If *type* is **detection**, *detector* (name of vision service detector), *cameras* (list of configured cameras), *confidence_pct* (percent confidence threshold out of 1), and *class_regex* (regular expression to match detection class, defaults to any class) must be defined.
Note that detector and cameras must be configured in *depends_on*.

If *type* is **classification**, *classifier* (name of vision service classifier), *cameras* (list of configured cameras), *confidence_pct* (percent confidence threshold out of 1), and *class_regex* (regular expression to match detection class, defaults to any class) must be defined.
Note that classifier and cameras must be configured in *depends_on*.

If *type* is **time**, *ranges* must be defined, which is a list of *start_hour* and *end_hour*, which are integers representing the start hour in UTC.

## Todo

- Support storing data in Viam's cloud Data Service
- Support other types of webhooks
- Allow using 3rd-party email and SMS services for more reliable delivery
- Include image in SMS/emails
