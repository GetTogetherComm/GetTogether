from collections import Mapping, OrderedDict

from django.contrib.sites.models import Site
from django.db import models
from django.shortcuts import resolve_url
from django.utils import timezone

import pytz
from events.models import Event, Place, Team
from rest_framework import serializers
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.utils import representation
from rest_framework.utils.serializer_helpers import ReturnDict


def localized_time(dt, tz="UTC"):
    event_tz = pytz.timezone(tz)
    print("Searchable timezone: %s" % tz)
    return dt.astimezone(event_tz).strftime("%Y-%m-%dT%H:%M:%S%z")


class CollectionSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        # Dealing with nested relationships, data can be a Manager,
        # so, first get a queryset from the Manager if needed
        iterable = data.all() if isinstance(data, models.Manager) else data

        repr_data = OrderedDict(
            {
                "@context": "https://www.w3.org/ns/activitystreams",
                "summary": self.child.verbose_name_plural,
                "type": "Collection",
                "totalItems": len(iterable),
                "items": [self.child.to_representation(item) for item in iterable],
            }
        )
        repr_data.move_to_end("@context", last=False)
        repr_data.move_to_end("items")
        return repr_data

    @property
    def data(self):
        ret = super(serializers.ListSerializer, self).data
        return ReturnDict(ret, serializer=self)


class APGroupSerializer(serializers.ModelSerializer):
    verbose_name_plural = "Groups"

    context = serializers.CharField(
        label="context", default="https://www.w3.org/ns/activitystreams"
    )
    type = serializers.CharField(label="type", default="Group")
    id = serializers.CharField(source="get_absolute_url")
    name = serializers.CharField(source="__str__")
    url = serializers.CharField(source="web_url")

    class Meta:
        list_serializer_class = CollectionSerializer
        model = Team
        fields = ("context", "type", "id", "name", "url")

    def to_representation(self, instance):
        data = super(APGroupSerializer, self).to_representation(instance)
        data["@context"] = data["context"]
        del data["context"]
        data.move_to_end("@context", last=False)

        data["id"] = "http://%s%s" % (Site.objects.get_current().domain, data["id"])
        return data


class APPlaceSerializer(serializers.ModelSerializer):
    verbose_name_plural = "Places"

    context = serializers.CharField(
        label="context", default="https://www.w3.org/ns/activitystreams"
    )
    type = serializers.CharField(label="type", default="Place")
    id = serializers.CharField(source="get_absolute_url")
    name = serializers.CharField(source="__str__")
    latitude = serializers.DecimalField(max_digits=10, decimal_places=5)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=5)
    url = serializers.URLField(source="place_url")

    class Meta:
        list_serializer_class = CollectionSerializer
        model = Place
        fields = ("context", "type", "id", "name", "latitude", "longitude", "url")

    def to_representation(self, instance):
        data = super(APPlaceSerializer, self).to_representation(instance)
        data["@context"] = data["context"]
        del data["context"]
        data.move_to_end("@context", last=False)

        data["id"] = "http://%s%s" % (Site.objects.get_current().domain, data["id"])
        return data


class APEventSerializer(serializers.ModelSerializer):
    verbose_name_plural = "Events"

    context = serializers.CharField(default="https://www.w3.org/ns/activitystreams")
    type = serializers.CharField(default="Event")
    id = serializers.CharField(source="get_absolute_url")
    name = serializers.CharField()
    attributedTo = APGroupSerializer(source="team")
    location = APPlaceSerializer(source="place")
    startTime = serializers.DateTimeField(source="start_time")
    endTime = serializers.DateTimeField(source="end_time")
    image = serializers.URLField(source="team.card_img_url")
    url = serializers.URLField(source="web_url")
    published = serializers.DateTimeField(source="created_time")

    class Meta:
        list_serializer_class = CollectionSerializer
        model = Event
        fields = (
            "context",
            "type",
            "id",
            "name",
            "startTime",
            "endTime",
            "attributedTo",
            "location",
            "image",
            "url",
            "published",
        )

    def to_representation(self, instance):
        data = super(APEventSerializer, self).to_representation(instance)
        data["@context"] = data["context"]
        del data["context"]
        data.move_to_end("@context", last=False)

        if data["image"].startswith("/"):
            data["image"] = "/".join(data["id"].split("/")[:3]) + data["image"]

        data["id"] = "http://%s%s" % (Site.objects.get_current().domain, data["id"])
        return data


@api_view(["GET"])
def events_list(request):
    serializer = APEventSerializer(
        Event.objects.filter(end_time__gte=timezone.now(), team__access=Team.PUBLIC),
        many=True,
    )
    return Response(serializer.data)


@api_view(["GET"])
def places_list(request):
    serializer = APPlaceSerializer(Place.objects.all(), many=True)
    return Response(serializer.data)
