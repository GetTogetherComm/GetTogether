from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from events.models.profiles import Team
from events.forms import TeamForm, NewTeamForm

from events.models.events import Event

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
    events = Event.objects.all()
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
            return redirect('show-team', team_id=new_team.pk)
        else:
            context = {
                'team_form': form,
            }
            return render(request, 'get_together/create_team.html', context)
    else:
     return redirect('home')

def show_team(request, team_id, *args, **kwargs):
    team = Team.objects.get(id=team_id)
    team_events = Event.objects.filter(team=team)
    context = {
        'team': team,
        'events_list': team_events,
    }
    return render(request, 'get_together/show_team.html', context)

def show_event(request, event_id, event_slug):
    event = Event.objects.get(id=event_id)
    context = {
        'team': event.team,
        'event': event,
    }
    return render(request, 'get_together/show_event.html', context)
