from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils import timezone
from django.db.models import Q

from accounts.models import Account, EmailConfirmation
from events.models import Event, Attendee

import time
import urllib
import datetime

class Command(BaseCommand):
    help = "Sends upcomming event notifications to attendees."

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)

        # Events that start within a day.
        query = Q(status=Attendee.YES,
                  event__start_time__gt=timezone.now())

        attendees = Attendee.objects.filter(query)

        for attendee in attendees:
            
            # Skip people who don't want notificiations or have no email address.
            if not attendee.user.send_notifications or not attendee.user.user.email:
                continue

            # Skip people who have been reminded in the last day.
            if attendee.last_reminded and timezone.now() > attendee.last_reminded - datetime.timedelta(days=1):
                continue

            context = {
                'event': attendee.event,
            }

            email_subject = '[GetTogether] Upcoming event reminder'
            email_body_text = render_to_string('get_together/emails/reminder.txt', context)
            email_body_html = render_to_string('get_together/emails/reminder.html', context)
            email_recipients = [attendee.user.user.email]
            email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

            send_mail(
                from_email=email_from,
                html_message=email_body_html,
                message=email_body_text,
                recipient_list=email_recipients,
                subject=email_subject,
            )

            attendee.last_reminded = timezone.now()
            attendee.save()

            time.sleep(0.1)
