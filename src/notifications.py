class NotificationSMS():
    type: str="sms"
    url: str
    carrier: str
    phone: str

class NotificationEmail():
    type: str="email"
    url: str

class NotificationWebhookGET():
    type: str="webhook_get"
    address: str

def notify(rule_name:str, notification:NotificationEmail|NotificationSMS|NotificationWebhookGET):
    return