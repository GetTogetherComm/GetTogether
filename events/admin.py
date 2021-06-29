from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Q
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models.events import (
    Attendee,
    CommonEvent,
    Event,
    EventComment,
    EventPhoto,
    EventSeries,
    Place,
)
from .models.locale import SPR, City, Continent, Country, Language
from .models.profiles import (
    Category,
    Member,
    Organization,
    OrgTeamRequest,
    Sponsor,
    Team,
    TeamMembershipRequest,
    Topic,
    UserProfile,
)
from .models.search import Searchable
from .models.speakers import Presentation, Speaker, SpeakerRequest, Talk

admin.site.register(Language)
admin.site.register(Continent)
admin.site.register(Country)


def ban_user(banned_user):
    banned_user.is_active = False
    banned_user.save()
    for team in Team.objects.filter(owner_profile__user=banned_user):
        team.access = Team.PRIVATE
        team.save()
    return True


def countFilter(field_name):
    class CountFilter(SimpleListFilter):
        title = "%s Count" % field_name.title()
        parameter_name = "%s_count" % field_name

        def lookups(self, request, model_admin):
            return (
                ("0", "0"),
                ("1", "1"),
                ("2", "2 - 9"),
                ("10", "10 - 99"),
                ("100", "100+"),
                (">0", "> 0"),
            )

        def queryset(self, request, queryset):
            if self.value() == "0":
                return queryset.annotate(num_events=Count(field_name)).filter(
                    num_events=0
                )
            if self.value() == ">0":
                return queryset.annotate(num_events=Count(field_name)).filter(
                    num_events__gt=0
                )
            if self.value() == "1":
                return queryset.annotate(num_events=Count(field_name)).filter(
                    num_events=1
                )
            if self.value() == "2":
                return queryset.annotate(num_events=Count(field_name)).filter(
                    num_events__gte=2, num_events__lte=9
                )
            if self.value() == "10":
                return queryset.annotate(num_events=Count(field_name)).filter(
                    num_events__gte=10, num_events__lte=99
                )
            if self.value() == "100":
                return queryset.annotate(num_events=Count(field_name)).filter(
                    num_events__gte=100
                )

    return CountFilter


class SPRAdmin(admin.ModelAdmin):
    raw_id_fields = ("country",)
    list_filter = ("country",)
    search_fields = ("name", "country__name")


admin.site.register(SPR, SPRAdmin)


class CityAdmin(admin.ModelAdmin):
    raw_id_fields = ("spr",)
    list_display = ("name", "spr", "latitude", "longitude", "population")
    list_filter = ("spr__country",)
    search_fields = ("name", "spr__name")


admin.site.register(City, CityAdmin)


class ProfileAdmin(admin.ModelAdmin):
    search_fields = ("user__username", "user__email", "realname")
    raw_id_fields = ("city",)
    list_display = (
        "user",
        "realname",
        "city",
        "web_url",
        "send_notifications",
        "do_not_track",
    )
    list_filter = ("send_notifications", "do_not_track", "user__last_login")


admin.site.register(UserProfile, ProfileAdmin)


class OrgAdmin(admin.ModelAdmin):
    raw_id_fields = ("owner_profile",)
    list_display = ("name", "slug", "team_count", "owner_profile", "site")

    def team_count(self, org):
        return org.teams.all().count()

    team_count.short_description = "Teams"


admin.site.register(Organization, OrgAdmin)


class OrgRequestAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "team",
        "request_origin",
        "requested_by",
        "requested_date",
        "accepted_by",
        "joined_date",
    )
    list_filter = ("organization", "request_origin")


admin.site.register(OrgTeamRequest, OrgRequestAdmin)


class SponsorAdmin(admin.ModelAdmin):
    list_display = ("name", "web_url", "event_count")
    list_filter = (countFilter("events"),)

    def event_count(self, sponsor):
        return sponsor.events.all().count()

    event_count.short_description = "Sponsored Events"


admin.site.register(Sponsor, SponsorAdmin)


class TeamAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    raw_id_fields = (
        "country",
        "spr",
        "city",
        "owner_profile",
        "admin_profiles",
        "contact_profiles",
        "sponsors",
    )
    list_display = (
        "__str__",
        "open_link",
        "member_count",
        "event_count",
        "owner_profile",
        "created_date",
        "access",
        "active",
    )
    list_filter = (
        "access",
        "organization",
        countFilter("member"),
        countFilter("event"),
        ("country", admin.RelatedOnlyFieldListFilter),
        "active",
    )
    ordering = ("-created_date",)

    actions = ("ban_team_owner",)

    def ban_team_owner(self, request, queryset):
        ban_count = 0
        try:
            for team in queryset.all():
                if ban_user(team.owner_profile.user):
                    ban_count += 1
            self.message_user(request, "%s users banned" % ban_count)
        except Exception as e:
            self.message_user(
                request=request,
                message="Error banning users: %s" % e,
                level=messages.WARNING,
            )

    def member_count(self, team):
        return team.members.all().count()

    member_count.short_description = "Members"

    def event_count(self, team):
        return team.event_set.all().count()

    event_count.short_description = "Events"

    def open_link(self, team):
        return mark_safe(
            '<a href="%s" target="_blank">Open</a>' % team.get_absolute_url()
        )

    open_link.short_description = "Link"


admin.site.register(Team, TeamAdmin)


class TeamMembershipRequestAdmin(admin.ModelAdmin):
    list_display = (
        "team",
        "user",
        "invite_email",
        "request_origin",
        "requested_by",
        "requested_date",
        "accepted_by",
        "joined_date",
    )
    list_filter = ("team", "request_origin")


admin.site.register(TeamMembershipRequest, TeamMembershipRequestAdmin)


class SearchableAdmin(admin.ModelAdmin):
    search_fields = ("event_title",)
    list_display = ("event_url", "start_time", "federation_node", "federation_time")
    list_filter = ("federation_node",)
    ordering = ("-start_time",)


admin.site.register(Searchable, SearchableAdmin)


class PlaceAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "event_count", "city", "place_url")
    list_filter = ("city__spr__country",)
    raw_id_fields = ("city",)

    def event_count(self, place):
        return place.event_set.all().count()

    event_count.short_description = "Events"


admin.site.register(Place, PlaceAdmin)


class EventAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    raw_id_fields = ("place", "created_by", "sponsors")
    list_display = (
        "__str__",
        "open_link",
        "attendee_count",
        "start_time",
        "created_by",
        "created_time",
    )
    list_filter = (
        "created_time",
        "start_time",
        countFilter("attendee"),
        ("team__country", admin.RelatedOnlyFieldListFilter),
    )
    ordering = ("-start_time",)

    actions = ("ban_event_creator",)

    def ban_event_creator(self, request, queryset):
        ban_count = 0
        try:
            for event in queryset.all():
                if ban_user(event.created_by.user):
                    ban_count += 1
            self.message_user(request, "%s users banned" % ban_count)
        except Exception as e:
            self.message_user(
                request=request,
                message="Error banning users: %s" % e,
                level=messages.WARNING,
            )

    def attendee_count(self, event):
        return event.attendees.all().count()

    attendee_count.short_description = "Attendees"

    def open_link(self, event):
        return mark_safe(
            '<a href="%s" target="_blank">Open</a>' % event.get_absolute_url()
        )

    open_link.short_description = "Link"


admin.site.register(Event, EventAdmin)


class EventPhotoAdmin(admin.ModelAdmin):
    raw_id_fields = ("event",)
    list_display = ("title", "event", "view")

    def view(self, photo):
        return mark_safe(
            '<a href="%s" target="_blank"><img src="%s" height="90px"></a>'
            % (photo.src.url, photo.thumbnail.url)
        )

    view.short_description = "Photo"


admin.site.register(EventPhoto, EventPhotoAdmin)


class EventCommentAdmin(admin.ModelAdmin):
    raw_id_fields = ("event", "author")
    list_display = ("event", "author", "status", "created_time")


admin.site.register(EventComment, EventCommentAdmin)


class CommonEventAdmin(admin.ModelAdmin):
    raw_id_fields = ("place", "city", "spr", "country")
    list_display = (
        "__str__",
        "participant_count",
        "organization",
        "start_time",
        "country",
        "spr",
        "city",
    )
    ordering = ("-start_time",)

    def participant_count(self, event):
        return event.participating_events.all().count()

    participant_count.short_description = "Participants"


admin.site.register(CommonEvent, CommonEventAdmin)


class EventSeriesAdmin(admin.ModelAdmin):
    raw_id_fields = ("place", "team")
    list_display = ("__str__", "instance_count", "team", "start_time", "last_time")
    list_filter = (("team", admin.RelatedOnlyFieldListFilter), countFilter("instances"))
    ordering = ("-last_time",)

    def instance_count(self, series):
        return series.instances.all().count()

    instance_count.short_description = "Instances"


admin.site.register(EventSeries, EventSeriesAdmin)


class MemberAdmin(admin.ModelAdmin):
    list_display = ("__str__", "role", "joined_date")
    list_filter = ("role", "team", "joined_date")


admin.site.register(Member, MemberAdmin)


class AttendeeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "role", "status", "joined_date", "last_reminded")
    list_filter = ("role", "status", "joined_date")


admin.site.register(Attendee, AttendeeAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "image")
    exclude = ("slug",)

    def image(self, obj):
        return mark_safe(
            '<img src="%s" title="%s" height="64px" />' % (obj.img_url, obj.name)
        )

    image.short_description = "Image"


admin.site.register(Category, CategoryAdmin)


class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category")
    list_filter = ("category",)
    exclude = ("slug",)


admin.site.register(Topic, TopicAdmin)


class SpeakerAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "avatar")


admin.site.register(Speaker, SpeakerAdmin)


class TalkAdmin(admin.ModelAdmin):
    list_display = ("title", "speaker", "category")
    list_filter = ("category",)


admin.site.register(Talk, TalkAdmin)


class PresentationAdmin(admin.ModelAdmin):
    list_display = ("talk", "status", "event")
    list_filter = ("status",)


admin.site.register(Presentation, PresentationAdmin)
