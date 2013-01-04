# encoding=utf-8

import os
import imaplib
import datetime
import email
import email.Header
import cStringIO
import mimetypes
from PIL import Image


from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from piconv.models import Email, Attachment

class ImapMail(object):
    def __init__(self, data):
        self.data = data[0][1]

        msg = email.message_from_string(self.data)

        self.files = {}
        self.message_id = self.decode(msg.get('Message-ID'))
        self.subject = self.decode(msg.get('Subject'))
        self.sender = self.decode(msg.get('From'))
        self.to = self.decode(msg.get('To'))
        self.date = self.get_format_date(msg.get('Date'))

        #添付ファイル,本文
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue

            #ファイル名を取得
            filename = part.get_filename()

            #ファイル名が取得できなければ本文
            if not filename:
                self.body = self.decode_body(part)

            #ファイル名が存在すれば添付ファイル
            else:
                tmpfile = cStringIO.StringIO()
                tmpfile.write(part.get_payload(decode=1))
                filename = self.decode(filename)
                self.files[filename] = tmpfile

    def decode(self, dec_target):
        decodefrag = email.Header.decode_header(dec_target)
        s = u""
        for frag, enc in decodefrag:
            if enc:
                s += unicode(frag, enc)
            else:
                s += unicode(frag)
        return s

    def decode_body(self, part):
        body = u""
        charset = str(part.get_content_charset())
        if charset:
            body = unicode(part.get_payload(), charset)
        else:
            body = part.get_payload()
        return body

    def get_format_date(self, date_string):
        """
        メールの日付をtimeに変換
        http://www.faqs.org/rfcs/rfc2822.html
        "Jan" / "Feb" / "Mar" / "Apr" /"May" / "Jun" / "Jul" / "Aug" /"Sep" / "Oct" / "Nov" / "Dec"
        Wed, 12 Dec 2007 19:18:10 +0900
        """
        format_pattern = '%a, %d %b %Y %H:%M:%S'
        #3 Jan 2012 17:58:09という形式でくるパターンもあるので、
        #先頭が数値だったらパターンを変更
        if date_string[0].isdigit():
            format_pattern = '%d %b %Y %H:%M:%S'
        return datetime.datetime.strptime(date_string[0:-6], format_pattern)

class Command(BaseCommand):

    def handle(self, *args, **options):

        host = getattr(settings, "IMAP_HOST", u"imap.gmail.com")
        username = settings.EMAIL_USERNAME
        password = settings.EMAIL_PASSWORD
        email_addr = args[0]
        format = args[1]

        #ログイン
        imap = imaplib.IMAP4_SSL(host)
        imap.login(username, password)
        imap.list()
        imap.select("inbox")

        #未読メールを取得
        result, data = imap.search(None, 'UnSeen', '(TO "%s")' % email_addr)

        for index in data[0].split():
            resp, data = imap.fetch(index, "(RFC822)")
            mail = ImapMail(data)


            defaults = {
                        "subject": mail.subject,
                        "sender": mail.sender,
                        "to": mail.to,
                        "date": mail.date,
                        "body":mail.body,
                        }
            email, created = Email.objects.get_or_create(message_id=mail.message_id, defaults=defaults)

            if created:
                for filename, obj in mail.files.items():
                    content_type, subType = mimetypes.guess_type(filename)
                    defaults = {"file":SimpleUploadedFile(filename, obj.getvalue(), content_type=content_type)}
                    attachment, created = Attachment.objects.get_or_create(email=email, filename=filename, defaults=defaults)

                email.send_reply(format)
                print email






