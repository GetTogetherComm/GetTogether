from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils import timezone

from events.models import Event, EventSeries

import time
import datetime

class Command(BaseCommand):
    help = "Generates the next event for any series that needs one"

    def handle(self, *args, **options):
        needs_update = EventSeries.objects.filter(last_time__lte=timezone.now())

        for series in needs_update:
            next_event = series.create_next_in_series()
            if next_event is not None:
                print("Created new event: %s" % next_event)
