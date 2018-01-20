from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from .models.search import Searchable, SearchableSerializer
from .models.events import Event, Place, PlaceSerializer
from .models.locale import Country ,CountrySerializer, SPR, SPRSerializer, City, CitySerializer

import simplejson

# Create your views here.
def searchable_list(request, *args, **kwargs):
    searchables = Searchable.objects.all()
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

