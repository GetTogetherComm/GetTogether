from django.db import models
from django.contrib.sites.models import Site
from django.contrib.auth.models import User, Group, AnonymousUser
from django.utils.translation import ugettext_lazy as _

from .locale import *

import pytz

class UserProfile(models.Model):
    " Store profile information about a user "

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    realname = models.CharField(_("Real Name"), max_length=150, blank=True)
    tz = models.CharField(max_length=32, verbose_name=_('Timezone'), default='UTC', choices=[(tz, tz) for tz in pytz.all_timezones], blank=False, null=False, help_text=_('The most commonly used timezone for this User.'))
    avatar = models.URLField(verbose_name=_("Photo"), max_length=150, blank=True, null=True)

    web_url = models.URLField(verbose_name=_('Website URL'), blank=True, null=True)
    twitter = models.CharField(verbose_name=_('Twitter Name'), max_length=32, blank=True, null=True)
    facebook = models.URLField(verbose_name=_('Facebook URL'), max_length=32, blank=True, null=True)

    class Meta:
        ordering = ('user__username',)

    def __str__(self):
        try:
            if self.realname:
                return "%s (%s)" % (self.user.username, self.realname)
            return "%s" % self.user.username
        except:
            return "Unknown Profile"

    def get_timezone(self):
        try:
            return pytz.timezone(self.tz)
        except:
            return pytz.utc
    timezone = property(get_timezone)

    def tolocaltime(self, dt):
        as_utc = pytz.utc.localize(dt)
        return as_utc.astimezone(self.timezone)

    def fromlocaltime(self, dt):
        local = self.timezone.localize(dt)
        return local.astimezone(pytz.utc)

    def can_create_event(self, team):
        if not self.user_id:
            return False
        if self.user.is_superuser:
            return True
        if team.owner_profile == self:
            return True
        if self in team.admin_profiles.all():
            return True
        if self in team.contact_profiles.all():
            return True
        return False

def get_user_timezone(username):
    # TODO: find a smarter way to get timezone
    return 'UTC'

def _getUserProfile(self):
    if not self.is_authenticated:
        return UserProfile()

    profile, created = UserProfile.objects.get_or_create(user=self)

    if created:
        profile.tz = get_user_timezone(self.username)
        profile.save()

    return profile

def _getAnonProfile(self):
    return UserProfile()

User.profile = property(_getUserProfile)
AnonymousUser.profile = property(_getAnonProfile)

class Organization(models.Model):
    name = models.CharField(max_length=256, null=False, blank=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    def __str__(self):
        return u'%s' % (self.name)

class Team(models.Model):
    name = models.CharField(max_length=256, null=False, blank=False)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)

    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    spr = models.ForeignKey(SPR, null=True, blank=True, on_delete=models.CASCADE)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)

    web_url = models.URLField(_("Website"), null=True, blank=True)
    email = models.EmailField(_("Email Address"), null=True, blank=True)

    created_date = models.DateField(_("Date Created"), null=True, blank=True)

    owner_profile = models.ForeignKey(UserProfile, related_name='owner', null=True, on_delete=models.CASCADE)
    admin_profiles = models.ManyToManyField(UserProfile, related_name='admins', blank=True)
    contact_profiles = models.ManyToManyField(UserProfile, related_name='contacts', blank=True)

    cover_img = models.URLField(_("Team Photo"), null=True, blank=True)
    languages = models.ManyToManyField(Language, blank=True)
    active = models.BooleanField(_("Active Team"), default=True)
    tz = models.CharField(max_length=32, verbose_name=_('Default Timezone'), default='UTC', choices=[(tz, tz) for tz in pytz.all_timezones], blank=False, null=False, help_text=_('The most commonly used timezone for this Team.'))

    def __str__(self):
        return u'%s' % (self.name)

