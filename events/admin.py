from django.contrib import admin
from django.utils.safestring import mark_safe

# Register your models here.
from .models.locale import Language, Continent, Country, SPR, City
from .models.profiles import (
    UserProfile,
    Organization,
    Team,
    Member,
    Category,
    Topic,
    Sponsor,
)
from .models.search import Searchable
from .models.events import (
    Place,
    Event,
    EventComment,
    EventSeries,
    EventPhoto,
    CommonEvent,
    Attendee,
)
from .models.speakers import (
    Speaker,
    Talk,
    Presentation,
    SpeakerRequest,
)

admin.site.register(Language)
admin.site.register(Continent)
admin.site.register(Country)

class SPRAdmin(admin.ModelAdmin):
    raw_id_fields = ('country',)
    list_filter =('country',)
    search_fields = ('name', 'country__name')
admin.site.register(SPR, SPRAdmin)

class CityAdmin(admin.ModelAdmin):
    raw_id_fields = ('spr',)
    list_display = ('name', 'spr', 'latitude', 'longitude')
    list_filter =('spr__country',)
    search_fields = ('name', 'spr__name')
admin.site.register(City, CityAdmin)

class ProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ('city',)
    list_display = ('user', 'realname', 'city', 'web_url', 'send_notifications', 'do_not_track')
    list_filter = ('send_notifications', 'do_not_track', 'user__last_login')
admin.site.register(UserProfile, ProfileAdmin)

class OrgAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'site')
admin.site.register(Organization, OrgAdmin)

class SponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'web_url')
admin.site.register(Sponsor, SponsorAdmin)

class TeamAdmin(admin.ModelAdmin):
    raw_id_fields = ('country', 'spr', 'city', 'owner_profile', 'admin_profiles', 'contact_profiles', 'sponsors')
    list_display = ('__str__', 'active', 'member_count', 'event_count', 'owner_profile', 'created_date', 'is_premium', 'premium_expires')
    list_filter = ('active', 'is_premium', 'organization', ('country',admin.RelatedOnlyFieldListFilter))
    ordering = ('-created_date',)
    def member_count(self, team):
        return team.members.all().count()
    member_count.short_description = 'Members'
    def event_count(self, team):
        return team.event_set.all().count()
    event_count.short_description = 'Events'
admin.site.register(Team, TeamAdmin)

class SearchableAdmin(admin.ModelAdmin):
    list_display = ('event_url', 'start_time', 'federation_node', 'federation_time')
    list_filter = ('federation_node',)
    ordering = ('-start_time',)
admin.site.register(Searchable, SearchableAdmin)

class PlaceAdmin(admin.ModelAdmin):
    raw_id_fields = ('city',)
admin.site.register(Place, PlaceAdmin)

class EventAdmin(admin.ModelAdmin):
    raw_id_fields = ('place', 'created_by', 'sponsors')
    list_display = ('__str__', 'attendee_count', 'start_time', 'created_by', 'created_time')
    list_filter = ('created_time', ('created_by',admin.RelatedOnlyFieldListFilter), ('team',admin.RelatedOnlyFieldListFilter))
    ordering = ('-start_time',)
    def attendee_count(self, event):
        return event.attendees.all().count()
    attendee_count.short_description = 'Attendees'
admin.site.register(Event, EventAdmin)

class EventPhotoAdmin(admin.ModelAdmin):
    raw_id_fields = ('event',)
    list_display = ('title', 'event', 'view')
    def view(self, photo):
        return mark_safe('<a href="%s" target="_blank"><img src="%s" height="90px"></a>' % (photo.src.url, photo.thumbnail.url))
    view.short_description = 'Photo'
admin.site.register(EventPhoto, EventPhotoAdmin)

class EventCommentAdmin(admin.ModelAdmin):
    raw_id_fields = ('event', 'author')
    list_display = ('event', 'author', 'status', 'created_time')
admin.site.register(EventComment, EventCommentAdmin)

class CommonEventAdmin(admin.ModelAdmin):
    raw_id_fields = ('place', 'city', 'spr', 'country')
    list_display = ('__str__', 'participant_count', 'organization', 'start_time', 'country', 'spr', 'city')
    ordering = ('-start_time',)
    def participant_count(self, event):
        return event.participating_events.all().count()
    participant_count.short_description = 'Participants'
admin.site.register(CommonEvent, CommonEventAdmin)

class EventSeriesAdmin(admin.ModelAdmin):
    raw_id_fields = ('place', 'team')
    list_display = ('__str__', 'instance_count', 'team', 'start_time', 'last_time')
    ordering = ('-last_time',)
    def instance_count(self, series):
        return series.instances.all().count()
    instance_count.short_description = 'Instances'
admin.site.register(EventSeries, EventSeriesAdmin)

class MemberAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'role', 'joined_date')
    list_filter = ('role', 'team', 'joined_date')
admin.site.register(Member, MemberAdmin)

class AttendeeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'role', 'status', 'joined_date', 'last_reminded')
    list_filter = ('role', 'status', 'joined_date')
admin.site.register(Attendee, AttendeeAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'image')
    exclude = ('slug', )
    def image(self, obj):
        return (mark_safe('<img src="%s" title="%s" height="64px" />' % (obj.img_url, obj.name)))
    image.short_description = 'Image'
admin.site.register(Category, CategoryAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category')
    list_filter = ('category',)
    exclude = ('slug', )
admin.site.register(Topic, TopicAdmin)

class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'avatar')
admin.site.register(Speaker, SpeakerAdmin)

class TalkAdmin(admin.ModelAdmin):
    list_display = ('title', 'speaker', 'category')
    list_filter = ('category',)
admin.site.register(Talk, TalkAdmin)

class PresentationAdmin(admin.ModelAdmin):
    list_display = ('talk', 'status', 'event')
    list_filter = ('status',)
admin.site.register(Presentation, PresentationAdmin)

