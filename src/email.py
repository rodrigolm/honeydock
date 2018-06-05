import smtplib

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


def send_email_alert(attacker_ip: str, option: int) -> None:
    """Sends an email when a new connection is created"""

    fromaddr = ""
    toaddr = ""
    msg = MIMEMultipart()
    msg["From"] = fromaddr
    msg["To"] = toaddr
    msg["Subject"] = "HoneyDock Attack Alert"

    if option == 1:
        body = "HoneyDock just received a new connection from: " + attacker_ip
    else:
        body = "HoneyDock just received another connection from: " + attacker_ip

    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("", 587)
    server.starttls()
    server.login("", "")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
