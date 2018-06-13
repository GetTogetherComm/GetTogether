from django.utils import timezone
from django.conf import settings

from .models.locale import City

import math
import pytz
import datetime
import geocoder

KM_PER_DEGREE_LAT = 110.574
KM_PER_DEGREE_LNG = 111.320 # At the equator

class TimezoneChoices():

    def __iter__(self):
        for tz in pytz.all_timezones:
            yield (tz, tz)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_geoip(request):
    client_ip = get_client_ip(request)
    if client_ip == '127.0.0.1' or client_ip == 'localhost':
        if settings.DEBUG:
            client_ip = getattr(settings, 'DEBUG_IP', '8.8.8.8') # Try Google's server
            print("Client is localhost, using %s for geoip instead" % client_ip)
        else:
            raise Exception("Client is localhost")

    g = geocoder.ip(client_ip)
    return g

def get_bounding_box(center, radius):
    minlat = center[0]-(radius/KM_PER_DEGREE_LAT)
    maxlat = center[0]+(radius/KM_PER_DEGREE_LAT)
    minlng = center[1]-(radius/(KM_PER_DEGREE_LNG*math.cos(math.radians(center[0]))))
    maxlng = center[1]+(radius/(KM_PER_DEGREE_LNG*math.cos(math.radians(center[0]))))
    return (minlat, maxlat, minlng, maxlng)

def distance(center1, center2):
    avglat = (center2[0] + center1[0])/2
    dlat = (center2[0] - center1[0]) * KM_PER_DEGREE_LAT
    dlng = (center2[1] - center1[1]) * (KM_PER_DEGREE_LNG*math.cos(math.radians(avglat)))
    dkm = math.sqrt((dlat*dlat) + (dlng*dlng))
    return dkm

def city_distance_from(ll, city):
    if ll is None:
        return 0
    if city is not None and city.latitude is not None and city.longitude is not None:
        return distance((ll), (city.latitude, city.longitude))
    else:
        return 99999

def team_distance_from(ll, team):
    if ll is None:
        return 0
    if team.city is not None:
        return city_distance_from(ll, team.city)
    else:
        return 99999

def event_distance_from(ll, event):
    if ll is None:
        return 0
    if event.place is not None and event.place.latitude is not None and event.place.longitude is not None:
        return distance((ll), (event.place.latitude, event.place.longitude))
    if event.team is not None:
        return team_distance_from(ll, event.team)
    else:
        return 99999

def searchable_distance_from(ll, searchable):
    if ll is None:
        return 0
    if searchable.latitude is not None and searchable.longitude is not None:
        return distance((ll), (float(searchable.latitude), float(searchable.longitude)))
    else:
        return 99999

def get_nearest_city(ll, max_distance=100):
    if ll is None:
        return None
    city = None
    city_distance = 1 #km
    while city is None and city_distance <= max_distance:
        minlat = ll[0]-(city_distance/KM_PER_DEGREE_LAT)
        maxlat = ll[0]+(city_distance/KM_PER_DEGREE_LAT)
        minlng = ll[1]-(city_distance/(KM_PER_DEGREE_LNG*math.cos(math.radians(ll[0]))))
        maxlng = ll[1]+(city_distance/(KM_PER_DEGREE_LNG*math.cos(math.radians(ll[0]))))
        nearby_cities = City.objects.filter(latitude__gte=minlat, latitude__lte=maxlat, longitude__gte=minlng, longitude__lte=maxlng)
        if len(nearby_cities) == 0:
            city_distance += 1
        else:
            return sorted(nearby_cities, key=lambda city: city_distance_from(ll, city))[0]
    return city
