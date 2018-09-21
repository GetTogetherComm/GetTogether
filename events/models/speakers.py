from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from ..utils import slugify
from .locale import *
from .profiles import *
from .events import *
from .search import *
from .. import location

import pytz
import datetime

class Speaker(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    avatar = ProcessedImageField(verbose_name=_("Photo Image"),
                                           upload_to='avatars',
                                           processors=[ResizeToFill(128, 128)],
                                           format='PNG',
                                           blank=True)
    title = models.CharField(max_length=256, blank=True, null=True)
    bio = models.TextField(verbose_name=_('Biography'), blank=True)

    categories = models.ManyToManyField('Category', blank=True)
    topics = models.ManyToManyField('Topic', blank=True)

    def headshot(self):
        if self.avatar:
            return self.avatar
        else:
            return self.user.avatar

    def headshot_url(self):
        if self.avatar is not None and self.avatar.name is not None and self.avatar.name != '':
            return self.avatar.url
        else:
            return self.user.avatar_url()


    def __str__(self):
        if self.title is not None and self.title != '':
            return '%s, %s' % (self.user, self.title)
        else:
            return str(self.user)

class Talk(models.Model):
    PRESENTATION=0
    WORKSHOP=1
    PANEL=2
    ROUNDTABLE=3
    QANDA=4
    DEMO=5
    TYPES = [
        (PRESENTATION, _("Presentation")),
        (WORKSHOP, _("Workshop")),
        (PANEL, _("Panel")),
        (ROUNDTABLE, _("Roundtable")),
        (QANDA, _("Q & A")),
        (DEMO, _("Demonstration")),
    ]
    speaker = models.ForeignKey(Speaker, verbose_name=_('Speaker Bio'), related_name='talks', on_delete=models.CASCADE)
    title = models.CharField(max_length=256)
    abstract = models.TextField()
    talk_type = models.SmallIntegerField(_("Type"), choices=TYPES, default=PRESENTATION)
    web_url = models.URLField(_("Website"), null=True, blank=True)

    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=False, null=True)
    topics = models.ManyToManyField('Topic', blank=True)

    @property
    def future_presentations(self):
        return self.presentations.filter(status__gte=0, event__start_time__gt=timezone.now())

    @property
    def past_presentations(self):
        return self.presentations.filter(status=1, event__start_time__lte=timezone.now())

    def __str__(self):
        self.title


class SpeakerRequest(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    topics = models.ManyToManyField('Topic', blank=True)

class Presentation(models.Model):
    DECLINED=-1
    PROPOSED=0
    ACCEPTED=1

    STATUSES = [
        (DECLINED, _("Declined")),
        (PROPOSED, _("Proposed")),
        (ACCEPTED, _("Accepted")),
    ]
    event = models.ForeignKey(Event, related_name='presentations', on_delete=models.CASCADE)
    talk = models.ForeignKey(Talk, related_name='presentations', on_delete=models.CASCADE, blank=False, null=True)
    status = models.SmallIntegerField(choices=STATUSES, default=PROPOSED, db_index=True)
    start_time = models.DateTimeField(verbose_name=_('Start Time'), db_index=True, null=True, blank=True)

    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=False)
    created_time = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self):
        try:
            return '%s at %s' % (self.talk.title, self.event.name)
        except:
            return "No talk"

