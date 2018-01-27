from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from events.models.profiles import Team, UserProfile, Member
from events.forms import TeamForm, NewTeamForm, TeamEventForm, NewTeamEventForm, NewPlaceForm

from events.models.events import Event, Place, Attendee

import datetime
import simplejson

# Create your views here.
def teams_list(request, *args, **kwargs):
    teams = Team.objects.all()
    context = {
        'all_teams': teams,
    }
    if request.user.is_authenticated:
        context['my_teams'] = request.user.profile.memberships.all()
    return render(request, 'get_together/teams/list_teams.html', context)

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
    return render(request, 'get_together/teams/show_team.html', context)

def create_team(request, *args, **kwargs):
    if request.method == 'GET':
        form = NewTeamForm()

        context = {
            'team_form': form,
        }
        return render(request, 'get_together/teams/create_team.html', context)
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
            return render(request, 'get_together/teams/create_team.html', context)
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
        return render(request, 'get_together/teams/edit_team.html', context)
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
            return render(request, 'get_together/teams/edit_team.html', context)
    else:
     return redirect('home')

