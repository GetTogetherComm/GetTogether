import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template, render_to_string
from django.urls import reverse
from django.utils import timezone

from accounts.models import EmailRecord
from events.models import Attendee, Event


class Command(BaseCommand):
    help = "Sends email to event hosts about new attendees"

    def handle(self, *args, **options):
        # Attendees who recently joined
        attendees = Attendee.objects.filter(
            role=Attendee.NORMAL,
            joined_date__gte=timezone.now() - datetime.timedelta(days=1),
        ).order_by("event")

        current_event = None
        new_attendees = []
        for attendee in attendees:

            if attendee.event != current_event:
                send_new_attendees(current_event, new_attendees)
                current_event = attendee.event
                new_attendees = []

            new_attendees.append(attendee)
        if current_event is not None:
            send_new_attendees(current_event, new_attendees)


def send_new_attendees(event, new_attendees):
    if len(new_attendees) < 1:
        return
    hosts = [
        attendee.user.user
        for attendee in Attendee.objects.filter(event=event, role=Attendee.HOST)
        if attendee.user.user.account.is_email_confirmed
    ]
    if len(hosts) < 1:
        return
    context = {
        "event": event,
        "attendees": new_attendees,
        "site": Site.objects.get(id=1),
    }

    email_subject = "New event attendees"
    email_body_text = render_to_string(
        "get_together/emails/events/new_event_attendees.txt", context
    )
    email_body_html = render_to_string(
        "get_together/emails/events/new_event_attendees.html", context
    )
    email_recipients = [host.email for host in hosts]
    email_from = getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@gettogether.community"
    )

    success = send_mail(
        from_email=email_from,
        html_message=email_body_html,
        message=email_body_text,
        recipient_list=email_recipients,
        subject=email_subject,
    )

    for host in hosts:
        EmailRecord.objects.create(
            sender=None,
            recipient=host,
            email=host.email,
            subject=email_subject,
            body=email_body_text,
            ok=success,
        )
