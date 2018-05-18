from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string

from events.models import Event, EventSeries, Attendee
from accounts.models import EmailRecord

import time
import datetime

class Command(BaseCommand):
    help = "Generates the next event for any series that needs one"

    def handle(self, *args, **options):
        needs_update = EventSeries.objects.filter(last_time__lte=timezone.now())

        for series in needs_update:
            next_event = series.create_next_in_series()
            if next_event is not None:
                print("Created new event: %s" % next_event)
                email_host_new_event(next_event)


def email_host_new_event(event):
    context = {
        'event': event,
        'site': Site.objects.get(id=1),
    }
    email_subject = '[GetTogether] New event: %s' % event.name
    email_body_text = render_to_string('get_together/emails/events/event_from_series.txt', context)
    email_body_html = render_to_string('get_together/emails/events/event_from_series.html', context)
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

    for attendee in Attendee.objects.filter(event=event, role=Attendee.HOST, user__user__account__is_email_confirmed=True):
        success = send_mail(
            from_email=email_from,
            html_message=email_body_html,
            message=email_body_text,
            recipient_list=[attendee.user.user.email],
            subject=email_subject,
            fail_silently=True,
        )
        EmailRecord.objects.create(
            sender=None,
            recipient=attendee.user.user,
            email=attendee.user.user.email,
            subject=email_subject,
            body=email_body_text,
            ok=success
        )