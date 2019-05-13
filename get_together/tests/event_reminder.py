import datetime

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from model_mommy import mommy
from model_mommy.recipe import Recipe

from events.models.events import Attendee, Event
from events.models.profiles import UserProfile


class UpcommingEventReminderTest(TestCase):
    def setUp(self):
        super().setUp()

        user = mommy.make(User, email="test@gettogether.community")

        self.userProfile = mommy.make(UserProfile, user=user, send_notifications=True)
        self.event = mommy.make(
            Event, start_time=timezone.now() + datetime.timedelta(hours=1)
        )

    def tearDown(self):
        super().tearDown()

    def test_reminder(self):
        attendee = mommy.make(
            Attendee, event=self.event, user=self.userProfile, status=Attendee.YES
        )

        call_command("send_event_reminder")

        self.assertEquals(len(mail.outbox), 1)

    def test_reminder_updated_last_reminded(self):
        attendee = mommy.make(
            Attendee, event=self.event, user=self.userProfile, status=Attendee.YES
        )
        last_reminded = attendee.last_reminded

        call_command("send_event_reminder")

        attendee.refresh_from_db()

        self.assertNotEqual(attendee.last_reminded, last_reminded)

    def test_quick_successive_reminders(self):
        attendee = mommy.make(
            Attendee, event=self.event, user=self.userProfile, status=Attendee.YES
        )

        call_command("send_event_reminder")
        call_command("send_event_reminder")

        self.assertEquals(len(mail.outbox), 1)

    def test_successive_reminders_after_a_day(self):
        attendee = mommy.make(
            Attendee, event=self.event, user=self.userProfile, status=Attendee.YES
        )
        attendee_id = attendee.id

        call_command("send_event_reminder")
        self.assertEquals(len(mail.outbox), 1)

        attendee.last_reminded = timezone.now() - datetime.timedelta(days=2)
        attendee.save()
        # This should send another email, because the last one was more than a day ago
        call_command("send_event_reminder")

        self.assertEquals(len(mail.outbox), 2)

    def test_reminders_only_for_the_upcoming_day(self):
        attendee = mommy.make(
            Attendee, event=self.event, user=self.userProfile, status=Attendee.YES
        )
        self.event.start_time = timezone.now() + datetime.timedelta(days=2)
        self.event.save()

        call_command("send_event_reminder")
        self.assertEquals(len(mail.outbox), 0)

        self.event.start_time = timezone.now() + datetime.timedelta(hours=23)
        self.event.save()

        call_command("send_event_reminder")
        self.assertEquals(len(mail.outbox), 1)
