import datetime

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _

import simplejson
from events.forms import NewPlaceForm
from events.models.events import Attendee, Event, Place
from events.models.profiles import Member, Team, UserProfile


# Create your views here.
def places_list(request, *args, **kwargs):
    places = Place.objects.all()
    context = {"places_list": places}
    return render(request, "get_together/places/list_places.html", context)


def show_place(request, place_id):
    place = get_object_or_404(Place, id=place_id)
    context = {
        "place": place,
        "event_list": Event.objects.filter(
            place=place, team__access=Team.PUBLIC
        ).order_by("-start_time"),
    }
    return render(request, "get_together/places/show_place.html", context)


def create_place(request):
    if request.method == "GET":
        form = NewPlaceForm()

        context = {"place_form": form}
        return render(request, "get_together/places/create_place.html", context)
    elif request.method == "POST":
        form = NewPlaceForm(request.POST)
        if form.is_valid():
            new_place = form.save()
            return redirect("places")
        else:
            context = {"place_form": form}
            return render(request, "get_together/places/create_place.html", context)
    else:
        return redirect("home")
