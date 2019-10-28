import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

import mock
from events.ipstack import IPStackResult
from events.models import Attendee, City, Event, Member, Place, Team, UserProfile
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
        settings.USE_TZ = True

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

    def test_private_team_event_in_place(self):
        team = mommy.make(Team, slug="private_team")
        team.access = Team.PRIVATE
        team.save()
        place = mommy.make(Place, name="Test Place", latitude=0.0, longitude=0.0)
        event = mommy.make(
            Event,
            name="Private Event",
            team=team,
            place=place,
            start_time=timezone.now() + datetime.timedelta(days=1),
            end_time=timezone.now() + datetime.timedelta(days=2),
        )
        event.save()

        c = Client()
        response = c.get(reverse("show-place", kwargs={"place_id": place.id}))
        assert response.status_code == 200

        self.assertContains(response, "Private Event", 0)


class EventTimesTests(TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_place_set_when_user_is_utc(self):
        testuser = mommy.make(User, email="test@gettogether.community")
        userProfile = mommy.make(UserProfile, user=testuser, tz="UTC")

        team = mommy.make(Team, slug="test_team")

        place = mommy.make(
            Place,
            name="Test Place",
            latitude=41.8796844,
            longitude=-87.63822920000001,
            tz="America/Chicago",
        )

        start_time = timezone.now() + datetime.timedelta(days=1)
        event = mommy.make(
            Event,
            name="Test Event",
            team=team,
            start_time=start_time,
            end_time=start_time + datetime.timedelta(hours=2),
        )
        localized_start_time = event.localize_datetime(start_time)
        assert event.tz == "UTC"
        assert event.local_start_time == localized_start_time

        event.set_place(place)
        event.save()
        assert event.tz == "America/Chicago"
        assert event.local_start_time == localized_start_time

    def test_add_place_with_different_timezone(self):
        testuser = mommy.make(User, email="test@gettogether.community")
        userProfile = mommy.make(UserProfile, user=testuser, tz="UTC")

        team = mommy.make(Team, owner_profile=userProfile, slug="test_team")

        chicago = mommy.make(City, name="Chicago")
        place = mommy.make(
            Place,
            name="Test Place",
            city=chicago,
            latitude=41.8796844,
            longitude=-87.63822920000001,
            tz="America/Chicago",
        )

        start_time = timezone.now() + datetime.timedelta(days=1)
        event = mommy.make(
            Event,
            name="Test Event",
            team=team,
            start_time=start_time,
            end_time=start_time + datetime.timedelta(hours=2),
        )
        localized_start_time = event.localize_datetime(start_time)
        assert event.tz == "UTC"
        assert event.local_start_time == localized_start_time

        c = Client()
        c.force_login(testuser)
        form_data = {
            "id": place.id,
            "name": place.name,
            "address": place.address,
            "city": place.city.id,
            "longitude": place.longitude,
            "latitude": place.latitude,
            "place_url": "",
            "tz": place.tz,
        }
        response = c.post(
            reverse("add-place", kwargs={"event_id": event.id}), data=form_data
        )

        assert response.status_code == 302
        assert response.url == event.get_absolute_url()

        event = Event.objects.get(id=event.id)
        assert event.tz == "America/Chicago"
        assert event.local_start_time == localized_start_time
