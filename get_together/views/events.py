from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

from events.models.events import Event, CommonEvent, EventPhoto, Place, Attendee
from events.models.profiles import Team, Organization, UserProfile, Member
from events.forms import TeamEventForm, NewTeamEventForm, DeleteEventForm, EventCommentForm, NewPlaceForm, UploadEventPhotoForm, NewCommonEventForm
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
    event = Event.objects.get(id=event_id)
    comment_form = EventCommentForm()
    context = {
        'team': event.team,
        'event': event,
        'comment_form': comment_form,
        'is_attending': request.user.profile in event.attendees.all(),
        'attendee_list': Attendee.objects.filter(event=event),
        'can_edit_event': request.user.profile.can_edit_event(event),
    }
    return render(request, 'get_together/events/show_event.html', context)

@login_required
def create_event_team_select(request):
    teams = request.user.profile.moderating
    if len(teams) == 1:
        return redirect('create-event', team_id=teams[0].id)

    return render(request, 'get_together/events/create_event_team_select.html', {'teams': teams})

@login_required
def create_event(request, team_id):
    team = Team.objects.get(id=team_id)
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

def add_event_photo(request, event_id):
    event = Event.objects.get(id=event_id)
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

def add_place_to_event(request, event_id):
    event = Event.objects.get(id=event_id)
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
            new_place = form.save()
            event.place = new_place
            event.save()
            return redirect('share-event', event.id)
        else:
            context = {
                'event': event,
                'place_form': form,
            }
            return render(request, 'get_together/places/create_place.html', context)
    else:
     return redirect('home')

def share_event(request, event_id):
    event = Event.objects.get(id=event_id)
    context = {
        'event': event,
    }
    return render(request, 'get_together/events/share_event.html', context)

def edit_event(request, event_id):
    event = Event.objects.get(id=event_id)

    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = TeamEventForm(instance=event)

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

def delete_event(request, event_id):
    event = Event.objects.get(id=event_id)
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

def show_common_event(request, event_id, event_slug):
    event = CommonEvent.objects.get(id=event_id)
    context = {
        'org': event.organization,
        'common_event': event,
        'can_edit_event': False,
    }
    return render(request, 'get_together/orgs/show_common_event.html', context)

@login_required
def create_common_event(request, org_slug):
    org = Organization.objects.get(slug=org_slug)
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

def share_common_event(request, event_id):
    event = CommonEvent.objects.get(id=event_id)
    context = {
        'event': event,
    }
    return render(request, 'get_together/orgs/share_common_event.html', context)

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


