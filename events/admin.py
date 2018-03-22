from django.contrib import admin
from django.utils.safestring import mark_safe

# Register your models here.
from .models.locale import Language, Continent, Country, SPR, City
from .models.profiles import UserProfile, Organization, Team, Member, Category, Topic
from .models.search import Searchable
from .models.events import Place, Event, EventPhoto, CommonEvent, Attendee

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
    list_filter =('spr__country',)
    search_fields = ('name', 'spr__name')
admin.site.register(City, CityAdmin)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'realname', 'avatar', 'web_url')
admin.site.register(UserProfile, ProfileAdmin)

class OrgAdmin(admin.ModelAdmin):
    list_display = ('name', 'site')
admin.site.register(Organization, OrgAdmin)

class TeamAdmin(admin.ModelAdmin):
    raw_id_fields = ('country', 'spr', 'city', 'owner_profile', 'admin_profiles', 'contact_profiles')
    list_display = ('__str__', 'member_count', 'owner_profile', 'created_date')
    ordering = ('-created_date',)
    def member_count(self, team):
        return team.members.all().count()
    member_count.short_description = 'Members'
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
    raw_id_fields = ('place', 'created_by')
    list_display = ('__str__', 'attendee_count', 'start_time', 'created_by', 'created_time')
    ordering = ('-start_time',)
    def attendee_count(self, event):
        return event.attendees.all().count()
    attendee_count.short_description = 'Attendees'
admin.site.register(Event, EventAdmin)

class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'view')
    def view(self, photo):
        return mark_safe('<a href="%s" target="_blank"><img src="%s" height="90px"></a>' % (photo.src.url, photo.thumbnail.url))
    view.short_description = 'Photo'
admin.site.register(EventPhoto, EventPhotoAdmin)

class CommonEventAdmin(admin.ModelAdmin):
    raw_id_fields = ('place', 'city', 'spr', 'country')
    list_display = ('__str__', 'participant_count', 'organization', 'start_time', 'country', 'spr', 'city')
    ordering = ('-start_time',)
    def participant_count(self, event):
        return event.participating_events.all().count()
    participant_count.short_description = 'Participants'
admin.site.register(CommonEvent, CommonEventAdmin)

class MemberAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'role')
    list_filter = ('role', 'team')
admin.site.register(Member, MemberAdmin)

class AttendeeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'role', 'status')
    list_filter = ('role', 'status')
admin.site.register(Attendee, AttendeeAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image')
    def image(self, obj):
        return (mark_safe('<img src="%s" title="%s" height="64px" />' % (obj.img_url, obj.name)))
    image.short_description = 'Image'
admin.site.register(Category, CategoryAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
