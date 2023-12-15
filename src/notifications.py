import subprocess
import urllib.request

from email.message import EmailMessage

# att|verizon|sprint|tmobile|boost|metropcs
carrier_email_gateways = {
    "att": "mms.att.net",
    "verizon": "vzwpix.com",
    "sprint": "pm.sprint.com",
    "tmobile": "tmomail.net",
    "boost": "myboostmobile.com",
    "metropcs": "mymetropcs.com"
}

class NotificationSMS():
    type: str="sms"
    url: str
    carrier: str
    phone: str

class NotificationEmail():
    type: str="email"
    address: str

class NotificationWebhookGET():
    type: str="webhook_get"
    url: str

def notify(event_name:str, notification:NotificationEmail|NotificationSMS|NotificationWebhookGET):

    match notification.type:
        case "email":
            send_email(event_name, notification, False)
        case "sms":
            send_email(event_name, notification, True)
        case "webhook_get":
            contents = urllib.request.urlopen(notification.url).read()

    return


def send_email(event_name:str, notification:NotificationEmail|NotificationSMS, is_sms:bool):
    msg = EmailMessage()
    msg.set_content("Event triggered!")
    msg['From'] = "savcam@viam.com"
    if is_sms:
        to_address = notification.phone + "@" + carrier_email_gateways[notification.carrier]
    else:
        to_address = notification.address
    msg['To'] = to_address
    msg['Subject'] = "SAVCAM event: " + event_name

    sendmail_location = "/usr/sbin/sendmail"
    subprocess.run([sendmail_location, "-t", "-oi"], input=msg.as_bytes())