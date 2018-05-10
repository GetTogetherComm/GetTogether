from django.utils.translation import ugettext_lazy as _

from django.conf import settings

import datetime
import simplejson
import geocoder
import math
import traceback

from .new_user import *

KM_PER_DEGREE_LAT = 110.574
KM_PER_DEGREE_LNG = 111.320 # At the equator
DEFAULT_NEAR_DISTANCE = 100 # kilometeres


def get_geoip(request):
    client_ip = get_client_ip(request)
    if client_ip == '127.0.0.1' or client_ip == 'localhost':
        if settings.DEBUG:
            client_ip = '8.8.8.8' # Try Google's server
            print("Client is localhost, using 8.8.8.8 for geoip instead")
        else:
            raise Exception("Client is localhost")

    g = geocoder.ip(client_ip)
    return g


def get_nearby_teams(request, near_distance=DEFAULT_NEAR_DISTANCE):
    g = get_geoip(request)
    if g.latlng is None or g.latlng[0] is None or g.latlng[1] is None:
        print("Could not identify latlng from geoip")
        return Team.objects.none()
    try:
        minlat = g.latlng[0]-(near_distance/KM_PER_DEGREE_LAT)
        maxlat = g.latlng[0]+(near_distance/KM_PER_DEGREE_LAT)
        minlng = g.latlng[1]-(near_distance/(KM_PER_DEGREE_LNG*math.cos(math.radians(g.latlng[0]))))
        maxlng = g.latlng[1]+(near_distance/(KM_PER_DEGREE_LNG*math.cos(math.radians(g.latlng[0]))))

        near_teams = Team.objects.filter(city__latitude__gte=minlat, city__latitude__lte=maxlat, city__longitude__gte=minlng, city__longitude__lte=maxlng)
        return near_teams
    except Exception as e:
        print("Error looking for local teams: ", e)
        return Team.objects.none()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



