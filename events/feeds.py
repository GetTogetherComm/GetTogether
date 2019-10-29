import datetime

from django.contrib.sites.models import Site
from django.utils import timezone

from django_ical.views import ICalFeed

from .models.events import CommonEvent, Event
from .models.profiles import Organization, Team, UserProfile


class AbstractEventCalendarFeed(ICalFeed):
    def item_guid(self, event):
        site = Site.objects.get(id=1)
        return "%s@%s" % (event.id, site.domain)

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

    def __call__(self, request, *args, **kwargs):
        response = ICalFeed.__call__(self, request, *args, **kwargs)
        response["Access-Control-Allow-Origin"] = "*"
        return response


class UserEventsCalendar(AbstractEventCalendarFeed):
    timezone = "UTC"

    def get_object(self, request, account_secret):
        return UserProfile.objects.get(secret_key=account_secret)

    def items(self, user):
        return Event.objects.filter(
            attendees=user, end_time__gt=timezone.now()
        ).order_by("-start_time")


class TeamEventsCalendar(AbstractEventCalendarFeed):
    timezone = "UTC"

    def get_object(self, request, team_id):
        return Team.public_objects.get(id=team_id)

    def items(self, team):
        return Event.objects.filter(team=team, end_time__gt=timezone.now()).order_by(
            "-start_time"
        )


class SingleEventCalendar(AbstractEventCalendarFeed):
    timezone = "UTC"

    def get_object(self, request, event_id, event_slug):
        return Event.objects.get(id=event_id)

    def items(self, event):
        return [event]


class PrivateTeamEventsCalendar(AbstractEventCalendarFeed):
    timezone = "UTC"

    def get_object(self, request, team_id, account_secret):
        request_user = UserProfile.objects.get(secret_key=account_secret)
        team = Team.objects.get(id=team_id)
        if team.access == Team.PRIVATE and not request_user.is_in_team(team):
            return None
        return team

    def items(self, team):
        return Event.objects.filter(team=team, end_time__gt=timezone.now()).order_by(
            "-start_time"
        )
