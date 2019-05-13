from django.db import models
from django.utils.translation import ugettext_lazy as _

import pytz
from rest_framework import serializers


class Language(models.Model):
    class Meta:
        ordering = ("name",)

    name = models.CharField(_("Language"), max_length=150, null=True)
    code = models.CharField(_("Language Code"), max_length=20, null=True)

    def __str__(self):
        return u"%s" % (self.name)


class Continent(models.Model):
    name = models.CharField(_("Name"), max_length=50)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return u"%s" % (self.name)


class Country(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Country Code"), max_length=8)
    continents = models.ManyToManyField(Continent)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "Countries"

    def __str__(self):
        return u"%s" % (self.name)

    @property
    def slug(self):
        if self.name is not None:
            return self.name.replace(",", "").replace(" ", "_")
        else:
            return "no_country"


class CountrySerializer(serializers.ModelSerializer):
    display = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = Country
        fields = ("id", "name", "code", "display")


class SPR(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Admin Code"), max_length=8)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return u"%s, %s" % (self.name, self.country.name)

    @property
    def slug(self):
        if self.name is not None:
            return self.name.replace(",", "").replace(" ", "_")
        else:
            return "no_spr"


class SPRSerializer(serializers.ModelSerializer):
    display = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = SPR
        fields = ("id", "name", "code", "country", "slug", "display")


class City(models.Model):
    class Meta:
        ordering = ("name",)
        verbose_name_plural = _("Cities")

    name = models.CharField(_("Name"), max_length=100)
    spr = models.ForeignKey(SPR, on_delete=models.CASCADE)
    tz = models.CharField(
        max_length=32,
        verbose_name=_("Default Timezone"),
        default="UTC",
        choices=[(tz, tz) for tz in pytz.all_timezones],
        blank=False,
        null=False,
        help_text=_("The most commonly used timezone for this Team."),
    )
    longitude = models.FloatField(
        help_text=_("Longitude in Degrees East"), null=True, blank=True
    )
    latitude = models.FloatField(
        help_text=_("Latitude in Degrees North"), null=True, blank=True
    )
    population = models.IntegerField(
        help_text=_("Population"), null=False, blank=False, default=0
    )

    @property
    def short_name(self):
        if self.spr.country.name == "United States":
            return u"%s, %s" % (self.name, self.spr.name)
        else:
            return u"%s, %s" % (self.name, self.spr.country.name)

    def __str__(self):
        return u"%s, %s, %s" % (self.name, self.spr.name, self.spr.country.name)

    @property
    def slug(self):
        if self.name is not None:
            return self.name.replace(",", "").replace(" ", "_")
        else:
            return "no_city"


class CitySerializer(serializers.ModelSerializer):
    display = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = City
        fields = (
            "id",
            "name",
            "short_name",
            "spr",
            "tz",
            "latitude",
            "longitude",
            "slug",
            "display",
        )
