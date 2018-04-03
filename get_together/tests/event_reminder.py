from django.test import TestCase
from django.core.management import call_command
from django.core import mail
from django.utils import timezone
from model_mommy import mommy
from model_mommy.recipe import Recipe
import datetime

from django.contrib.auth.models import User

from events.models.events import Event, Attendee
from events.models.profiles import UserProfile

class UpcommingEventReminderTest(TestCase):

    def setUp(self):
        super().setUp()

        user = mommy.make(User, email='test@gettogether.community')

        self.userProfile = mommy.make(UserProfile, user=user, send_notifications=True)
        self.event = mommy.make(Event, start_time=timezone.now() + datetime.timedelta(hours=1))


    def tearDown(self):
        super().tearDown()


    def test_reminder(self):
        attendee = mommy.make(Attendee, event=self.event, user=self.userProfile, status=Attendee.YES)

        call_command('send_event_reminder')

        self.assertEquals(len(mail.outbox), 1)


    def test_reminder_updated_last_reminded(self):
        attendee = mommy.make(Attendee, event=self.event, user=self.userProfile, status=Attendee.YES)
        last_reminded = attendee.last_reminded

        call_command('send_event_reminder')

        attendee.refresh_from_db()

        self.assertNotEqual(attendee.last_reminded, last_reminded)


    def test_quick_successive_reminders(self):
        attendee = mommy.make(Attendee, event=self.event, user=self.userProfile, status=Attendee.YES)

        call_command('send_event_reminder')
        call_command('send_event_reminder')

        self.assertEquals(len(mail.outbox), 1)
