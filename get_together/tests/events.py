import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from django.test import Client, TestCase
from django.utils import timezone

import mock
from events.ipstack import IPStackResult
from events.models import Attendee, Event, Member, Place, Team, UserProfile
from model_mommy import mommy

# Create your tests here.


def mock_get_geoip(latitude=0.0, longitude=0.0):
    def get_geoip(request):
        g = IPStackResult({})
        g.raw["latitude"] = latitude
        g.raw["longitude"] = longitude
        return g

    return get_geoip


class EventDisplayTests(TestCase):
    def setUp(self):
        super().setUp()
        settings.USE_TZ = False

    def tearDown(self):
        super().tearDown()

    @mock.patch(
        "events.location.get_geoip", mock_get_geoip(latitude=0.0, longitude=0.0)
    )
    def test_events_list(self):
        place = mommy.make(Place, name="Test Place", latitude=0.0, longitude=0.0)
        event = mommy.make(
            Event,
            name="Test Event",
            place=place,
            start_time=timezone.now() + datetime.timedelta(days=1),
            end_time=timezone.now() + datetime.timedelta(days=2),
        )
        event.save()

        c = Client()
        response = c.get(resolve_url("all-events"))
        assert response.status_code == 200

    @mock.patch(
        "events.location.get_geoip", mock_get_geoip(latitude=None, longitude=None)
    )
    def test_events_list_no_geoip(self):
        place = mommy.make(Place, name="Test Place", latitude=0.0, longitude=0.0)
        event = mommy.make(
            Event,
            name="Test Event",
            place=place,
            start_time=timezone.now() + datetime.timedelta(days=1),
            end_time=timezone.now() + datetime.timedelta(days=2),
        )
        event.save()

        c = Client()
        response = c.get(resolve_url("all-events"))
        assert response.status_code == 200

    def test_show_event(self):
        event = mommy.make(Event)
        event.save()

        event_url = event.get_absolute_url()

        c = Client()
        response = c.get(event_url)
        assert response.status_code == 200

    def test_show_event_attendee_without_avatar(self):
        event = mommy.make(Event)
        event.save()

        profile = mommy.make(UserProfile, avatar="")
        profile.save()

        attendee = mommy.make(
            Attendee,
            event=event,
            user=profile,
            role=Attendee.NORMAL,
            status=Attendee.YES,
        )
        attendee.save()

        c = Client()
        response = c.get(event.get_absolute_url())
        assert response.status_code == 200

    def test_private_team_event_hidden_for_non_members(self):
        team = mommy.make(Team, slug="private_team")
        team.access = Team.PRIVATE
        team.save()

        event = mommy.make(Event, team=team)
        event.save()

        c = Client()
        response = c.get(event.get_absolute_url())
        assert response.status_code == 404

    def test_private_team_event_visible_for_members(self):
        team = mommy.make(Team, slug="private_team")
        team.access = Team.PRIVATE
        team.save()

        event = mommy.make(Event, team=team)
        event.save()

        testuser = mommy.make(User, email="test@gettogether.community")
        userProfile = mommy.make(UserProfile, user=testuser, send_notifications=True)

        member = mommy.make(Member, team=team, user=userProfile, role=Member.NORMAL)

        c = Client()
        c.force_login(testuser)

        response = c.get(event.get_absolute_url())
        assert response.status_code == 200
