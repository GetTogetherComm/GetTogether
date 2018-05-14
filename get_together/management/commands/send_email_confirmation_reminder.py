from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings
from django.contrib.sites.models import Site

from accounts.models import Account, EmailConfirmation, EmailRecord

import time
import urllib
import datetime

class Command(BaseCommand):
    help = "Sends confirmation emails to accounts that haven't been confirmed yet"

    def add_arguments(self, parser):
        parser.add_argument('-d','--days-since-last', dest='days', type=int, default=None)

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)
        accounts = Account.objects.filter(is_email_confirmed=False)
        for account in accounts:
            if not account.user.email:
                break # Skip accounts without an email
            confirmation_request = EmailConfirmation.objects.filter(user=account.user)

            if 'days' in options and options.get('days', None):
                discard_before = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=options.get('days'))
                for request in confirmation_request.filter(expires__lte=discard_before):
                    request.delete()

            if confirmation_request.count() > 0:
                print("Confirmation request pending for %s <%s>" % (account.user.username, account.user.email))
                break

            print("Sending confirmation email to %s <%s>" % (account.user.username, account.user.email))
            confirmation_request = account.new_confirmation_request()
            confirmation_url = "https://%s%s" % (site.domain, reverse('confirm-email', kwargs={'confirmation_key':confirmation_request.key}))

            context = {
                'confirmation': confirmation_request,
                'confirmation_url': confirmation_url,
            }
            email_subject = '[GetTogether] Email confirmation reminder'
            email_body_text = render_to_string('get_together/emails/confirm_email.txt', context)
            email_body_html = render_to_string('get_together/emails/confirm_email.html', context)
            email_recipients = [account.user.email]
            email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')
            success = send_mail(
                subject=email_subject,
                message=email_body_text,
                from_email=email_from,
                recipient_list=email_recipients,
                html_message=email_body_html
            )

            EmailRecord.objects.create(
                sender=None,
                recipient=account.user,
                email=account.user.email,
                subject=email_subject,
                body=email_body_text,
                ok=success
            )
            time.sleep(0.1)



