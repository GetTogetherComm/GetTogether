from django.core.management.base import BaseCommand, CommandError

from events.models.locale import Country, SPR, City

# Fields from geoname table, from http://download.geonames.org/export/dump/readme.txt
COMBINED_CODE = 0
NAME = 1
ASCIINAME = 2
GEONAMEID = 3

COUNTRY_CACHE = dict()


class Command(BaseCommand):
    help = 'Loads spr data from GeoNames database file'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str)

    def handle(self, *args, **options):
        if 'file' in options:
            # Preload country cache
            for country in Country.objects.all():
                COUNTRY_CACHE[country.code] = country
            with open(options['file'], 'r') as spr_file:
                for spr_line in spr_file.readlines():
                    if spr_line.startswith("#"):
                        continue
                    spr = spr_line.split("\t")
                    if len(spr) ==4:
                        COUNTRY_CODE, SPR_CODE = spr[COMBINED_CODE].split(".")
                        country = COUNTRY_CACHE.get(COUNTRY_CODE)
                        if country is not None:
                            #print("%s - %s, %s" % (SPR_CODE, spr[NAME], country.name))
                            SPR.objects.get_or_create(name=spr[NAME], code=SPR_CODE, country=country)
                    else:
                        print("Short line (%s): %s" % (len(spr), spr_line))
        else:
            print("No File in options!")
