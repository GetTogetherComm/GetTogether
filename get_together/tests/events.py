from django.test import TestCase, Client
from model_mommy import mommy

from django.contrib.auth.models import User
from events.models import Event, Attendee, UserProfile
# Create your tests here.
class EventDisplayTests(TestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_show_event(self):
        event = mommy.make(Event)
        event.save()

        event_url = event.get_absolute_url()

        c = Client()
        response = c.get(event_url)
        assert(response.status_code == 200)

    def test_show_event_attendee_without_avatar(self):
        event = mommy.make(Event)
        event.save()

        profile = mommy.make(UserProfile, avatar='')
        profile.save()

        attendee = mommy.make(Attendee, event=event, user=profile, role=Attendee.NORMAL, status= Attendee.YES)
        attendee.save()

        c = Client()
        response = c.get(event.get_absolute_url())
        assert(response.status_code == 200)

