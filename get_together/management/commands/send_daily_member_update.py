from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils import timezone

from events.models import Event, Member
from accounts.models import EmailRecord

import datetime


class Command(BaseCommand):
    help = "Sends email to team admins about new members"

    def handle(self, *args, **options):
        # members who recently joined
        members = Member.objects.filter(role=Member.NORMAL, joined_date__gte=timezone.now() - datetime.timedelta(days=1)).order_by('team')

        current_team = None
        new_members = []
        for member in members:

            if member.team != current_team:
                send_new_members(current_team, new_members)
                current_team = member.team
                new_members = []

            new_members.append(member)
        if current_team is not None:
            send_new_members(current_team, new_members)


def send_new_members(team, new_members):
    if len(new_members) < 1:
        return
    admins = [member.user.user for member in Member.objects.filter(team=team, role=Member.ADMIN) if member.user.user.account.is_email_confirmed]
    if len(admins) < 1:
        return
    context = {
        'team': team,
        'members': new_members,
        'site': Site.objects.get(id=1)
    }

    email_subject = 'New team members'
    email_body_text = render_to_string('get_together/emails/teams/new_team_members.txt', context)
    email_body_html = render_to_string('get_together/emails/teams/new_team_members.html', context)
    email_recipients = [admin.email for admin in admins]
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

    success = send_mail(
        from_email=email_from,
        html_message=email_body_html,
        message=email_body_text,
        recipient_list=email_recipients,
        subject=email_subject,
    )

    for admin in admins:
        EmailRecord.objects.create(
            sender=None,
            recipient=admin,
            email=admin.email,
            subject=email_subject,
            body=email_body_text,
            ok=success
        )