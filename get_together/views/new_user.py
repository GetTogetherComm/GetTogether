from django.utils.translation import ugettext_lazy as _

from django.contrib.sites.models import Site
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings

from events.models.profiles import Team, UserProfile, Member
from events.models.events import Event, Place, Attendee
from events.forms import SendNotificationsForm

import datetime
import simplejson

def new_user_confirm_profile(request):
    pass

def new_user_find_teams(request):
    pass

def new_user_find_events(request):
    pass

# These views are for confirming a user's email address before sending them mail
@login_required
def user_send_confirmation_email(request):
    confirmation_request = request.user.account.new_confirmation_request()
    site = Site.objects.get(id=1)
    confirmation_url = "https://%s%s" % (site.domain, reverse('confirm-email', kwargs={'confirmation_key':confirmation_request.key}))

    context = {
        'confirmation': confirmation_request,
        'confirmation_url': confirmation_url,
    }
    email_subject = '[GetTogether] Confirm email address'
    email_body_text = render_to_string('get_together/emails/confirm_email.txt', context, request)
    email_body_html = render_to_string('get_together/emails/confirm_email.html', context, request)
    email_recipients = [request.user.email]
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')
    send_mail(
        subject=email_subject,
        message=email_body_text,
        from_email=email_from,
        recipient_list=email_recipients,
        html_message=email_body_html
    )
    return render(request, 'get_together/users/sent_email_confirmation.html', context)

@login_required
def user_confirm_email(request, confirmation_key):
    if request.user.account.confirm_email(confirmation_key):
        messages.add_message(request, messages.SUCCESS, message=_('Your email address has been confirmed.'))
        return redirect('confirm-notifications')
    else:
        return render(request, 'get_together/users/bad_email_confirmation.html')

@login_required
def user_confirm_notifications(request):
    if request.method == 'GET':
        form = SendNotificationsForm(instance=request.user.profile)
        context = {
            'notifications_form': form
        }
        return render(request, 'get_together/users/confirm_notifications.html', context)
    elif request.method == 'POST':
        form = SendNotificationsForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('home')

