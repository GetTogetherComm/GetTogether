from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from events.models.profiles import Team, UserProfile, Member
from events.forms import TeamEventForm, NewTeamEventForm, DeleteEventForm, NewPlaceForm, UploadEventPhotoForm

from events.models.events import Event, EventPhoto, Place, Attendee

import datetime
import simplejson

# Create your views here.
def events_list(request, *args, **kwargs):
    events = Event.objects.filter(attendees=request.user.profile, end_time__gt=datetime.datetime.now()).order_by('start_time')
    context = {
        'events_list': events,
    }
    return render(request, 'get_together/events/list_events.html', context)

def show_event(request, event_id, event_slug):
    event = Event.objects.get(id=event_id)
    context = {
        'team': event.team,
        'event': event,
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

    if request.method == 'GET':
        form = NewTeamEventForm()

        context = {
            'team': team,
            'event_form': form,
        }
        return render(request, 'get_together/events/create_event.html', context)
    elif request.method == 'POST':
        form = NewTeamEventForm(request.POST)
        if form.is_valid:
            form.instance.team = team
            form.instance.created_by = request.user.profile
            new_event = form.save()
            return redirect('add-place', new_event.id)
        else:
            context = {
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


