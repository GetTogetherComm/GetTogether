from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from events.models.locale import City
from events.models.events import Event, Place, Attendee
from events.models.profiles import Team, UserProfile, Member
from events.models.search import Searchable
from events.forms import SearchForm
from events import location

from accounts.decorators import setup_wanted
from django.conf import settings

import datetime
import simplejson
import geocoder
import math
import traceback

from .teams import *
from .events import *
from .places import *
from .user import *
from .new_user import *
from .new_team import *
from .speakers import *
from .utils import *

KM_PER_DEGREE_LAT = 110.574
KM_PER_DEGREE_LNG = 111.320 # At the equator
DEFAULT_NEAR_DISTANCE = 100 # kilometeres
# Create your views here.

@setup_wanted
def home(request, *args, **kwards):
    context = {}
    if request.user.is_authenticated:
        user_teams = Team.objects.filter(owner_profile=request.user.profile)
        if len(user_teams) > 0:
            context['user_teams'] = user_teams

    near_distance = int(request.GET.get("distance", DEFAULT_NEAR_DISTANCE))
    context['distance'] = near_distance

    city=None
    ll = None
    if "city" in request.GET and request.GET.get("city"):
        context['city_search'] = True
        city = City.objects.get(id=request.GET.get("city"))
        context['city'] = city
        ll = [city.latitude, city.longitude]
    else :
        context['city_search'] = False
        try:
            g = location.get_geoip(request)
            if g.latlng is not None and g.latlng[0] is not None and g.latlng[1] is not None:
                ll = g.latlng
                context['geoip_lookup'] = True

                try:
                    city_distance = 1 #km
                    while city is None and city_distance < 100:
                        minlat = ll[0]-(city_distance/KM_PER_DEGREE_LAT)
                        maxlat = ll[0]+(city_distance/KM_PER_DEGREE_LAT)
                        minlng = ll[1]-(city_distance/(KM_PER_DEGREE_LNG*math.cos(math.radians(ll[0]))))
                        maxlng = ll[1]+(city_distance/(KM_PER_DEGREE_LNG*math.cos(math.radians(ll[0]))))
                        nearby_cities = City.objects.filter(latitude__gte=minlat, latitude__lte=maxlat, longitude__gte=minlng, longitude__lte=maxlng)
                        if len(nearby_cities) == 0:
                            city_distance += 1
                        else:
                            city = sorted(nearby_cities, key=lambda city: location.city_distance_from(ll, city))[0]

                    if request.user.profile.city is None:
                        profile = request.user.profile
                        profile.city = city
                        profile.save()
                except:
                    pass # City lookup failed

        except Exception as err:
            context['geoip_lookup'] = False
            print("Geocoder lookup failed for %s" % request.META.get('REMOTE_ADDR'), err)
            traceback.print_exc()

    #import pdb; pdb.set_trace()
    if ll is not None:
        context['latitude'] = ll[0]
        context['longitude'] = ll[1]
        try:
            minlat = ll[0]-(near_distance/KM_PER_DEGREE_LAT)
            maxlat = ll[0]+(near_distance/KM_PER_DEGREE_LAT)
            minlng = ll[1]-(near_distance/(KM_PER_DEGREE_LNG*math.cos(math.radians(ll[0]))))
            maxlng = ll[1]+(near_distance/(KM_PER_DEGREE_LNG*math.cos(math.radians(ll[0]))))
            context['minlat'] = minlat
            context['maxlat'] = maxlat
            context['minlng'] = minlng
            context['maxlng'] = maxlng

            near_events = Searchable.objects.filter(latitude__gte=minlat, latitude__lte=maxlat, longitude__gte=minlng, longitude__lte=maxlng, end_time__gte=datetime.datetime.now())
            context['near_events'] = sorted(near_events, key=lambda searchable: location.searchable_distance_from(ll, searchable))

            near_teams = Team.objects.filter(city__latitude__gte=minlat, city__latitude__lte=maxlat, city__longitude__gte=minlng, city__longitude__lte=maxlng)
            context['near_teams'] = sorted(near_teams, key=lambda team: location.team_distance_from(ll, team))

#            # If there aren't any teams in the user's geoip area, direct them to start one
            if context['geoip_lookup'] and len(near_teams) < 1 and len(near_events) < 1:
                messages.add_message(request, messages.INFO, message=_('There are no teams or events yet in your area, be the first to start one!'))
                return redirect('create-team')
        except Exception as err:
            print("Error looking up nearby teams and events", err)
            traceback.print_exc()

    initial_search = {'distance': near_distance}
    if city is not None and city.id > 0:
        initial_search['city'] = city.id
    search_form = SearchForm(initial=initial_search)
    context['search_form'] = search_form
    return render(request, 'get_together/index.html', context)

