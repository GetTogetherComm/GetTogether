import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

import mock
from accounts.email_lists import is_blocked_email
from events.ipstack import get_ipstack_geocoder
from events.models import Member, Team, UserProfile
from model_mommy import mommy

# Create your tests here.


class UserCreationTests(TestCase):
    def setUp(self):
        super().setUp()
        settings.EMAIL_BLOCKLIST = []
        settings.EMAIL_ALLOWLIST = []

    def tearDown(self):
        super().tearDown()

    def test_confirm_email(self):
        user = mommy.make(User, email="test@ggettogether.community")
        assert not is_blocked_email(user.email)
        user.save()

        email_confirmation_url = resolve_url("send-confirm-email")

        c = Client()
        c.force_login(user)
        response = c.get(email_confirmation_url)
        assert response.status_code == 200

    def test_blocked_email(self):
        settings.EMAIL_BLOCKLIST = ["gettogether.community"]
        user = mommy.make(User, email="blocked@gettogether.community")
        assert is_blocked_email(user.email)
        user.save()

        email_confirmation_url = resolve_url("send-confirm-email")

        c = Client()
        c.force_login(user)
        response = c.get(email_confirmation_url)
        assert response.status_code == 302
