from django.core.management.base import BaseCommand

from events.models.locale import Country

# Fields from geoname table, from http://download.geonames.org/export/dump/readme.txt
ISO = 0
ISO3 = 1
ISO_NUMERIC = 2
FIPS = 3
COUNTRY = 4
CAPITAL = 5
AREA = 6
POPULATION = 7
CONTINENT = 8
TLD = 9
CURRENCYCODE = 10
CURRENCYNAME = 11
PHONE = 12
POSTAL_CODE_FORMAT = 13
POSTAL_CODE_REGEX = 14
LANGUAGES = 15
GEONAMEID = 16
NEIGHBOURS = 17
EQUIVALENTFIPSCODE = 18


class Command(BaseCommand):
    help = 'Loads country data from GeoNames database file'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str)

    def handle(self, *args, **options):
        if 'file' in options:
            with open(options['file'], 'r') as countries_file:
                for country_line in countries_file.readlines():
                    if country_line.startswith("#"):
                        continue
                    country = country_line.split("\t")
                    if len(country) == 19:
                        # print("%s - %s" % (country[ISO], country[COUNTRY]))
                        Country.objects.get_or_create(name=country[COUNTRY], code=country[ISO])
                    else:
                        print("Short line (%s): %s" % (len(country), country_line))
        else:
            print("No File in options!")
