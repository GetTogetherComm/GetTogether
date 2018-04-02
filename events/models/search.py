from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from rest_framework import serializers

from .. import location

import pytz
import datetime

# Provides a searchable index of events that may belong to this site or a federated site
class Searchable(models.Model):
    event_uri = models.CharField(primary_key=True, max_length=256, null=False, blank=False)
    event_url = models.URLField(null=False, blank=False)
    event_title = models.CharField(max_length=256, null=False, blank=False)
    img_url = models.URLField(null=False, blank=False)
    location_name = models.CharField(max_length=256, null=False, blank=False)
    group_name = models.CharField(max_length=256, null=False, blank=False)
    venue_name = models.CharField(max_length=256, null=False, blank=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    latitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    tz = models.CharField(max_length=32, verbose_name=_('Default Timezone'), default='UTC', choices=location.TimezoneChoices(), blank=False, null=False, help_text=_('The most commonly used timezone for this Team.'))
    cost = models.PositiveSmallIntegerField(default=0, blank=True)
    tags = models.CharField(blank=True, null=True, max_length=128)

    origin_node = models.URLField(null=False, blank=False)
    federation_node = models.URLField(null=False, blank=False)
    federation_time = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return u'%s' % (self.event_url)

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

class SearchableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Searchable
        fields = (
            'event_uri',
            'event_url',
            'event_title',
            'img_url',
            'location_name',
            'group_name',
            'venue_name',
            'longitude',
            'latitude',
            'start_time',
            'end_time',
            'cost',
            'tags',
            'origin_node'
        )

