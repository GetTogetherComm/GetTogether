import datetime
import math
import traceback

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _

import geocoder
import simple_ga as ga
import simplejson
from accounts.decorators import setup_wanted
from events import location
from events.forms import SearchForm, SearchTeamsByName
from events.models.events import Attendee, Event, Place
from events.models.locale import City
from events.models.profiles import Member, Team, UserProfile
from events.models.search import Searchable

from .events import *
from .new_event import *
from .new_team import *
from .new_user import *
from .orgs import *
from .places import *
from .speakers import *
from .teams import *
from .user import *
from .utils import *

KM_PER_DEGREE_LAT = 110.574
KM_PER_DEGREE_LNG = 111.320  # At the equator
DEFAULT_NEAR_DISTANCE = 100  # kilometeres
# Create your views here.


def home(request, *args, **kwards):
    context = {}

    near_distance = int(request.GET.get("distance", DEFAULT_NEAR_DISTANCE))
    context["distance"] = near_distance
    context["name"] = request.GET.get("name", "")
    context["geoip_lookup"] = False
    context["city_search"] = False

    city = None
    ll = None
    if "city" in request.GET and request.GET.get("city"):
        try:
            city_id = int(request.GET.get("city"))
            city = City.objects.get(id=city_id)
            context["city"] = city
            ll = [city.latitude, city.longitude]
            ga.add_event(
                request, "homepage_search", category="search", label=city.short_name
            )
            context["city_search"] = True
        except:
            messages.add_message(
                request,
                messages.ERROR,
                message=_("Could not locate the City you requested."),
            )
            context["city_search"] = False

    if context["city_search"] == False:
        try:
            g = location.get_geoip(request)
            if (
                g.latlng is not None
                and len(g.latlng) >= 2
                and g.latlng[0] is not None
                and g.latlng[1] is not None
            ):
                ll = g.latlng
                context["geoip_lookup"] = True

                try:
                    city_distance = 1  # km
                    while city is None and city_distance < 100:
                        minlat = ll[0] - (city_distance / KM_PER_DEGREE_LAT)
                        maxlat = ll[0] + (city_distance / KM_PER_DEGREE_LAT)
                        minlng = ll[1] - (
                            city_distance
                            / (KM_PER_DEGREE_LNG * math.cos(math.radians(ll[0])))
                        )
                        maxlng = ll[1] + (
                            city_distance
                            / (KM_PER_DEGREE_LNG * math.cos(math.radians(ll[0])))
                        )
                        nearby_cities = City.objects.filter(
                            latitude__gte=minlat,
                            latitude__lte=maxlat,
                            longitude__gte=minlng,
                            longitude__lte=maxlng,
                        )
                        if len(nearby_cities) == 0:
                            city_distance += 1
                        else:
                            city = sorted(
                                nearby_cities,
                                key=lambda city: location.city_distance_from(ll, city),
                            )[0]

                    if (
                        request.user.is_authenticated
                        and request.user.profile.city is None
                    ):
                        profile = request.user.profile
                        profile.city = city
                        profile.save()
                except Exception as err:
                    print("City lookup failed", err)
                    raise Exception("City lookup filed")
            else:
                raise Exception("Geocoder result has no latlng")
        except Exception as err:
            context["geoip_lookup"] = False
            print(
                "Geocoder lookup failed for %s" % request.META.get("REMOTE_ADDR"), err
            )

    if ll is not None:
        context["latitude"] = ll[0]
        context["longitude"] = ll[1]
        try:
            minlat = ll[0] - (near_distance / KM_PER_DEGREE_LAT)
            maxlat = ll[0] + (near_distance / KM_PER_DEGREE_LAT)
            minlng = ll[1] - (
                near_distance / (KM_PER_DEGREE_LNG * math.cos(math.radians(ll[0])))
            )
            maxlng = ll[1] + (
                near_distance / (KM_PER_DEGREE_LNG * math.cos(math.radians(ll[0])))
            )
            context["minlat"] = minlat
            context["maxlat"] = maxlat
            context["minlng"] = minlng
            context["maxlng"] = maxlng

            near_events = Searchable.objects.filter(
                latitude__gte=minlat,
                latitude__lte=maxlat,
                longitude__gte=minlng,
                longitude__lte=maxlng,
                end_time__gte=datetime.datetime.now(),
            )
            if context["name"]:
                near_events = near_events.filter(
                    Q(event_title__icontains=context["name"])
                    | Q(group_name__icontains=context["name"])
                )
            context["near_events"] = sorted(
                near_events,
                key=lambda searchable: location.searchable_distance_from(
                    ll, searchable
                ),
            )

            #            # If there aren't any teams in the user's geoip area, show them the closest ones
            if context["geoip_lookup"] and len(near_events) < 1:
                context["closest_events"] = sorted(
                    Searchable.objects.filter(end_time__gte=datetime.datetime.now()),
                    key=lambda searchable: location.searchable_distance_from(
                        ll, searchable
                    ),
                )[:3]

            near_teams = Team.public_objects.filter(
                city__latitude__gte=minlat,
                city__latitude__lte=maxlat,
                city__longitude__gte=minlng,
                city__longitude__lte=maxlng,
            ).filter(
                Q(access=Team.PUBLIC)
                | Q(access=Team.PRIVATE, owner_profile=request.user.profile)
            )
            if context["name"]:
                near_teams = near_teams.filter(name__icontains=context["name"])
            context["near_teams"] = sorted(
                near_teams, key=lambda team: location.team_distance_from(ll, team)
            )

            #            # If there aren't any teams in the user's geoip area, show them the closest ones
            if context["geoip_lookup"] and len(near_teams) < 1:
                context["closest_teams"] = sorted(
                    Team.public_objects.all(),
                    key=lambda team: location.team_distance_from(ll, team),
                )[:3]
        except Exception as err:
            print("Error looking up nearby teams and events", err)
            traceback.print_exc()

    initial_search = {"distance": near_distance}
    if city is not None and city.id > 0:
        initial_search["city"] = city.id
        context["search_by_city"] = city
    if context["name"]:
        initial_search["name"] = context["name"]
    search_form = SearchTeamsByName(initial=initial_search)
    context["search_form"] = search_form
    return render(request, "get_together/index.html", context)
