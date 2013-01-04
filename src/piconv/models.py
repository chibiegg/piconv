    # encoding=utf-8

from PIL import Image
import StringIO
from os import path

from django.db import models
from django.conf import settings

from piconv.sendmail import create_message, sendmail

class NamedStringIO(StringIO.StringIO):
    name = u""
    def __init__(self, name, buffer_=None):
        StringIO.StringIO.__init__(self, buffer_)
        self.name = name

class Email(models.Model):

    class Meta:
        verbose_name = verbose_name_plural = u"メール"
        ordering = ("-created",)

    created = models.DateTimeField(u"登録受信日時", auto_now_add=True)
    modified = models.DateTimeField(u"修正日時", auto_now=True)

    #メール
    message_id = models.CharField(u"Message-ID", max_length=200, unique=True)
    subject = models.TextField(u"件名", blank=True)
    sender = models.EmailField(u"送信者", max_length=512)
    to = models.EmailField(u"送信先", max_length=512)
    date = models.DateTimeField(u"送信日時")
    body = models.TextField(u"本文", blank=True)

    #内部情報
    replied = models.BooleanField(u"返信済み", default=False, blank=True)
    reply_body = models.TextField(u"返信内容", blank=True)
    note = models.TextField(u"備考", blank=True)
    error = models.BooleanField(u"エラーあり", default=False, blank=True)
    error_message = models.TextField(u"エラー内容", blank=True)

    def __unicode__(self):
        return u"[%s] Subject:%s ID:%s" % (self.sender, self.subject, self.message_id)

    def send_reply(self, format="jpg", force=False):
        """画像を変換して返信する"""
        if self.replied and not force:
            #送信済み
            return

        subject = u"[画像変換] Re:%s" % (self.subject,)
        body = u"Piconvをご利用いただきありがとうございます．"

        files = {}
        error_files = []

        if self.attachment_set.all().count() == 0:
            #添付ファイルが無かった
            body += u"\n\n添付ファイルがありませんでした．\n画像ファイルを添付して送信しなおしてください．"
        else:
            for attachement in self.attachment_set.all():
                try:
                    image = Image.open(attachement.file).convert("RGB")
                    filename = path.splitext(attachement.filename)[0] + u"." + format
                    file = NamedStringIO(filename)
                    image.save(file)
                    file.seek(0)
                    files[attachement.filename] = file
                except IOError:
                    #画像のオープンに失敗
                    error_files.append(attachement)

            if files:
                #成功したファイルがある
                body += u"\n\n次のファイルを変換しました．\n"
                for filename in files.keys():
                    body += u"・%s\n" % filename


            if error_files:
                #エラーがある
                body += u"\n\n次のファイルの変換に失敗しました．\n"
                for attachement in error_files:
                    body += u"・%s\n" % attachement.filename

        body += u"\n" + getattr(settings, "EMAIL_FOOTER", u"")

        #メール送信
        sender = self.to
        to = self.sender

        msg = create_message(sender, to, subject, body, 'utf-8', files.values())
        sendmail(sender, to, msg)

        self.replied = True
        self.reply_body = body
        self.save()


class Attachment(models.Model):

    class Meta:
        verbose_name = verbose_name_plural = u"添付ファイル"

    created = models.DateTimeField(u"登録受信日時", auto_now_add=True)
    modified = models.DateTimeField(u"修正日時", auto_now=True)
    email = models.ForeignKey(Email, verbose_name=u"メール")
    filename = models.CharField(u"オリジナルファイル名", max_length=512)
    file = models.FileField(u"ファイル", upload_to=u"attachment/%Y/%m/%d", max_length=512)



