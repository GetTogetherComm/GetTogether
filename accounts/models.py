from django.db import models
from django.contrib.sites.models import Site
from django.contrib.auth.models import User, Group, AnonymousUser
from django.utils.translation import ugettext_lazy as _
from django.utils.crypto import get_random_string
from django.conf import settings

import pytz
import datetime
import hashlib

class Account(models.Model):
    " Store account information about a user "

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    acctname = models.CharField(_("Account Name"), max_length=150, blank=True)
    is_email_confirmed = models.BooleanField(default=False)

    has_completed_setup = models.BooleanField(default=False)
    setup_completed_date = models.DateTimeField(blank=True, null=True)

    badges = models.ManyToManyField('Badge', through='BadgeGrant')

    class Meta:
        ordering = ('user__username',)

    def setup_complete(self):
        self.has_completed_setup = True
        self.setup_completed_date = datetime.datetime.now()
        self.save()

    def new_confirmation_request(self):
        valid_for = getattr(settings, 'EMAIL_CONFIRMAION_EXPIRATION_DAYS', 5)
        confirmation_key=get_random_string(length=32)
        return EmailConfirmation.objects.create(
            user=self.user,
            email=self.user.email,
            key=confirmation_key,
            expires=datetime.datetime.now()+datetime.timedelta(days=valid_for)
        )

    def confirm_email(self, confirmation_key):
        try:
            confirmation_request = EmailConfirmation.objects.get(user=self.user, email=self.user.email, key=confirmation_key, expires__gt=datetime.datetime.now())
            if confirmation_request is not None:
                self.is_email_confirmed = True
                self.save()
                confirmation_request.delete()
                return True
        except Exception as e:
            print(e)
            return False

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

class EmailConfirmation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.CharField(max_length=256)
    key = models.CharField(max_length=256)
    expires = models.DateTimeField()

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


class EmailRecord(models.Model):
    """
    Model to store all the outgoing emails.
    """
    when = models.DateTimeField(
        null=False, auto_now_add=True
    )
    sender = models.ForeignKey(User, related_name='sent_messages', null=True, blank=True, on_delete=models.SET_NULL)
    recipient = models.ForeignKey(User, related_name='recv_messages', null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(
        null=False, blank=False,
    )
    subject = models.CharField(
         null=False, max_length=128,
    )
    body = models.TextField(
        null=False, max_length=1024,
    )
    ok = models.BooleanField(
        null=False, default=True,
    )
