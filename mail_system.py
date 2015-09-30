## -- Time to Split -- ##
import sys
import random


from django.contrib.sites.models import Site
from django.core.mail import send_mail, send_mass_mail
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template.base import Template as T, Context
from django.utils.text import slugify
from django.conf import settings

from functions import primary_source


def render_email(announcement, profile):
    site = Site.objects.get(pk=1)
    glean = announcement.glean
    glean_link = "<a href='{0}'>Glean Info</a>".format(glean.url)
    template = T(announcement.template.body)
    context = Context(
        {
            "custom": announcement.message,
            "glean": glean,
            'date': glean.date.strftime('%A, %B %d'),
            'info': glean_link,
            'raw_glean_link': glean.url,
            "unsubscribe_url": profile.unsubscribe_url,
            "unsubscribe": profile.stock_unsubscribe_link,
            "email": profile.user.email
        }
    )
    body = template.render(context)
    return body


#== Mailing Logic ==#
def quick_mail(subject, text, recipient):
    msg = EmailMessage(
        subject,
        text,
        'no-reply@vermontgleaningcollective.org',
        [recipient]
    )
    msg.content_subtype = "html"
    msg.send()


def mail_from_source(announcement):
        mo = announcement.member_organization
        glean = announcement.glean

        from_address = "{name} <{email}>".format(
            name=mo.name,
            email=settings.ANNOUNCEMENT_FROM_EMAIL
        )

        if announcement.title:
            subject = announcement.title
        else:
            subject = glean.title
        count = 0

        if mo.testing:
            for recipient in announcement.email_recipients.all():
                profile = recipient.profile
                body = render_email(announcement, profile)
                if recipient not in glean.invited_volunteers.all():
                    glean.invited_volunteers.add(recipient)

            if mo.testing_email:
                profile = announcement.glean.created_by.profile
                body = render_email(announcement, profile)
                msg = EmailMessage(
                    subject,
                    body,
                    from_address,
                    [mo.testing_email]
                )
                msg.content_subtype = "html"
                msg.send()
                count += 1

        else:
            for recipient in announcement.email_recipients.all():
                profile = recipient.profile
                body = render_email(announcement, profile)
                msg = EmailMessage(
                    subject,
                    body,
                    from_address,
                    [recipient.email]
                )
                msg.content_subtype = "html"
                msg.send()
                count += 1
                if recipient not in glean.invited_volunteers.all():
                    glean.invited_volunteers.add(recipient)
            for recipient in announcement.phone_recipients.all():
                if recipient not in glean.invited_volunteers.all():
                    glean.invited_volunteers.add(recipient)
        glean.save()
        return count
