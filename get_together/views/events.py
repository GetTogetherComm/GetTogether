from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.sites.models import Site
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings

from events.models.events import (
    Event,
    CommonEvent,
    EventSeries,
    EventPhoto,
    Place,
    Attendee,
    update_event_searchable,
    delete_event_searchable,
)
from events.models.speakers import Speaker, Talk, SpeakerRequest, Presentation
from events.models.profiles import Team, Organization, UserProfile, Member
from events.forms import (
    TeamEventForm,
    NewTeamEventForm,
    DeleteEventForm,
    EventSeriesForm,
    DeleteEventSeriesForm,
    EventCommentForm,
    NewPlaceForm,
    UploadEventPhotoForm,
    NewCommonEventForm,
    EventInviteEmailForm,
    EventInviteMemberForm,
)
from events import location

import datetime
import simplejson

# Create your views here.
def events_list(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect('all-events')
    events = Event.objects.filter(attendees=request.user.profile, end_time__gt=timezone.now()).order_by('start_time')
    geo_ip = location.get_geoip(request)
    context = {
        'active': 'my',
        'events_list': sorted(events, key=lambda event: location.event_distance_from(geo_ip.latlng, event)),
    }
    return render(request, 'get_together/events/list_events.html', context)

def events_list_all(request, *args, **kwargs):
    events = Event.objects.filter(end_time__gt=timezone.now()).order_by('start_time')
    geo_ip = location.get_geoip(request)
    context = {
        'active': 'all',
        'events_list': sorted(events, key=lambda event: location.event_distance_from(geo_ip.latlng, event)),
    }
    return render(request, 'get_together/events/list_events.html', context)

def show_event(request, event_id, event_slug):
    event = get_object_or_404(Event, id=event_id)
    comment_form = EventCommentForm()
    context = {
        'team': event.team,
        'event': event,
        'comment_form': comment_form,
        'is_attending': request.user.profile in event.attendees.all(),
        'attendee_list': Attendee.objects.filter(event=event).order_by('-status'),
        'attendee_count': Attendee.objects.filter(event=event, status=Attendee.YES).count(),
        'presentation_list': event.presentations.filter(status=Presentation.ACCEPTED).order_by('start_time'),
        'pending_presentations': event.presentations.filter(status=Presentation.PROPOSED).count(),
        'can_edit_event': request.user.profile.can_edit_event(event),
        'can_edit_team': request.user.profile.can_edit_team(event.team),
        'is_email_confirmed': request.user.account.is_email_confirmed,
    }
    return render(request, 'get_together/events/show_event.html', context)

def show_series(request, series_id, series_slug):
    series = get_object_or_404(EventSeries, id=series_id)
    context = {
        'team': series.team,
        'series': series,
        'instances': series.instances.all().order_by('-start_time'),
        'can_edit_event': request.user.profile.can_create_event(series.team),
    }
    return render(request, 'get_together/events/show_series.html', context)

@login_required
def create_event_team_select(request):
    teams = request.user.profile.moderating
    if len(teams) == 1:
        return redirect('create-event', team_id=teams[0].id)

    return render(request, 'get_together/events/create_event_team_select.html', {'teams': teams})

@login_required
def create_event(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if not request.user.profile.can_create_event(team):
        messages.add_message(request, messages.WARNING, message=_('You can not create events for this team.'))
        return redirect('show-team', team_id=team.pk)

    new_event = Event(team=team, created_by=request.user.profile)


    if request.method == 'GET':
        if 'common' in request.GET and request.GET['common'] != '':
            new_event.parent = CommonEvent.objects.get(id=request.GET['common'])
        form = NewTeamEventForm(instance=new_event)

        context = {
            'event': new_event,
            'team': team,
            'event_form': form,
        }
        return render(request, 'get_together/events/create_event.html', context)
    elif request.method == 'POST':
        if 'common' in request.POST and request.POST['common'] != '':
            new_event.parent = CommonEvent.objects.get(id=request.POST['common'])
        form = NewTeamEventForm(request.POST, instance=new_event)
        if form.is_valid:
            new_event = form.save()
            Attendee.objects.create(event=new_event, user=request.user.profile, role=Attendee.HOST, status=Attendee.YES)

            if form.cleaned_data.get('recurrences', None):
                new_series = EventSeries.from_event(new_event, recurrences=form.cleaned_data['recurrences'])
                new_series.save()
                new_event.series = new_series
                new_event.save()

            messages.add_message(request, messages.SUCCESS, message=_('Your event has been scheduled! Next, find a place for your event.'))
            return redirect('add-place', new_event.id)
        else:
            context = {
                'event': new_event,
                'team': team,
                'event_form': form,
            }
            return render(request, 'get_together/events/create_event.html', context)
    else:
     return redirect('home')


@login_required
def invite_attendees(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    attendee_userids = [attendee.user.id for attendee in Attendee.objects.filter(event=event)]
    members = Member.objects.filter(team=event.team, ).order_by('user__realname')
    member_choices = [(member.id, member.user) for member in members if member.user.user.account.is_email_confirmed and member.user.id not in attendee_userids]
    default_choices = [('all', 'All Members (%s)' % len(member_choices))]

    if request.method == 'POST' and request.POST.get('form', None) == 'email':
        email_form = EventInviteEmailForm(request.POST)
        if email_form.is_valid():
            to = email_form.cleaned_data['emails']
            for email in to:
                invite_attendee(email, event, request.user.profile)
            messages.add_message(request, messages.SUCCESS, message=_('Sent %s invites' % len(to)))
            return redirect(event.get_absolute_url())
        team_form = EventInviteMemberForm()
        team_form.fields['member'].choices = default_choices + member_choices
    elif request.method == 'POST' and request.POST.get('form', None) == 'team':
        team_form = EventInviteMemberForm(request.POST)
        team_form.fields['member'].choices = default_choices + member_choices
        if team_form.is_valid():
            to = team_form.cleaned_data['member']
            if to == 'all':
                for (member_id, user) in member_choices:
                    try:
                        attendee = Attendee.objects.get(event=event, user=user)
                    except:
                        # No attendee record found, so send the invite
                        invite_attendee(user.user.email, event, request.user.profile)
                messages.add_message(request, messages.SUCCESS, message=_('Sent %s invites' % len(member_choices)))
                return redirect(event.get_absolute_url())
            else:
                member = get_object_or_404(Member, id=to)
                try:
                    attendee = Attendee.objects.get(event=event, user=member.user)
                except:
                    # No attendee record found, so send the invite
                    invite_attendee(member.user.user.email, event, request.user.profile)
                    messages.add_message(request, messages.SUCCESS, message=_('Invited %s' % member.user))
                return redirect(event.get_absolute_url())
        email_form = EventInviteEmailForm()
    else:
        email_form = EventInviteEmailForm()
        team_form = EventInviteMemberForm()
        team_form.fields['member'].choices = default_choices + member_choices

    context = {
        'event': event,
        'email_form': email_form,
        'team_form': team_form,
        'member_choice_count': len(member_choices),
        'can_edit_team': request.user.profile.can_edit_team(event.team),
        'is_email_confirmed': request.user.account.is_email_confirmed,
    }
    return render(request, 'get_together/events/invite_attendees.html', context)


def invite_attendee(email, event, sender):
    context = {
        'sender': sender,
        'team': event.team,
        'event': event,
        'site': Site.objects.get(id=1),
    }
    email_subject = '[GetTogether] Invite to attend %s' % event.name
    email_body_text = render_to_string('get_together/emails/attendee_invite.txt', context)
    email_body_html = render_to_string('get_together/emails/attendee_invite.html', context)
    email_recipients = [email]
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

    send_mail(
        from_email=email_from,
        html_message=email_body_html,
        message=email_body_text,
        recipient_list=email_recipients,
        subject=email_subject,
        fail_silently=True,
    )


@login_required
def add_event_photo(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = UploadEventPhotoForm()

        context = {
            'event': event,
            'photo_form': form,
        }
        return render(request, 'get_together/events/add_photo.html', context)
    elif request.method == 'POST':
        new_photo = EventPhoto(event=event)
        form = UploadEventPhotoForm(request.POST, request.FILES, instance=new_photo)
        if form.is_valid():
            form.save()
            return redirect(event.get_absolute_url())
        else:
            context = {
                'event': event,
                'photo_form': form,
            }
            return render(request, 'get_together/events/add_photo.html', context)
    else:
     return redirect('home')

@login_required
def add_place_to_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = NewPlaceForm()

        context = {
            'event': event,
            'place_form': form,
        }
        return render(request, 'get_together/places/create_place.html', context)
    elif request.method == 'POST':
        form = NewPlaceForm(request.POST)
        if form.is_valid:
            if request.POST.get('id', None):
                form.instance.id = request.POST.get('id')
            new_place = form.save()
            event.place = new_place
            event.save()
            if event.series is not None and event.series.place is None:
                event.series.place = new_place;
                event.series.save()
            return redirect(event.get_absolute_url())
        else:
            context = {
                'event': event,
                'place_form': form,
            }
            return render(request, 'get_together/places/create_place.html', context)
    else:
     return redirect('home')

@login_required
def add_place_to_series(request, series_id):
    series = get_object_or_404(EventSeries, id=series_id)
    if not request.user.profile.can_edit_series(series):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(series.get_absolute_url())

    if request.method == 'GET':
        form = NewPlaceForm()

        context = {
            'series': series,
            'place_form': form,
        }
        return render(request, 'get_together/places/add_place_to_series.html', context)
    elif request.method == 'POST':
        form = NewPlaceForm(request.POST)
        if form.is_valid:
            if request.POST.get('id', None):
                form.instance.id = request.POST.get('id')
            new_place = form.save()
            series.place = new_place
            series.save()
            return redirect('show-series', series.id, series.slug)
        else:
            context = {
                'series': series,
                'place_form': form,
            }
            return render(request, 'get_together/places/add_place_to_series.html', context)
    else:
     return redirect('home')

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = TeamEventForm(instance=event)
        if event.series is not None:
            form.initial['recurrences'] = event.series.recurrences

        context = {
            'team': event.team,
            'event': event,
            'event_form': form,
        }
        return render(request, 'get_together/events/edit_event.html', context)
    elif request.method == 'POST':
        form = TeamEventForm(request.POST,instance=event)
        if form.is_valid:
            new_event = form.save()

            if form.cleaned_data.get('recurrences', None):
                if event.series is not None:
                    event.series.recurrences = form.cleaned_data['recurrences']
                    event.series.save()
                else:
                    new_series = EventSeries.from_event(new_event, recurrences=form.cleaned_data['recurrences'])
                    new_series.save()
                    new_event.series = new_series
                    new_event.save()

            return redirect(new_event.get_absolute_url())
        else:
            context = {
                'team': event.team,
                'event': event,
                'event_form': form,
            }
            return render(request, 'get_together/events/edit_event.html', context)
    else:
     return redirect('home')

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = DeleteEventForm()

        context = {
            'team': event.team,
            'event': event,
            'delete_form': form,
        }
        return render(request, 'get_together/events/delete_event.html', context)
    elif request.method == 'POST':
        form = DeleteEventForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            team_id = event.team_id
            delete_event_searchable(event);
            event.delete()
            return redirect('show-team', team_id)
        else:
            context = {
                'team': event.team,
                'event': event,
                'delete_form': form,
            }
            return render(request, 'get_together/events/delete_event.html', context)
    else:
     return redirect('home')

@login_required
def edit_series(request, series_id):
    series = get_object_or_404(EventSeries, id=series_id)

    if not request.user.profile.can_edit_series(series):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(series.get_absolute_url())

    if request.method == 'GET':
        form = EventSeriesForm(instance=series)

        context = {
            'team': series.team,
            'series': series,
            'series_form': form,
        }
        return render(request, 'get_together/events/edit_series.html', context)
    elif request.method == 'POST':
        form = EventSeriesForm(request.POST,instance=series)
        if form.is_valid:
            new_series = form.save()
            return redirect(new_series.get_absolute_url())
        else:
            context = {
                'team': event.team,
                'series': series,
                'series_form': form,
            }
            return render(request, 'get_together/events/edit_series.html', context)
    else:
     return redirect('home')

@login_required
def delete_series(request, series_id):
    series = get_object_or_404(EventSeries, id=series_id)
    if not request.user.profile.can_edit_series(series):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(series.get_absolute_url())

    if request.method == 'GET':
        form = DeleteEventSeriesForm()

        context = {
            'team': series.team,
            'series': series,
            'delete_form': form,
        }
        return render(request, 'get_together/events/delete_series.html', context)
    elif request.method == 'POST':
        form = DeleteEventSeriesForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            team_id = series.team_id
            series.delete()
            return redirect('show-team', team_id)
        else:
            context = {
                'team': series.team,
                'series': series,
                'delete_form': form,
            }
            return render(request, 'get_together/events/delete_series.html', context)
    else:
     return redirect('home')

def show_common_event(request, event_id, event_slug):
    event = get_object_or_404(CommonEvent, id=event_id)
    context = {
        'org': event.organization,
        'common_event': event,
        'can_edit_event': False,
    }
    return render(request, 'get_together/orgs/show_common_event.html', context)

@login_required
def create_common_event(request, org_slug):
    org = get_object_or_404(Organization, slug=org_slug)
    if not request.user.profile.can_create_common_event(org):
        messages.add_message(request, messages.WARNING, message=_('You can not create events for this org.'))
        return redirect('show-org', org_id=org.pk)

    new_event = CommonEvent(organization=org, created_by=request.user.profile)
    if request.method == 'GET':
        form = NewCommonEventForm(instance=new_event)

        context = {
            'org': org,
            'event_form': form,
        }
        return render(request, 'get_together/orgs/create_common_event.html', context)
    elif request.method == 'POST':
        form = NewCommonEventForm(request.POST, instance=new_event)
        if form.is_valid:
            new_event = form.save()
            return redirect('show-common-event', new_event.id, new_event.slug)
        else:
            context = {
                'org': org,
                'event_form': form,
            }
            return render(request, 'get_together/orgs/create_common_event.html', context)
    else:
     return redirect('home')

@login_required
def create_common_event_team_select(request, event_id):
    teams = request.user.profile.moderating
    if len(teams) == 1:
        return redirect(reverse('create-event', kwargs={'team_id':teams[0].id}) + '?common=%s'%event_id)
    context = {
        'common_event_id': event_id,
        'teams': teams
    }
    return render(request, 'get_together/orgs/create_common_event_team_select.html', context)


