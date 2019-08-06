import datetime
import hashlib

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import pytz
from rest_framework import serializers

from .. import location


# Provides a searchable index of events that may belong to this site or a federated site
class Searchable(models.Model):
    event_uri = models.CharField(
        primary_key=True, max_length=256, null=False, blank=False
    )
    event_url = models.URLField(null=False, blank=False)
    event_title = models.CharField(max_length=256, null=False, blank=False)
    img_url = models.URLField(null=False, blank=False)
    location_name = models.CharField(max_length=256, null=False, blank=False)
    group_name = models.CharField(max_length=256, null=False, blank=False)
    venue_name = models.CharField(max_length=256, null=False, blank=True)
    longitude = models.DecimalField(
        max_digits=12, decimal_places=8, null=True, blank=True
    )
    latitude = models.DecimalField(
        max_digits=12, decimal_places=8, null=True, blank=True
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    tz = models.CharField(
        max_length=32,
        verbose_name=_("Default Timezone"),
        default="UTC",
        choices=location.TimezoneChoices(),
        blank=False,
        null=False,
        help_text=_("The most commonly used timezone for this Team."),
    )
    cost = models.PositiveSmallIntegerField(default=0, blank=True)
    tags = models.CharField(blank=True, null=True, max_length=128)

    origin_node = models.URLField(null=False, blank=False)
    federation_node = models.URLField(null=False, blank=False)
    federation_time = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return u"%s" % (self.event_url)

    @property
    def local_start_time(self, val=None):
        if val is not None:
            self.start_time = val.astimezone(pytz.utc)
        else:
            if self.start_time is None:
                return None
            event_tz = pytz.timezone(self.tz)
            return timezone.make_naive(self.start_time.astimezone(event_tz), event_tz)

    @property
    def local_end_time(self, val=None):
        if val is not None:
            self.end_time = val.astimezone(pytz.utc)
        else:
            if self.end_time is None:
                return None
            event_tz = pytz.timezone(self.tz)
            return timezone.make_naive(self.end_time.astimezone(event_tz), event_tz)


class SearchableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Searchable
        fields = (
            "event_uri",
            "event_url",
            "event_title",
            "img_url",
            "location_name",
            "group_name",
            "venue_name",
            "longitude",
            "latitude",
            "start_time",
            "end_time",
            "cost",
            "tags",
            "origin_node",
        )


def update_event_searchable(event):
    site = Site.objects.get(id=1)
    if settings.DEBUG:
        schema = "http"
    else:
        schema = "https"

    event_url = "%s://%s%s" % (schema, site.domain, event.get_absolute_url())
    origin_url = "%s://%s%s" % (schema, site.domain, reverse("searchables"))

    md5 = hashlib.md5()
    federation_url = event_url.split("/")
    federation_node = "/".join(federation_url[:3])
    federation_id = "/".join(federation_url[:5])
    md5.update(bytes(federation_id, "utf8"))
    event_uri = federation_node + "/" + md5.hexdigest()

    try:
        searchable = Searchable.objects.get(event_uri=event_uri)
    except:
        searchable = Searchable(event_uri)
        searchable.origin_node = origin_url
        searchable.federation_node = origin_url
        searchable.federation_time = timezone.now()

    searchable.event_url = event_url

    if event.team.card_img_url.startswith(
        "http:"
    ) or event.team.card_img_url.startswith("https:"):
        searchable.img_url = event.team.card_img_url
    else:
        searchable.img_url = "%s://%s%s" % (
            schema,
            site.domain,
            event.team.card_img_url,
        )

    searchable.event_title = event.name
    searchable.group_name = event.team.name
    searchable.start_time = event.start_time
    searchable.end_time = event.end_time
    searchable.tz = event.tz
    searchable.cost = 0
    searchable.tags = event.tags
    if event.place is not None:
        searchable.location_name = str(event.place.city)
        searchable.venue_name = event.place.name
        if event.place.longitude is not None and event.place.latitude is not None:
            searchable.longitude = event.place.longitude
            searchable.latitude = event.place.latitude
        elif event.place.city is not None:
            searchable.longitude = event.place.city.longitude
            searchable.latitude = event.place.city.latitude
    else:
        searchable.location_name = event.team.location_name

    if event.team.city is not None and (
        searchable.longitude is None or searchable.latitude is None
    ):
        searchable.longitude = event.team.city.longitude
        searchable.latitude = event.team.city.latitude

    searchable.save()


def delete_event_searchable(event):
    site = Site.objects.get(id=1)
    if settings.DEBUG:
        schema = "http"
    else:
        schema = "https"
    event_url = "%s://%s%s" % (schema, site.domain, event.get_absolute_url())
    origin_url = "%s://%s%s" % (schema, site.domain, reverse("searchables"))

    md5 = hashlib.md5()
    federation_url = event_url.split("/")
    federation_node = "/".join(federation_url[:3])
    federation_id = "/".join(federation_url[:5])
    md5.update(bytes(federation_id, "utf8"))
    event_uri = federation_node + "/" + md5.hexdigest()

    try:
        searchable = Searchable.objects.get(event_uri=event_uri)
        searchable.delete()
    except:
        pass
