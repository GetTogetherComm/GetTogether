from django.contrib.sites.models import Site
from django_ical.views import ICalFeed
from django.utils import timezone

import datetime

from .models.events import Event, CommonEvent
from .models.profiles import UserProfile, Team, Organization

class AbstractEventCalendarFeed(ICalFeed):
    def item_guid(self, event):
        site = Site.objects.get(id=1)
        return  '%s@%s' % (event.id, site.domain)

    def item_link(self, event):
        return event.get_full_url()

    def item_title(self, event):
        return event.name

    def item_description(self, event):
        return event.summary

    def item_start_datetime(self, event):
        return event.start_time

    def item_end_datetime(self, event):
        return event.end_time

    def item_created(self, event):
        return event.created_time

    def item_location(self, event):
        if event.place is not None:
            return str(event.place)
        return None

    def item_geo(self, event):
        if event.place is not None:
            latitude = event.place.latitude or None
            longitude = event.place.longitude or None
            return (latitude, longitude)
        elif event.team.city is not None:
            latitude = event.team.city.latitude
            longitude = event.team.city.longitude
            return (latitude, longitude)
        return None

class UserEventsCalendar(AbstractEventCalendarFeed):
    timezone = 'UTC'

    def get_object(self, request, account_secret):
        return UserProfile.objects.get(secret_key=account_secret)

    def items(self, user):
        return Event.objects.filter(attendees=user, end_time__gt=timezone.now()).order_by('-start_time')

class TeamEventsCalendar(AbstractEventCalendarFeed):
    timezone = 'UTC'

    def get_object(self, request, team_id):
        return Team.objects.get(id=team_id)

    def items(self, team):
        return Event.objects.filter(team=team, end_time__gt=timezone.now()).order_by('-start_time')

