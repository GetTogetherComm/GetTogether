from django.core.management.base import BaseCommand, CommandError
from events.models.search import Searchable, SearchableSerializer
from rest_framework.parsers import JSONParser

import urllib
import datetime

class Command(BaseCommand):
    help = 'Imports searchable data from another node'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str)

    def handle(self, *args, **options):
        if 'url' in options:
            resp = urllib.request.urlopen(options['url'])
            json_data = JSONParser().parse(resp)
            for record in json_data:
                record['federation_node'] = options['url']
                record['federation_time'] = datetime.datetime.now()
                Searchable.objects.update_or_create(defaults=record, event_uri=record['event_uri'])

        else:
            print("No URL in options!")
