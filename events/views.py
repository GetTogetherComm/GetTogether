from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from .models.search import Searchable, SearchableSerializer
from .models.events import Event, Place, PlaceSerializer, Attendee
from .models.locale import Country ,CountrySerializer, SPR, SPRSerializer, City, CitySerializer
from .models.profiles import Team, UserProfile, Member

import simplejson

# Create your views here.
def searchable_list(request, *args, **kwargs):
    searchables = Searchable.objects.exclude(location_name='')
    serializer = SearchableSerializer(searchables, many=True)
    return JsonResponse(serializer.data, safe=False)

def events_list(request, *args, **kwargs):
    events = Event.objects.all()
    context = {
        'events_list': events,
    }
    return render(request, 'events/event_list.html', context)

@api_view(['GET'])
def places_list(request, *args, **kwargs):
    places = Place.objects.all()
    if "q" in request.GET:
        match = request.GET.get("q", "")
        places = Place.objects.filter(name__icontains=match)
    else:
        places = Place.objects.all()
    serializer = PlaceSerializer(places, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def country_list(request, *args, **kwargs):
    if "q" in request.GET:
        match = request.GET.get("q", "")
        countries = Country.objects.filter(name__icontains=match)
    else:
        countries = Country.objects.all()
    serializer = CountrySerializer(countries, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def spr_list(request, *args, **kwargs):
    if "q" in request.GET:
        match = request.GET.get("q", "")
        sprs = SPR.objects.filter(name__icontains=match)
    else:
        sprs = SPR.objects.all()
    if "country" in request.GET and request.GET.get("country") is not "":
        sprs = sprs.filter(country=request.GET.get("country"))

    serializer = SPRSerializer(sprs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def city_list(request, *args, **kwargs):
    if "q" in request.GET:
        match = request.GET.get("q", "")
        cities = City.objects.filter(name__icontains=match)
    else:
        cities = City.objects.all()

    if "spr" in request.GET and request.GET.get("spr") is not "":
        cities = cities.filter(spr=request.GET.get("spr"))

    serializer = CitySerializer(cities, many=True)
    return Response(serializer.data)

def join_team(request, team_id):
    if request.user.is_anonymous:
        messages.add_message(request, messages.WARNING, message=_('You must be logged in to join a team.'))
        return redirect('show-team', team_id=team_id)
    team = Team.objects.get(id=team_id)
    if request.user.profile in team.members.all():
        messages.add_message(request, messages.INFO, message=_('You are already a member of this team.'))
        return redirect('show-team', team_id=team_id)
    new_member = Member.objects.create(team=team, user=request.user.profile, role=Member.NORMAL)
    messages.add_message(request, messages.SUCCESS, message=_('Welcome to the team!'))
    return redirect('show-team', team_id=team_id)

def leave_team(request, team_id):
    if request.user.is_anonymous:
        messages.add_message(request, messages.WARNING, message=_('You must be logged in to leave a team.'))
        return redirect('show-team', team_id=team_id)
    team = Team.objects.get(id=team_id)
    if request.user.profile not in team.members.all():
        messages.add_message(request, messages.INFO, message=_('You are not a member of this team.'))
        return redirect('show-team', team_id=team_id)
    Member.objects.filter(team=team, user=request.user.profile).delete()
    messages.add_message(request, messages.SUCCESS, message=_('You are no longer on this team.'))
    return redirect('show-team', team_id=team_id)

def attend_event(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.user.is_anonymous:
        messages.add_message(request, messages.WARNING, message=_("You must be logged in to say you're attending."))
        return redirect(event.get_absolute_url())
    if request.user.profile in event.attendees.all():
        messages.add_message(request, messages.INFO, message=_('You are already attending this event.'))
        return redirect(event.get_absolute_url())
    new_attendee = Attendee.objects.create(event=event, user=request.user.profile, role=Attendee.NORMAL, status=Attendee.YES)
    messages.add_message(request, messages.SUCCESS, message=_("We'll see you there!"))
    return redirect(event.get_absolute_url())

