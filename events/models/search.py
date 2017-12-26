from django.db import models
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

import datetime

# Provides a searchable index of events that may belong to this site or a federated site
class Searchable(models.Model):
    event_url = models.URLField(primary_key=True, null=False, blank=False)
    event_title = models.CharField(max_length=256, null=False, blank=False)
    location_name = models.CharField(max_length=256, null=False, blank=False)
    group_name = models.CharField(max_length=256, null=False, blank=False)
    venue_name = models.CharField(max_length=256, null=False, blank=False)
    longitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    latitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    cost = models.PositiveSmallIntegerField(default=0, blank=True)
    tags = models.CharField(blank=True, null=True, max_length=128)

    origin_node = models.URLField(null=False, blank=False)
    federation_node = models.URLField(null=False, blank=False)
    federation_time = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return u'%s' % (self.event_url)

class SearchableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Searchable
        fields = (
            'event_url',
            'event_title',
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

    def save(self, federation_node):
        self.federation_node = federation_node
        super().save()

    def update(self, instance, validated_data):
        validated_data['federation_node'] = self.federation_node
        return super().update(instance, validated_data)
