from django.db import models
from django.contrib.sites.models import Site
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import reverse
from django.utils import timezone

from rest_framework import serializers
from mptt.models import MPTTModel, TreeForeignKey
from recurrence.fields import RecurrenceField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from .locale import *
from .profiles import *
from .search import *
from .. import location

import re
import pytz
import datetime
import unicodedata
import hashlib

SLUG_OK = '-_~'

class Place(models.Model):
    name = models.CharField(help_text=_('Name of the Place'), max_length=150)
    city = models.ForeignKey(City, verbose_name=_('City'), on_delete=models.CASCADE)
    address = models.CharField(help_text=_('Address with Street and Number'), max_length=150, null=True, blank=True)
    longitude = models.FloatField(help_text=_('Longitude in Degrees East'), null=True, blank=True)
    latitude = models.FloatField(help_text=_('Latitude in Degrees North'), null=True, blank=True)
    tz = models.CharField(max_length=32, verbose_name=_('Timezone'), default='UTC', choices=location.TimezoneChoices(), blank=False, null=False)
    place_url = models.URLField(help_text=_('URL for the Place Homepage'), verbose_name=_('URL of the Place'), max_length=200, blank=True, null=True)
    cover_img = models.URLField(_("Place photo"), null=True, blank=True)

    def __str__(self):
        return u'%s, %s' % (self.name, self.city.name)

class PlaceSerializer(serializers.ModelSerializer):
    city = serializers.CharField(read_only=True)
    class Meta:
        model = Place
        fields = (
            'id',
            'name',
            'city',
            'address',
            'longitude',
            'latitude',
            'tz',
            'place_url',
            'cover_img'
        )


class Event(models.Model):
    name = models.CharField(max_length=150, verbose_name=_('Event Name'))
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    parent = models.ForeignKey('CommonEvent', related_name='participating_events', null=True, blank=True, on_delete=models.SET_NULL)
    series = models.ForeignKey('EventSeries',related_name='instances',  null=True, blank=True, on_delete=models.SET_NULL)

    start_time = models.DateTimeField(help_text=_('Date and time that the event starts'), verbose_name=_('Start Time'), db_index=True)
    end_time = models.DateTimeField(help_text=_('Date and time that the event ends'), verbose_name=_('End Time'), db_index=True)

    summary = models.TextField(help_text=_('Summary of the Event'), blank=True, null=True)

    place = models.ForeignKey(Place, blank=True, null=True, on_delete=models.CASCADE)

    web_url = models.URLField(verbose_name=_('Website'), help_text=_('URL for the event'), max_length=200, blank=True, null=True)
    announce_url = models.URLField(verbose_name=_('Announcement'), help_text=_('URL for the announcement'), max_length=200, blank=True, null=True)

    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_time = models.DateTimeField(help_text=_('the date and time when the event was created'), default=timezone.now, db_index=True)

    tags = models.CharField(verbose_name=_("Keyword Tags"), blank=True, null=True, max_length=128)
    #image
    #replies

    attendees = models.ManyToManyField(UserProfile, through='Attendee', related_name="attending", blank=True)

    @property
    def tz(self):
        if self.place is not None:
            return self.place.tz
        elif self.team is not None:
            return self.team.tz
        else:
            return settings.TIME_ZONE

    @property
    def local_start_time(self, val=None):
        if val is not None:
            self.start_time = val.astimezone(python.utc)
        else:
            if self.start_time is None:
                return None
            event_tz = pytz.timezone(self.tz)
            return timezone.make_naive(self.start_time.astimezone(event_tz), event_tz)

    @property
    def local_end_time(self, val=None):
        if val is not None:
            self.end_time = val.astimezone(python.utc)
        else:
            if self.end_time is None:
                return None
            event_tz = pytz.timezone(self.tz)
            return timezone.make_naive(self.end_time.astimezone(event_tz), event_tz)

    def get_absolute_url(self):
        return reverse('show-event', kwargs={'event_id': self.id, 'event_slug': self.slug})

    def get_full_url(self):
        site = Site.objects.get(id=1)
        return "https://%s%s" % (site.domain, self.get_absolute_url())

    @property
    def slug(self):
        return slugify(self.name)

    def __str__(self):
        return u'%s by %s at %s' % (self.name, self.team.name, self.start_time)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the "real" save() method.
        update_event_searchable(self)

def update_event_searchable(event):
    site = Site.objects.get(id=1)
    event_url = "https://%s%s" % (site.domain, event.get_absolute_url())
    origin_url = "https://%s%s" % (site.domain, reverse('searchables'))

    md5 = hashlib.md5()
    federation_url = event_url.split('/')
    federation_node = '/'.join(federation_url[:3])
    federation_id = '/'.join(federation_url[:5])
    md5.update(bytes(federation_id, 'utf8'))
    event_uri = federation_node + '/' + md5.hexdigest()

    try:
        searchable = Searchable.objects.get(event_uri=event_uri)
    except:
        searchable = Searchable(event_uri)
        searchable.origin_node = origin_url
        searchable.federation_node = origin_url
        searchable.federation_time = timezone.now()

    searchable.event_url = event_url

    if event.team.category:
        searchable.img_url = event.team.category.img_url
    else:
        searchable.img_url = "https://%s%s" % (site.domain, '/static/img/team_placeholder.png')
    searchable.event_title = event.name
    searchable.group_name = event.team.name
    searchable.start_time = event.start_time
    searchable.end_time = event.end_time
    searchable.tz = event.tz
    searchable.cost = 0
    searchable.tags = event.tags
    if (event.place is not None):
        searchable.location_name = str(event.place.city)
        searchable.venue_name = event.place.name
        searchable.longitude = event.place.longitude or None
        searchable.latitude = event.place.latitude or None
    else:
        searchable.location_name = event.team.location_name

    if event.team.city is not None and (searchable.longitude is None or searchable.latitude is None):
        searchable.longitude = event.team.city.longitude
        searchable.latitude = event.team.city.latitude

    searchable.save()

def slugify(s, ok=SLUG_OK, lower=True, spaces=False):
    # L and N signify letter/number.
    # http://www.unicode.org/reports/tr44/tr44-4.html#GC_Values_Table
    rv = []
    for c in unicodedata.normalize('NFKC', s):
        cat = unicodedata.category(c)[0]
        if cat in 'LN' or c in ok:
            rv.append(c)
        if cat == 'Z':  # space
            rv.append(' ')
    new = ''.join(rv).strip()
    if not spaces:
        new = re.sub('[-\s]+', '-', new)
    return new.lower() if lower else new

class Attendee(models.Model):
    NORMAL=0
    CREW=1
    HOST=2
    ROLES = [
        (NORMAL, _("Normal")),
        (CREW, _("Crew")),
        (HOST, _("Host"))
    ]
    NO=-1
    MAYBE=0
    YES=1
    STATUSES = [
        (NO, _("No")),
        (MAYBE, _("Maybe")),
        (YES, _("Yes")),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    role = models.SmallIntegerField(_("Role"), choices=ROLES, default=NORMAL, db_index=True)
    status = models.SmallIntegerField(_("Attending?"), choices=STATUSES, default=YES, db_index=True)
    joined_date = models.DateTimeField(default=timezone.now)
    last_reminded = models.DateTimeField(null=True, blank=True)

    @property
    def role_name(self):
        return Attendee.ROLES[self.role][1]

    @property
    def status_name(self):
        return Attendee.STATUSES[self.status+1][1]

    def __str__(self):
        return "%s at %s" % (self.user, self.event)

class EventPhoto(models.Model):
    event = models.ForeignKey(Event, related_name='photos', on_delete=models.CASCADE)
    title = models.CharField(max_length=256)
    caption = models.TextField(null=True, blank=True)
    src = models.ImageField(verbose_name=_('Photo'), upload_to='event_photos')
    thumbnail = ImageSpecField(source='src',
                                      processors=[ResizeToFill(250, 187)],
                                      format='JPEG',
                                      options={'quality': 60})

class EventComment(MPTTModel):
    REMOVED=-1
    PENDING=0
    APPROVED=1

    STATUSES = [
        (REMOVED, _("Removed")),
        (PENDING, _("Pending")),
        (APPROVED, _("Approved")),
    ]
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, related_name='comments', on_delete=models.CASCADE)
    body = models.TextField()
    created_time = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.SmallIntegerField(choices=STATUSES, default=APPROVED, db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True, on_delete=models.SET_NULL)

    def __str__(self):
        return '%s at %s' % (self.author, self.created_time)

class CommonEvent(models.Model):
    name = models.CharField(max_length=150, verbose_name=_('Event Name'))
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)
    parent = models.ForeignKey('CommonEvent', related_name='sub_events', null=True, blank=True, on_delete=models.SET_NULL)

    start_time = models.DateTimeField(help_text=_('Date and time that the event starts'), verbose_name=_('Start Time'), db_index=True)
    end_time = models.DateTimeField(help_text=_('Date and time that the event ends'), verbose_name=_('End Time'), db_index=True)
    summary = models.TextField(help_text=_('Summary of the Event'), blank=True, null=True)

    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    spr = models.ForeignKey(SPR, null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.SET_NULL)
    place = models.ForeignKey(Place, blank=True, null=True, on_delete=models.SET_NULL)

    web_url = models.URLField(verbose_name=_('Website'), help_text=_('URL for the event'), max_length=200, blank=True, null=True)
    announce_url = models.URLField(verbose_name=_('Announcement'), help_text=_('URL for the announcement'), max_length=200, blank=True, null=True)

    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_time = models.DateTimeField(help_text=_('the date and time when the event was created'), default=timezone.now, db_index=True)

    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=False, null=True)
    topics = models.ManyToManyField('Topic', blank=True)
    tags = models.CharField(verbose_name=_("Keyword Tags"), blank=True, null=True, max_length=128)

    def get_absolute_url(self):
        return reverse('show-common-event', kwargs={'event_id': self.id, 'event_slug': self.slug})

    def get_full_url(self):
        site = self.organization.site
        return "https://%s%s" % (site.domain, self.get_absolute_url())

    @property
    def slug(self):
        return slugify(self.name)

    def __str__(self):
        return self.name

class EventSeries(models.Model):
    name = models.CharField(max_length=150, verbose_name=_('Event Name'))
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    parent = models.ForeignKey('CommonEvent', related_name='planned_events', null=True, blank=True, on_delete=models.SET_NULL)

    recurrences = RecurrenceField(null=True)
    last_time = models.DateTimeField(help_text=_('Date and time of the last created instance in this series'), default=timezone.now, db_index=True)
    start_time = models.TimeField(help_text=_('Local time that the event starts'), verbose_name=_('Start Time'), db_index=True)
    end_time = models.TimeField(help_text=_('Local time that the event ends'), verbose_name=_('End Time'), db_index=True)

    summary = models.TextField(help_text=_('Summary of the Event'), blank=True, null=True)

    place = models.ForeignKey(Place, blank=True, null=True, on_delete=models.CASCADE)

    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_time = models.DateTimeField(help_text=_('the date and time when the event was created'), default=timezone.now, db_index=True)

    tags = models.CharField(verbose_name=_("Keyword Tags"), blank=True, null=True, max_length=128)

    @classmethod
    def from_event(klass, event, recurrences):
        new_series = EventSeries(
            team=event.team,
            parent=event.parent,
            name=event.name,
            start_time=event.local_start_time.time(),
            end_time=event.local_end_time.time(),
            last_time=event.start_time,
            summary=event.summary,
            place=event.place,
            created_by=event.created_by,
            recurrences=recurrences,
        )
        return new_series

    def create_next_in_series(self):
        next_date = self.recurrences.after(self.last_time, dtstart=self.last_time)
        if next_date is None:
            return None
        event_tz = pytz.timezone(self.tz)

        next_start = pytz.utc.localize(timezone.make_naive(event_tz.localize(datetime.datetime.combine(next_date.date(), self.start_time))))
        next_end = pytz.utc.localize(timezone.make_naive(event_tz.localize(datetime.datetime.combine(next_date.date(), self.end_time))))
        next_event = Event(
            series=self,
            team=self.team,
            name=self.name,
            start_time=next_start,
            end_time=next_end,
            summary=self.summary,
            place=self.place,
            created_by=self.created_by,
        )
        next_event.save()
        self.last_time = next_event.start_time
        self.save()
        return next_event

    def get_absolute_url(self):
        return reverse('show-series', kwargs={'series_id': self.id, 'series_slug': self.slug})

    def get_full_url(self):
        site = Site.objects.get(id=1)
        return "https://%s%s" % (site.domain, self.get_absolute_url())

    @property
    def slug(self):
        return slugify(self.name)

    @property
    def tz(self):
        if self.place is not None:
            return self.place.tz
        elif self.team is not None:
            return self.team.tz
        else:
            return settings.TIME_ZONE

    def __str__(self):
        return u'%s by %s at %s' % (self.name, self.team.name, self.start_time)


