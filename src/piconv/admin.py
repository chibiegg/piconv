# encoding=utf-8

from django.contrib import admin
from piconv.models import Attachment, Email

class AttachmentInline(admin.StackedInline):
    model = Attachment
    readonly_fields = ("created", "modified", "file")


class EmailAdmin(admin.ModelAdmin):
    inlines = [AttachmentInline, ]
    list_display = ("id", "sender", "subject")

admin.site.register(Email, EmailAdmin)

