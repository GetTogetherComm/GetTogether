from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse

from events.models.profiles import Organization, Team, UserProfile, Member
from events.models.events import Event, CommonEvent, Place, Attendee
from events.forms import TeamForm, NewTeamForm, TeamDefinitionForm
from events import location

import simple_ga as ga

import datetime
import simplejson

@login_required
def start_new_team(request):
    new_team = Team(owner_profile=request.user.profile)
    new_team.owner_profile = request.user.profile
    if request.method == 'GET':
        if 'organization' in request.GET and request.GET['organization'] != '':
            org = Organization.objects.get(id=request.GET['organization'])
            if request.user.profile.can_edit_org(org):
                new_team.organization = org
        form = NewTeamForm(instance=new_team)
        g = location.get_geoip(request)
        if g.latlng is not None and g.latlng[0] is not None and g.latlng[1] is not None:
            city = location.get_nearest_city(g.latlng)
            if city:
                form.initial={'city': city, 'tz': city.tz}

        context = {
            'team': new_team,
            'team_form': form,
        }
        if 'event' in request.GET and request.GET['event'] != '':
            context['event'] = request.GET['event']
        return render(request, 'get_together/new_team/start_new_team.html', context)
    elif request.method == 'POST':
        if 'organization' in request.POST and request.POST['organization'] != '':
            org = Organization.objects.get(id=request.POST['organization'])
            if request.user.profile.can_edit_org(org):
                new_team.organization = org
        form = NewTeamForm(request.POST, request.FILES, instance=new_team)
        if form.is_valid():
            new_team = form.save()
            new_team.save()
            if 'event' in request.POST and request.POST['event'] != '':
                try:
                    event = Event.objects.get(id=request.POST['event'])
                    event.team = new_team
                    event.save()
                except:
                    pass

            Member.objects.create(team=new_team, user=request.user.profile, role=Member.ADMIN)
            ga.add_event(request, action='new_team', category='growth', label=new_team.name)
            return redirect('define-team', team_id=new_team.pk)
        else:
            context = {
                'team': new_team,
                'team_form': form,
            }
            if 'event' in request.POST and request.POST['event'] != '':
                context['event'] = request.POST['event']
            return render(request, 'get_together/new_team/start_new_team.html', context)
    else:
        return redirect('home')

def define_new_team(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.method == 'GET':
        form = TeamDefinitionForm(instance=team)

        context = {
            'team': team,
            'team_form': form,
        }
        return render(request, 'get_together/new_team/define_team.html', context)
    elif request.method == 'POST':
        form = TeamDefinitionForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            if team.organization:
                messages.add_message(request, messages.SUCCESS, message=_('Your new member team is ready to go!'))
                return redirect('show-org', org_slug=team.organization.slug)
            else:
                messages.add_message(request, messages.SUCCESS, message=_('Your new team is ready to go! Now it\'s time to plan your first event.'))
                return redirect('create-event', team_id=team.id)
        else:
            context = {
                'team': team,
                'team_form': form,
            }
            return render(request, 'get_together/new_team/define_team.html', context)
    else:
     return redirect('home')

