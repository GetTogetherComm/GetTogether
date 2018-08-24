from django.utils.translation import ugettext_lazy as _

from django.contrib.sites.models import Site
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings

from events.models.profiles import Team, UserProfile, Member, Category
from events.models.events import Event, Place, Attendee
from events.forms import SendNotificationsForm, UserForm, ConfirmProfileForm

from accounts.models import EmailRecord

from .utils import get_nearby_teams

import simple_ga as ga

import datetime
import simplejson

@login_required
def setup_1_confirm_profile(request):
    user = request.user
    profile = request.user.profile

    if request.method == 'GET':
        user_form = UserForm(instance=user)
        profile_form = ConfirmProfileForm(instance=profile)
        context = {
            'user': user,
            'profile': profile,
            'user_form': user_form,
            'profile_form': profile_form,
        }
        return render(request, 'get_together/new_user/setup_1_confirm_profile.html', context)
    elif request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ConfirmProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            saved_user = user_form.save()
            profile_form.save()
            if saved_user.email is not None and saved_user.email != '' and not saved_user.account.is_email_confirmed:
                # Call the view to trigger sending a confirmation email, but ignore it's response
                user_send_confirmation_email(request)
            return redirect('setup-2-pick-categories')
        else:
            context = {
                'user': user,
                'profile': profile,
                'user_form': user_form,
                'profile_form': profile_form,
            }
            return render(request, 'get_together/new_user/setup_1_confirm_profile.html', context)
    else:
        return redirect('home')


@login_required
def setup_2_pick_categories(request):
    user = request.user
    profile = request.user.profile

    if request.method == 'GET':
        categories = Category.objects.all()
        context = {
            'user': user,
            'profile': profile,
            'categories': categories,
        }
        return render(request, 'get_together/new_user/setup_2_pick_categories.html', context)
    elif request.method == 'POST':
        for entry in request.POST:
            if entry.startswith('category_'):
                category_id = entry.split('_')[1]
                try:
                    profile.categories.add(category_id)
                except:
                    pass
        return redirect('setup-3-find-teams')
    else:
        return redirect('home')

@login_required
def setup_3_find_teams(request):
    user = request.user
    profile = request.user.profile
    if request.method == 'GET':
        teams = get_nearby_teams(request)
        if (teams.count() < 1):
            return redirect('setup-complete')
        context = {
            'user': user,
            'profile': profile,
            'teams': teams,
        }
        return render(request, 'get_together/new_user/setup_3_find_teams.html', context)
    elif request.method == 'POST':
        for entry in request.POST:
            if entry.startswith('team_'):
                team_id = entry.split('_')[1]
                try:
                    Member.objects.get_or_create(team_id=team_id, user=profile, defaults={'role': Member.NORMAL})
                except Member.MultipleObjectsReturned:
                    pass
        return redirect('setup-4-attend-events')
    else:
        return redirect('home')

@login_required
def setup_4_attend_events(request):
    user = request.user
    profile = request.user.profile
    if request.method == 'GET':
        events = Event.objects.filter(team__in=profile.memberships.all(), end_time__gte=datetime.datetime.now())
        if (events.count() < 1):
            return redirect('setup-complete')
        context = {
            'user': user,
            'profile': profile,
            'events': events,
        }
        return render(request, 'get_together/new_user/setup_4_attend_events.html', context)
    elif request.method == 'POST':
        for entry in request.POST:
            if entry.startswith('event_'):
                event_id = entry.split('_')[1]
                try:
                    Attendee.objects.get_or_create(event_id=event_id, user=profile, defaults={'role': Attendee.NORMAL, 'status': Attendee.YES})
                except Attendee.MultipleObjectsReturned:
                    pass
        return redirect('setup-complete')
    else:
        return redirect('home')

@login_required
def setup_complete(request):
    messages.add_message(request, messages.SUCCESS, message=_('Your setup is complete, welcome to GetTogether!'))
    request.user.account.setup_complete()
    return redirect('home')

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
    email_subject = 'Confirm your email address'
    email_body_text = render_to_string('get_together/emails/users/confirm_email.txt', context, request)
    email_body_html = render_to_string('get_together/emails/users/confirm_email.html', context, request)
    email_recipients = [request.user.email]
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')
    success = send_mail(
        subject=email_subject,
        message=email_body_text,
        from_email=email_from,
        recipient_list=email_recipients,
        html_message=email_body_html
    )
    EmailRecord.objects.create(
        sender=request.user,
        recipient=request.user,
        email=request.user.email,
        subject=email_subject,
        body=email_body_text,
        ok=success
    )
    return render(request, 'get_together/new_user/sent_email_confirmation.html', context)

@login_required
def user_confirm_email(request, confirmation_key):
    if request.user.account.confirm_email(confirmation_key):
        messages.add_message(request, messages.SUCCESS, message=_('Your email address has been confirmed.'))
        ga.add_event(request, action='email_confirmed', category='activity', label=str(request.user.profile))

        return redirect('confirm-notifications')
    else:
        return render(request, 'get_together/new_user/bad_email_confirmation.html')

@login_required
def user_confirm_notifications(request):
    if request.method == 'GET':
        form = SendNotificationsForm(instance=request.user.profile)
        context = {
            'notifications_form': form
        }
        return render(request, 'get_together/new_user/confirm_notifications.html', context)
    elif request.method == 'POST':
        form = SendNotificationsForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('home')

