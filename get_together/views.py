from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from events.models.profiles import Team, UserProfile, Member
from events.forms import TeamForm, NewTeamForm, TeamEventForm, NewTeamEventForm, NewPlaceForm

from events.models.events import Event, Place, Attendee

import datetime
import simplejson

# Create your views here.

def home(request, *args, **kwards):
    if request.user.is_authenticated:
        user_teams = Team.objects.filter(owner_profile=request.user.profile)
        if len(user_teams) > 0:
            return redirect('events')
        else:
            return redirect('create-team')
    else:
        return render(request, 'get_together/index.html')

def events_list(request, *args, **kwargs):
    events = Event.objects.filter(end_time__gt=datetime.datetime.now()).order_by('start_time')
    context = {
        'events_list': events,
    }
    return render(request, 'get_together/events.html', context)

def create_team(request, *args, **kwargs):
    if request.method == 'GET':
        form = NewTeamForm()

        context = {
            'team_form': form,
        }
        return render(request, 'get_together/create_team.html', context)
    elif request.method == 'POST':
        form = NewTeamForm(request.POST)
        if form.is_valid:
            new_team = form.save()
            new_team.owner_profile = request.user.profile
            new_team.save()
            Member.objects.create(team=new_team, user=request.user.profile, role=Member.ADMIN)
            return redirect('show-team', team_id=new_team.pk)
        else:
            context = {
                'team_form': form,
            }
            return render(request, 'get_together/create_team.html', context)
    else:
     return redirect('home')

def edit_team(request, team_id):
    team = Team.objects.get(id=team_id)
    if not request.user.profile.can_edit_team(team):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this team.'))
        return redirect('show-team', team_id=team.pk)

    if request.method == 'GET':
        form = TeamForm(instance=team)

        context = {
            'team': team,
            'team_form': form,
        }
        return render(request, 'get_together/edit_team.html', context)
    elif request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid:
            new_team = form.save()
            new_team.owner_profile = request.user.profile
            new_team.save()
            return redirect('show-team', team_id=new_team.pk)
        else:
            context = {
                'team': team,
                'team_form': form,
            }
            return render(request, 'get_together/edit_team.html', context)
    else:
     return redirect('home')

def teams_list(request, *args, **kwargs):
    teams = Team.objects.all()
    context = {
        'all_teams': teams,
    }
    if request.user.is_authenticated:
        context['my_teams'] = request.user.profile.memberships.all()
    return render(request, 'get_together/teams.html', context)


def show_team(request, team_id, *args, **kwargs):
    team = Team.objects.get(id=team_id)
    team_events = Event.objects.filter(team=team, end_time__gt=datetime.datetime.now()).order_by('start_time')
    context = {
        'team': team,
        'events_list': team_events,
        'is_member': request.user.profile in team.members.all(),
        'member_list': Member.objects.filter(team=team),
        'can_create_event': request.user.profile.can_create_event(team),
        'can_edit_team': request.user.profile.can_edit_team(team),
    }
    return render(request, 'get_together/show_team.html', context)

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
        return render(request, 'get_together/edit_event.html', context)
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
            return render(request, 'get_together/edit_event.html', context)
    else:
     return redirect('home')

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
        return render(request, 'get_together/create_event.html', context)
    elif request.method == 'POST':
        form = NewTeamEventForm(request.POST)
        if form.is_valid:
            form.instance.team = team
            form.instance.created_by = request.user.profile
            new_event = form.save()
            return redirect(new_event.get_absolute_url())
        else:
            context = {
                'team': team,
                'event_form': form,
            }
            return render(request, 'get_together/create_event.html', context)
    else:
     return redirect('home')

def places_list(request, *args, **kwargs):
    places = Place.objects.all()
    context = {
        'places_list': places,
    }
    return render(request, 'get_together/places.html', context)

def create_place(request):
    if request.method == 'GET':
        form = NewPlaceForm()

        context = {
            'place_form': form,
        }
        return render(request, 'get_together/create_place.html', context)
    elif request.method == 'POST':
        form = NewPlaceForm(request.POST)
        if form.is_valid:
            new_place = form.save()
            return redirect('places')
        else:
            context = {
                'place_form': form,
            }
            return render(request, 'get_together/create_place.html', context)
    else:
     return redirect('home')

def show_event(request, event_id, event_slug):
    event = Event.objects.get(id=event_id)
    context = {
        'team': event.team,
        'event': event,
        'is_attending': request.user.profile in event.attendees.all(),
        'attendee_list': Attendee.objects.filter(event=event),
        'can_edit_event': request.user.profile.can_edit_event(event),
    }
    return render(request, 'get_together/show_event.html', context)
