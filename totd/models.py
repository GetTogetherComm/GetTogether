from django.conf import settings
from django.contrib.messages.constants import DEFAULT_TAGS, INFO
from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone


# Create your models here.
class Tip(models.Model):
    name = models.CharField(max_length=128, null=False, blank=False)
    text = models.TextField()
    level = models.SmallIntegerField(choices=DEFAULT_TAGS.items(), default=INFO)

    run_start = models.DateTimeField(default=timezone.now)
    run_end = models.DateTimeField(null=True, blank=True)

    view = models.CharField(max_length=256, blank=True, null=True)
    sites = models.ManyToManyField(Site)

    seen_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="seen_tips", blank=True
    )

    def tags(self):
        return settings.MESSAGE_TAGS[self.level]

    def __str__(self):
        return self.name
