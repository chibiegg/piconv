# encoding=utf-8
import smtplib
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.Header import Header
from email.Utils import formatdate
from email import Encoders
import mimetypes

from django.conf import settings


def create_message(from_addr, to_addr, subject, body, encoding, files):
    msg = MIMEMultipart()
    msg['Subject'] = Header(subject, encoding)
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Date'] = formatdate()

    related = MIMEMultipart('related')
    alt = MIMEMultipart('alternative')
    related.attach(alt)

    content = MIMEText(body, 'plain', encoding)
    alt.attach(content)

    for file in files:
        filename = file.name
        attachment = MIMEBase(*mimetypes.guess_type(filename))
        attachment.set_payload(file.read())
        Encoders.encode_base64(attachment)
        related.attach(attachment)
        attachment.add_header("Content-Disposition", "attachment", filename=Header(filename, encoding).encode())

    msg.attach(related)
    return msg

def sendmail(from_addr, to_addr, msg):
    host = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
    s = smtplib.SMTP(host, 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
    s.sendmail(from_addr, [to_addr], msg.as_string())
    s.close()


