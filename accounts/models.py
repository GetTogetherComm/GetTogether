from django.db import models
from django.contrib.sites.models import Site
from django.contrib.auth.models import User, Group, AnonymousUser
from django.utils.translation import ugettext_lazy as _

import pytz
import datetime
import hashlib

class Account(models.Model):
    " Store account information about a user "

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    acctname = models.CharField(_("Account Name"), max_length=150, blank=True)

    badges = models.ManyToManyField('Badge', through='BadgeGrant')

    class Meta:
        ordering = ('user__username',)

    def __str__(self):
        try:
            if self.acctname:
                return self.acctname
            return "%s" % self.user.username
        except:
            return "Unknown Account"


def _getUserAccount(self):
    if not self.is_authenticated:
        return Account()

    profile, created = Account.objects.get_or_create(user=self)

    if created:
        if self.first_name:
            if self.last_name:
                profile.acctname = '%s %s' % (self.first_name, self.last_name)
            else:
                profile.acctname = self.first_name

        profile.save()

    return profile

def _getAnonAccount(self):
    return Account(acctname=_('Anonymous User'))

User.account = property(_getUserAccount)
AnonymousUser.account = property(_getAnonAccount)

class Badge(models.Model):
    name = models.CharField(_('Badge Name'), max_length=64, blank=False, null=False)
    img_url = models.URLField(_('Badge Image'), blank=False, null=False)

    def __str__(self):
        return self.name

class BadgeGrant(models.Model):
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    expires = models.DateTimeField()
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return '%s for %s' % (self.badge.name, self.account.acctname)


