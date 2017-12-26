from django.core.management.base import BaseCommand, CommandError
from events.models.search import Searchable, SearchableSerializer
from rest_framework.parsers import JSONParser

import urllib

class Command(BaseCommand):
    help = 'Imports searchable data from another node'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str)

    def handle(self, *args, **options):
        if 'url' in options:
            resp = urllib.request.urlopen(options['url'])
            json_data = JSONParser().parse(resp)
            serializer = SearchableSerializer(data=json_data, many=True)
            if serializer.is_valid():
                serializer.save(federation_node=options['url'])
            else:
                print("Serialized data not valid: %s" % serializer.errors)
        else:
            print("No URL in options!")
