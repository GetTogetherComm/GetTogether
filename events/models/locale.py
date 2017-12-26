from django.db import models
from django.utils.translation import ugettext_lazy as _

class Language(models.Model):
    class Meta:
        ordering = ('name',)
    name = models.CharField(_("Language"), max_length=150, null=True)
    code = models.CharField(_("Language Code"), max_length=20, null=True)

    def __str__(self):
        return u'%s' % (self.name)


class Continent(models.Model):
    name = models.CharField(_("Name"), max_length=50)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return u'%s' % (self.name)


class Country(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Country Code"), max_length=8)
    continents = models.ManyToManyField(Continent)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return u'%s' % (self.name)

    @property
    def slug(self):
        if self.name is not None:
            return self.name.replace(',', '').replace(' ', '_')
        else:
            return 'no_country'

class SPR(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return u'%s, %s' % (self.name, self.country.name)

    @property
    def slug(self):
        if self.name is not None:
            return self.name.replace(',', '').replace(' ', '_')
        else:
            return 'no_spr'

class City(models.Model):
    class Meta:
        ordering = ('name',)
        verbose_name_plural = _("Cities")

    name = models.CharField(_("Name"), max_length=100)
    spr = models.ForeignKey(SPR, on_delete=models.CASCADE)

    def __str__(self):
        return u'%s, %s, %s' % (self.name, self.spr.name, self.spr.country.name)

    @property
    def slug(self):
        if self.name is not None:
            return self.name.replace(',', '').replace(' ', '_')
        else:
            return 'no_city'



