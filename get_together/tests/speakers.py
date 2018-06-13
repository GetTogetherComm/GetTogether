from django.test import TestCase, Client
from django.shortcuts import resolve_url
from model_mommy import mommy

from django.contrib.auth.models import User
from events.models import Speaker, Talk

# Create your tests here.
class TalkCreationTests(TestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_resume_adding_talk(self):
        user = User.objects.create(username='testuser', password='12345', is_active=True)

        c = Client()
        response = c.force_login(user)

        response = c.get(resolve_url('add-talk'))
        assert(response.status_code == 302)
        assert(response.url == resolve_url('add-speaker'))

        response = c.get(resolve_url('add-speaker'))
        assert(response.status_code == 200)
        response = c.post(resolve_url('add-speaker'), {'title': 'test', 'bio': 'testing'})
        assert(response.status_code == 302)
        assert(response.url == resolve_url('add-talk'))

