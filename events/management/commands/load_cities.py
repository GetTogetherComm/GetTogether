from django.core.management.base import BaseCommand, CommandError

from events.models.locale import Country, SPR, City

# Fields from geoname table, from http://download.geonames.org/export/dump/readme.txt
GEONAMEID=0
NAME=1
ASCIINAME=2
ALTERNATENAMES=3
LATITUDE=4
LONGITUDE=5
FEATURE_CLASS=6
FEATURE_CODE=7
COUNTRY_CODE=8
COUNTRY_CODE_2=9
ADMIN1=10
ADMIN2=11
ADMIN3=12
ADMIN4=13
POPULATION=14
ELEVATION=15
DIGITAL_ELEVATION=16
TIMEZONE=17
MODIFICATION_DATE=18

COUNTRY_CACHE = dict()
SPR_CACHE = dict()

class Command(BaseCommand):
    help = 'Loads city data from GeoNames database file'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str)

    def handle(self, *args, **options):
        if 'file' in options:
            # Preload country cache
            for country in Country.objects.all():
                COUNTRY_CACHE[country.code] = country
            for spr in SPR.objects.all():
                SPR_CACHE["%s.%s"%(spr.country.code, spr.code)] = spr
            cities_file = open(options['file'], 'r')
            for city_line in cities_file.readlines():
                city = city_line.split("\t")
                if len(city) == 19:
                    if city[FEATURE_CODE] == "PPL" or city[FEATURE_CODE] == "PPLA":
                        country = COUNTRY_CACHE.get(city[COUNTRY_CODE])
                        spr = SPR_CACHE.get("%s.%s"%(city[COUNTRY_CODE], city[ADMIN1]))
                        if country is not None and spr is not None:
                            City.objects.get_or_create(name=city[NAME], spr=spr, tz=city[TIMEZONE])
                else:
                    print("Short line (%s): %s" % (len(city), city_line))
            cities_file.close()

        else:
            print("No File in options!")
