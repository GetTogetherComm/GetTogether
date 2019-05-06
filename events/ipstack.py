from collections import OrderedDict

from django.conf import settings

import requests
from geocoder.base import MultipleResultsQuery, OneResult

IPSTACK_URL = "http://api.ipstack.com/{0}?access_key={1}&format=json&legacy=1"
RESULT_CACHE = OrderedDict()
CACHE_SIZE = getattr(settings, "IPSTACK_CACHE_SIZE", 1000)


class IPStackResult(OneResult):
    @property
    def lat(self):
        return self.raw.get("latitude")

    @property
    def lng(self):
        return self.raw.get("longitude")

    @property
    def latlng(self):
        if self.ok:
            return [self.lat, self.lng]
        return None

    @property
    def ok(self):
        return bool(self.lng is not None and self.lat is not None)

    @property
    def address(self):
        if self.city:
            return u"{0}, {1} {2}".format(self.city, self.state, self.country)
        elif self.state:
            return u"{0}, {1}".format(self.state, self.country)
        elif self.country:
            return u"{0}".format(self.country)
        return u""

    @property
    def postal(self):
        zip_code = self.raw.get("zip_code")
        postal_code = self.raw.get("postal_code")
        if zip_code:
            return zip_code
        if postal_code:
            return postal_code

    @property
    def city(self):
        return self.raw.get("city")

    @property
    def state(self):
        return self.raw.get("region")

    @property
    def region_code(self):
        return self.raw.get("region_code")

    @property
    def country(self):
        return self.raw.get("country_name")

    @property
    def country_code3(self):
        return self.raw.get("country_code3")

    @property
    def continent(self):
        return self.raw.get("continent")

    @property
    def timezone(self):
        return self.raw.get("timezone")

    @property
    def area_code(self):
        return self.raw.get("area_code")

    @property
    def dma_code(self):
        return self.raw.get("dma_code")

    @property
    def offset(self):
        return self.raw.get("offset")

    @property
    def organization(self):
        return self.raw.get("organization")

    @property
    def ip(self):
        return self.raw.get("ip")

    @property
    def time_zone(self):
        return self.raw.get("time_zone")


def get_ipstack_geocoder(ip):
    if ip in RESULT_CACHE:
        return RESULT_CACHE[ip]
    ipstack_key = getattr(settings, "IPSTACK_ACCESS_KEY", None)
    if ipstack_key is None:
        print(
            "You must define IPSTACK_ACCESS_KEY in your setting to use ipstack.com geocoding"
        )
        return IPStackResult({})
    call_url = IPSTACK_URL.format(ip, ipstack_key)

    session = requests.Session()
    response = session.get(call_url)
    if response.status_code != 200:
        raise Exception(
            "Call to ipstack.com returned status code {0}".format(response.status_code)
        )
    result = IPStackResult(response.json())
    RESULT_CACHE[ip] = result
    if len(RESULT_CACHE) > CACHE_SIZE:
        RESULT_CACHE.popitem(last=False)  # Discard the oldest entry
    return result
