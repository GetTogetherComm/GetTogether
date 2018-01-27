from django.contrib import admin

# Register your models here.
from .models.locale import Language, Continent, Country, SPR, City
from .models.profiles import UserProfile, Organization, Team, Member
from .models.search import Searchable
from .models.events import Place, Event, Attendee

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
admin.site.register(Team, TeamAdmin)

admin.site.register(Searchable)

class PlaceAdmin(admin.ModelAdmin):
    raw_id_fields = ('city',)
admin.site.register(Place, PlaceAdmin)

class EventAdmin(admin.ModelAdmin):
    raw_id_fields = ('place', 'created_by')
admin.site.register(Event, EventAdmin)

admin.site.register(Member)
admin.site.register(Attendee)


