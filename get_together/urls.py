"""get_together URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from events import views as event_views
from events import feeds
from . import views

from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('account/password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('account/password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('account/password_reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('account/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('account/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('account/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),


    path('searchables/', event_views.searchable_list, name='searchables'),
    path('api/places/', event_views.places_list),
    path('api/countries/', event_views.country_list),
    path('api/spr/', event_views.spr_list),
    path('api/cities/', event_views.city_list),
    path('api/find_city/', event_views.find_city),
    path('api/org/<int:org_id>/', event_views.org_member_list),

    path('profile/+confirm_profile', views.setup_1_confirm_profile, name='setup-1-confirm-profile'),
    path('profile/+pick_categories', views.setup_2_pick_categories, name='setup-2-pick-categories'),
    path('profile/+find_teams',      views.setup_3_find_teams,      name='setup-3-find-teams'),
    path('profile/+attend_events',   views.setup_4_attend_events,   name='setup-4-attend-events'),
    path('profile/+setup_complete',  views.setup_complete,          name='setup-complete'),

    path('profile/+edit', views.edit_profile, name='edit-profile'),
    path('profile/+send_confirmation_email', views.user_send_confirmation_email, name='send-confirm-email'),
    path('profile/+confirm_email/<str:confirmation_key>', views.user_confirm_email, name='confirm-email'),
    path('profile/+confirm_notifications', views.user_confirm_notifications, name='confirm-notifications'),
    path('profile/<int:user_id>/', views.show_profile, name='show-profile'),
    path('profile/<str:account_secret>.ics', feeds.UserEventsCalendar(), name='user-event-ical'),

    path('profile/+add-speaker', views.add_speaker, name='add-speaker'),
    path('speaker/<int:speaker_id>/', views.show_speaker, name='show-speaker'),
    path('speaker/<int:speaker_id>/+edit', views.edit_speaker, name='edit-speaker'),
    path('speaker/<int:speaker_id>/+delete', views.delete_speaker, name='delete-speaker'),

    path('profile/+talks', views.list_user_talks, name='user-talks'),
    path('profile/+add-talk', views.add_talk, name='add-talk'),
    path('talk/<int:talk_id>/', views.show_talk, name='show-talk'),
    path('talk/<int:talk_id>/+edit', views.edit_talk, name='edit-talk'),
    path('talk/<int:talk_id>/+delete', views.delete_talk, name='delete-talk'),

    path('events/', views.events_list, name='events'),
    path('events/all/', views.events_list_all, name='all-events'),
    path('teams/', views.teams_list, name='teams'),
    path('teams/all/', views.teams_list_all, name='all-teams'),
    path('team/<int:team_id>/', views.show_team_by_id, name='show-team'),
    path('team/<int:team_id>/+edit/', views.edit_team, name='edit-team'),
    path('team/<int:team_id>/+join/', event_views.join_team, name='join-team'),
    path('team/<int:team_id>/+leave/', event_views.leave_team, name='leave-team'),
    path('team/<int:team_id>/+delete/', views.delete_team, name='delete-team'),
    path('team/<int:team_id>/+members/', views.manage_members, name='manage-members'),
    path('team/<int:team_id>/+change_role/<int:profile_id>/', views.change_member_role, name='change-member-role'),
    path('team/<int:team_id>/+invite/', views.invite_members, name='invite-members'),
    path('team/<int:team_id>/events.ics', feeds.TeamEventsCalendar(), name='team-event-ical'),

    path('+create-team/', views.start_new_team, name='create-team'),
    path('team/<int:team_id>/+define/', views.define_new_team, name='define-team'),
    path('team/+create-event/', views.create_event_team_select, name='create-event-team-select'),
    path('team/<int:team_id>/+create-event/', views.create_event, name='create-event'),

    path('+new-event/', views.new_event_start, name='new-event-start'),
    path('events/<int:event_id>/+new-event-place/', views.new_event_add_place, name='new-event-add-place'),
    path('events/<int:event_id>/+new-event-details/', views.new_event_add_details, name='new-event-add-details'),
    path('events/<int:event_id>/+new-event-team/', views.new_event_add_team, name='new-event-add-team'),

    path('events/<int:event_id>/+edit/', views.edit_event, name='edit-event'),
    path('events/<int:event_id>/+host/', views.change_event_host, name='change-team'),
    path('events/<int:event_id>/+attend/', views.attend_event, name='attend-event'),
    path('events/<int:event_id>/+attended/', views.attended_event, name='attended-event'),
    path('events/<int:event_id>/+attendees/', views.manage_attendees, name='manage-attendees'),
    path('events/<int:event_id>/+sponsors/', views.manage_event_sponsors, name='manage-event-sponsors'),
    path('events/<int:event_id>/+sponsor/', views.sponsor_event, name='sponsor-event'),
    path('events/<int:event_id>/+invite/', views.invite_attendees, name='invite-attendees'),
    path('events/<int:event_id>/+delete/', views.delete_event, name='delete-event'),
    path('events/<int:event_id>/+cancel/', views.cancel_event, name='cancel-event'),
    path('events/<int:event_id>/+restore/', views.restore_event, name='restore-event'),
    path('events/<int:event_id>/+add_place/', views.add_place_to_event, name='add-place'),
    path('events/<int:event_id>/+comment/', views.comment_event, name='comment-event'),
    path('events/<int:event_id>/+photo/', views.add_event_photo, name='add-event-photo'),
    path('photo/<int:photo_id>/+remove/', views.remove_event_photo, name='remove-event-photo'),
    path('events/<int:event_id>/+propose-talk/', views.propose_event_talk, name='propose-event-talk'),
    path('events/<int:event_id>/+schedule-talks/', views.schedule_event_talks, name='schedule-event-talks'),
    path('events/<int:event_id>/<str:event_slug>/', views.show_event, name='show-event'),

    path('series/<int:series_id>/+edit/', views.edit_series, name='edit-series'),
    path('series/<int:series_id>/+delete/', views.delete_series, name='delete-series'),
    path('series/<int:series_id>/+add_place/', views.add_place_to_series, name='add-place-to-series'),
    path('series/<int:series_id>/<str:series_slug>/', views.show_series, name='show-series'),

    path('org/<str:org_slug>/', views.show_org, name='show-org'),
    path('org/<str:org_slug>/+edit/', views.edit_org, name='edit-org'),
    path('team/<int:team_id>/+invite_to_join_org/', views.invite_to_join_org, name='invite-to-join-org'),
    path('org/<str:org_slug>/+request_to_join_org/', views.request_to_join_org, name='request-to-join-org'),
    path('org/+confirm_request/<str:request_key>/', views.confirm_request_to_join_org, name='confirm-request-to-join-org'),
    path('org/<str:org_slug>/+manage_teams/', views.manage_org_teams, name='manage-teams'),
    path('org/<str:org_slug>/+create-event/', views.create_common_event, name='create-common-event'),
    path('common/<int:event_id>/+create-event/', views.create_common_event_team_select, name='create-common-event-team-select'),
    path('common/<int:event_id>/+edit/', views.edit_common_event, name='edit-common-event'),
    path('common/<int:event_id>/<str:event_slug>/', views.show_common_event, name='show-common-event'),

    path('places/', views.places_list, name='places'),
    path('places/<int:place_id>/', views.show_place, name='show-place'),
    #path('+create-place/', views.create_place, name='create-place'),

    path('about/', include('django.contrib.flatpages.urls')),

    path('oauth/', include('social_django.urls', namespace='social')),

    path('activity_pub/', include('events.activity_pub.urls')),

    path('<str:team_slug>/', views.show_team_by_slug, name='show-team-by-slug'),
    path('<str:team_slug>/about/', views.show_team_about_by_slug, name='show-team-about-by-slug'),
    path('<str:team_slug>/events/', views.show_team_events_by_slug, name='show-team-events-by-slug'),
]
if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
