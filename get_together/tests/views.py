import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from django.test import Client, TestCase
from django.utils import timezone

import mock
from model_mommy import mommy

from accounts.models import Account, EmailConfirmation
from events.ipstack import IPStackResult
from events.models import *

# Create your tests here.


def mock_get_geoip(latitude=0.0, longitude=0.0):
    def get_geoip(request):
        g = IPStackResult({"latitude": latitude, "longitude": longitude})
        g.raw["latitude"] = latitude
        g.raw["longitude"] = longitude
        g.raw["address"] = "Testtown, Teststate, USA"
        return g

    return get_geoip


def mock_messages(request, level, message="No message text"):
    print(message)


def mock_nearby_teams(request, near_distance=None):
    return Team.objects.all()


@mock.patch("events.location.get_geoip", mock_get_geoip(latitude=0.0, longitude=0.0))
@mock.patch("django.contrib.messages.add_message", mock_messages)
@mock.patch("get_together.views.utils.get_nearby_teams", mock_nearby_teams)
class ViewTests(TestCase):
    def setUp(self):
        super().setUp()
        settings.IPSTACK_ACCESS_KEY = "gettogether-testing"
        settings.USE_TZ = False

        self.testuser = mommy.make(User, email="test@gettogether.community")
        self.userProfile = mommy.make(
            UserProfile, user=self.testuser, send_notifications=True
        )

        self.userAccount = mommy.make(
            Account, user=self.testuser, is_email_confirmed=True
        )

        self.org = mommy.make(
            Organization,
            owner_profile=self.userProfile,
            name="Test Org",
            slug="test-org",
        )
        self.team = mommy.make(
            Team,
            organization=self.org,
            name="Test team",
            slug="test_team",
            owner_profile=self.userProfile,
        )
        self.event = mommy.make(
            Event,
            team=self.team,
            start_time=datetime.datetime.now() + datetime.timedelta(hours=1),
            end_time=datetime.datetime.now() + datetime.timedelta(hours=2),
        )

    def check_view(self, url, login=False, status=200):
        client = Client(self)
        if login:
            client.force_login(self.testuser)
        response = client.get(url)
        if not response.status_code == status:
            print("check_view(%s) returned %s" % (url, response.status_code))
        assert response.status_code == status
        if response.status_code == 200:
            self.assertContains(response, "trans", 0)
        return response

    def test_teams_list(self):
        self.check_view("/teams/", login=True)

    def test_teams_list_all(self):
        self.check_view("/teams/all/", True)

    def test_show_team_by_slug(self):
        self.check_view("/%s/" % self.team.slug)

    def test_show_team_by_id(self):
        self.check_view("/team/%s/" % self.team.id, status=302)

    def test_show_team(self):
        self.check_view("/%s/" % self.team.slug)

    def test_show_team_events_by_slug(self):
        self.check_view("/%s/events/" % self.team.slug)

    def test_show_team_about_by_slug(self):
        self.team.about_page = "Testing about"
        self.team.save()
        self.check_view("/%s/about/" % self.team.slug)

    def test_create_team(self):
        self.check_view("/+create-team/", login=True)

    def test_edit_team(self):
        self.check_view("/team/%s/+edit/" % self.team.id, login=True)

    def test_delete_team(self):
        self.check_view("/team/%s/+delete/" % self.team.id, login=True)

    def test_manage_members(self):
        self.check_view("/team/%s/+members/" % self.team.id, login=True)

    def test_invite_members(self):
        member = mommy.make(
            Member, team=self.team, user=self.userProfile, role=Member.ADMIN
        )
        self.check_view("/team/%s/+invite/" % self.team.id, login=True)

    def test_change_member_role(self):
        settings.CSRF_VERIFY_TOKEN = False
        member = mommy.make(
            Member, team=self.team, user=self.userProfile, role=Member.ADMIN
        )
        self.check_view(
            "/team/%s/+change_role/%s/" % (self.team.id, member.id),
            login=True,
            status=302,
        )

    def test_places_list(self):
        self.check_view("/places/")

    def test_show_place(self):
        place = mommy.make(Place)
        self.check_view("/places/%s/" % place.id)

    #    def test_create_place(self):
    #        self.check_view('/+create-place/', login=True)

    def test_home(self):
        self.check_view("/")

    def test_start_new_team(self):
        self.check_view("/+create-team/", login=True)

    def test_define_new_team(self):
        self.check_view("/team/%s/+define/" % self.team.id, login=True)

    def test_setup_1_confirm_profile(self):
        self.check_view("/profile/+confirm_profile", login=True)

    def test_setup_2_pick_categories(self):
        self.check_view("/profile/+pick_categories", login=True)

    def test_setup_3_find_teams(self):
        pass  # TODO: the mocked get_nearby_teams isn't being used, need to find out why
        # self.check_view('/profile/+find_teams', login=True)

    def test_setup_4_attend_events(self):
        member = mommy.make(
            Member, team=self.team, user=self.userProfile, role=Member.ADMIN
        )
        self.check_view("/profile/+attend_events", login=True)

    def test_setup_complete(self):
        self.check_view("/profile/+setup_complete", login=True, status=302)

    def test_user_send_confirmation_email(self):
        self.check_view("/profile/+send_confirmation_email", login=True)

    def test_user_confirm_email(self):
        confirmation = self.userAccount.new_confirmation_request()
        self.check_view(
            "/profile/+confirm_email/%s" % confirmation.key, login=True, status=302
        )

    def test_user_confirm_notifications(self):
        self.check_view("/profile/+confirm_notifications", login=True)

    def test_show_org(self):
        self.check_view("/org/%s/" % self.org.slug)

    def test_edit_org(self):
        self.check_view("/org/%s/+edit/" % self.org.slug, login=True)

    def test_request_to_join_org(self):
        member = mommy.make(
            Member, team=self.team, user=self.userProfile, role=Member.ADMIN
        )
        self.check_view("/org/%s/+request_to_join_org/" % self.org.slug, login=True)

    def test_invite_to_join_org(self):
        self.check_view("/team/%s/+invite_to_join_org/" % self.team.id, login=True)

    def test_accept_request_to_join_org(self):
        teamrequest = mommy.make(
            OrgTeamRequest,
            organization=self.org,
            request_origin=OrgTeamRequest.TEAM,
            requested_by=self.userProfile,
        )
        self.check_view(
            "/org/+confirm_request/%s/" % teamrequest.request_key, login=True
        )

    def test_accept_invite_to_join_org(self):
        member = mommy.make(
            Member, team=self.team, user=self.userProfile, role=Member.ADMIN
        )
        orgrequest = mommy.make(
            OrgTeamRequest,
            team=self.team,
            request_origin=OrgTeamRequest.ORG,
            requested_by=self.userProfile,
        )
        self.check_view(
            "/org/+confirm_request/%s/" % orgrequest.request_key, login=True
        )

    def test_manage_org_teams(self):
        self.check_view("/org/%s/+manage_teams/" % self.org.slug, login=True)

    def test_show_common_event(self):
        common = mommy.make(
            CommonEvent, organization=self.org, name="Test common event"
        )
        common.participating_events.add(self.event)
        self.check_view("/common/%s/test-common-event/" % common.id)

    def test_create_common_event(self):
        self.check_view("/org/%s/+create-event/" % self.org.slug, login=True)

    def test_create_common_event_team_select(self):
        common = mommy.make(
            CommonEvent, organization=self.org, name="Test common event"
        )
        self.check_view("/common/%s/+create-event/" % common.id, login=True)

    def test_edit_common_event(self):
        common = mommy.make(
            CommonEvent, organization=self.org, name="Test common event"
        )
        self.check_view("/common/%s/+edit/" % common.id, login=True)

    def test_events_list(self):
        self.check_view("/events/", login=True)

    def test_events_list_all(self):
        self.check_view("/events/all/")

    def test_show_event(self):
        self.check_view("/events/%s/test-event/" % self.event.id)

    def test_do_not_track(self):
        settings.SOCIAL_AUTH_FACEBOOK_KEY = "mock_facebook_key"
        response = self.check_view("/events/%s/test-event/" % self.event.id, login=True)
        self.assertContains(response, "facebookShareButton", 1)
        self.assertContains(response, "attendEventButton", 1)

        self.userProfile.do_not_track = True
        self.userProfile.save()

        response = self.check_view("/events/%s/test-event/" % self.event.id, login=True)
        self.assertContains(response, "facebookShareButton", 0)
        self.assertContains(response, "attendEventButton", 1)

    def test_show_series(self):
        series = mommy.make(EventSeries, team=self.team, name="Test Series")
        self.check_view("/series/%s/test-series/" % series.id)

    def test_create_event_team_select(self):
        # If user has no teams, assume that one and redirect
        self.check_view("/team/+create-event/", login=True, status=302)

        member1 = mommy.make(
            Member, team=self.team, user=self.userProfile, role=Member.ADMIN
        )

        team2 = mommy.make(
            Team,
            organization=self.org,
            name="Test team 2",
            slug="test_team_2",
            owner_profile=self.userProfile,
        )
        member2 = mommy.make(
            Member, team=team2, user=self.userProfile, role=Member.ADMIN
        )

        # Now should render the team select page
        self.check_view("/team/+create-event/", login=True)

    def test_create_event(self):
        self.check_view("/team/%s/+create-event/" % self.team.id, login=True)

    def test_manage_event_sponsors(self):
        self.check_view("/events/%s/+sponsors/" % self.event.id, login=True)

    def test_sponsor_event(self):
        sponsor = mommy.make(Sponsor)
        self.check_view(
            "/events/%s/+sponsor/?sponsor=%s" % (self.event.id, sponsor.id), login=True
        )

    def test_manage_attendees(self):
        self.check_view("/events/%s/+attendees/" % self.event.id, login=True)

    def test_invite_attendees(self):
        self.check_view("/events/%s/+invite/" % self.event.id, login=True)

    def test_attend_event(self):
        settings.CSRF_VERIFY_TOKEN = False
        self.check_view(
            "/events/%s/+attend/?response=no" % self.event.id, login=True, status=302
        )
        self.check_view(
            "/events/%s/+attend/?response=maybe" % self.event.id, login=True, status=302
        )
        self.check_view(
            "/events/%s/+attend/?response=yes" % self.event.id, login=True, status=302
        )
        self.check_view("/events/%s/+attend/" % self.event.id, login=True, status=302)

    def test_attended_event(self):
        attendee = mommy.make(Attendee, user=self.userProfile, event=self.event)
        self.check_view(
            "/events/%s/+attended/?attendee=%s" % (self.event.id, attendee.id),
            login=True,
        )

    def test_comment_add(self):
        # Doesn't do anything on a GET
        self.check_view("/events/%s/+comment/" % self.event.id, login=True, status=302)

    def test_comment_edit(self):
        # Doesn't do anything on a GET
        comment = mommy.make(EventComment, event=self.event, author=self.userProfile)
        self.check_view("/comment/%s/+edit/" % comment.id, login=True, status=302)

    def test_comment_delete(self):
        # Doesn't do anything on a GET
        comment = mommy.make(EventComment, event=self.event, author=self.userProfile)
        self.check_view("/comment/%s/+delete/" % comment.id, login=True)

    def test_add_event_photo(self):
        member = mommy.make(
            Member, team=self.team, user=self.userProfile, role=Member.NORMAL
        )
        self.check_view("/events/%s/+photo/" % self.event.id, login=True)

    # TODO: Removed until we can mock an EventPhoto without uploading a real photo
    # @mock.patch("imagekit.models.ImageSpecField.url", "/static/img/team_placeholder.png")
    # def test_remove_event_photo(self):
    #     member = mommy.make(Member, team=self.team, user=self.userProfile, role=Member.NORMAL)
    #     photo = mommy.make(EventPhoto, event=self.event, uploader=self.userProfile, src='../static/img/team_placeholder.png')
    #     self.check_view('/photo/%s/+remove/' % photo.id, login=True)

    def test_add_place_to_event(self):
        self.check_view("/events/%s/+add_place/" % self.event.id, login=True)

    def test_add_place_to_series(self):
        series = mommy.make(EventSeries, team=self.team, name="Test Series")
        self.check_view("/series/%s/+add_place/" % series.id, login=True)

    def test_edit_event(self):
        self.check_view("/events/%s/+edit/" % self.event.id, login=True)

    def test_change_event_host(self):
        self.check_view("/events/%s/+host/" % self.event.id, login=True)

    def test_delete_event(self):
        self.check_view("/events/%s/+delete/" % self.event.id, login=True)

    def test_cancel_event(self):
        self.check_view("/events/%s/+cancel/" % self.event.id, login=True)

    def test_restore_event(self):
        self.check_view("/events/%s/+restore/" % self.event.id, login=True, status=302)

    def test_edit_series(self):
        series = mommy.make(EventSeries, team=self.team, name="Test Series")
        self.check_view("/series/%s/+edit/" % series.id, login=True)

    def test_delete_series(self):
        series = mommy.make(EventSeries, team=self.team, name="Test Series")
        self.check_view("/series/%s/+delete/" % series.id, login=True)

    def test_list_user_talks(self):
        self.check_view("/profile/+talks", login=True)

    def test_show_speaker(self):
        speaker = mommy.make(Speaker, user=self.userProfile, title="Test Speaker")
        self.check_view("/speaker/%s/" % speaker.id)

    def test_add_speaker(self):
        self.check_view("/profile/+add-speaker", login=True)

    def test_edit_speaker(self):
        speaker = mommy.make(Speaker, user=self.userProfile, title="Test Speaker")
        self.check_view("/speaker/%s/+edit" % speaker.id, login=True)

    def test_delete_speaker(self):
        speaker = mommy.make(Speaker, user=self.userProfile, title="Test Speaker")
        self.check_view("/speaker/%s/+delete" % speaker.id, login=True)

    def test_show_talk(self):
        speaker = mommy.make(Speaker, user=self.userProfile, title="Test Speaker")
        talk = mommy.make(Talk, speaker=speaker, title="Test Talk")
        self.check_view("/talk/%s/" % talk.id)

    def test_add_talk(self):
        speaker = mommy.make(Speaker, user=self.userProfile, title="Test Speaker")
        self.check_view("/profile/+add-talk", login=True)

    def test_edit_talk(self):
        speaker = mommy.make(Speaker, user=self.userProfile, title="Test Speaker")
        talk = mommy.make(Talk, speaker=speaker, title="Test Talk")
        self.check_view("/talk/%s/+edit" % talk.id, login=True)

    def test_delete_talk(self):
        speaker = mommy.make(Speaker, user=self.userProfile, title="Test Speaker")
        talk = mommy.make(Talk, speaker=speaker, title="Test Talk")
        self.check_view("/talk/%s/+delete" % talk.id, login=True)

    def test_propose_event_talk(self):
        speaker = mommy.make(Speaker, user=self.userProfile, title="Test Speaker")
        talk = mommy.make(Talk, speaker=speaker, title="Test Talk")
        self.event.enable_presentations = True
        self.event.save()
        self.check_view("/events/%s/+propose-talk/" % self.event.id, login=True)

    def test_schedule_event_talks(self):
        speaker = mommy.make(Speaker, user=self.userProfile, title="Test Speaker")
        talk = mommy.make(Talk, speaker=speaker, title="Test Talk")
        presentation = mommy.make(
            Presentation, event=self.event, talk=talk, status=Presentation.PROPOSED
        )
        self.check_view("/events/%s/+schedule-talks/" % self.event.id, login=True)

    def test_logout(self):
        self.check_view("/logout/", status=302)

    def test_login(self):
        self.check_view("/login/")

    def test_show_profile(self):
        self.check_view("/profile/%s/" % self.userProfile.id)

    def test_edit_profile(self):
        self.check_view("/profile/+edit", login=True)

    def test_new_event_start(self):
        self.check_view("/+new-event/", login=True)

    def test_new_event_add_place(self):
        self.check_view("/events/%s/+new-event-place/" % self.event.id, login=True)

    def test_new_event_add_details(self):
        self.check_view("/events/%s/+new-event-details/" % self.event.id, login=True)

    def test_new_event_add_team(self):
        self.check_view("/events/%s/+new-event-team/" % self.event.id, login=True)
