import datetime
import hashlib
import uuid

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group, User
from django.contrib.sites.models import Site
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import pytz
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import Adjust, ColorOverlay, ResizeToFill, ResizeToFit
from rest_framework import serializers

from .. import location
from ..utils import slugify
from .locale import *


class UserProfile(models.Model):
    " Store profile information about a user "

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    realname = models.CharField(verbose_name=_("Real Name"), max_length=150, blank=True)
    tz = models.CharField(
        max_length=32,
        verbose_name=_("Timezone"),
        default="UTC",
        choices=location.TimezoneChoices(),
        blank=False,
        null=False,
    )
    avatar = ProcessedImageField(
        verbose_name=_("Photo Image"),
        upload_to="avatars",
        processors=[ResizeToFill(128, 128)],
        format="PNG",
        blank=True,
    )
    city = models.ForeignKey(
        City,
        verbose_name=_("Home city"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    web_url = models.URLField(verbose_name=_("Website URL"), blank=True, null=True)
    twitter = models.CharField(
        verbose_name=_("Twitter Name"), max_length=32, blank=True, null=True
    )
    facebook = models.URLField(
        verbose_name=_("Facebook URL"), max_length=32, blank=True, null=True
    )

    send_notifications = models.BooleanField(
        verbose_name=_("Send notification emails"), default=True
    )
    do_not_track = models.BooleanField(verbose_name=_("Do not track"), default=False)

    secret_key = models.UUIDField(default=uuid.uuid4, editable=True)

    categories = models.ManyToManyField("Category", blank=True)
    topics = models.ManyToManyField("Topic", blank=True)

    class Meta:
        ordering = ("user__username",)

    def __str__(self):
        try:
            if self.realname:
                return self.realname
            return "%s" % self.user.username
        except:
            return _("Unknown Profile")

    @property
    def personal_team(self):
        teams = Team.objects.filter(access=Team.PERSONAL, owner_profile=self)
        if teams.count() > 0:
            return teams[0]
        else:
            new_slug = slugify(str(self))
            slug_matches = list(Team.objects.filter(slug=new_slug))
            if len(slug_matches) == 0 or (
                len(slug_matches) == 1 and slug_matches[0].owner_profile.id == self.id
            ):
                team_slug = new_slug
            else:
                team_slug = "%s-u%s" % (new_slug, self.id)

            return Team.objects.create(
                name=str(self),
                slug=team_slug,
                access=Team.PERSONAL,
                owner_profile=self,
                city=self.city,
            )

    def avatar_url(self):
        try:
            if (
                self.avatar is None
                or self.avatar.name is None
                or self.avatar.name == ""
            ):
                return settings.STATIC_URL + "img/avatar_placeholder.png"
            elif self.avatar.name.startswith("http"):
                return self.avatar.name
            else:
                return self.avatar.url
        except:
            return settings.STATIC_URL + "img/avatar_placeholder.png"

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

    @property
    def is_a_team_admin(self):
        return (
            Member.objects.filter(
                user=self,
                role=Member.ADMIN,
                team__access__in=(Team.PUBLIC, Team.PRIVATE),
            ).count()
            > 0
        )

    @property
    def administering(self):
        return [
            member.team
            for member in Member.objects.filter(
                user=self,
                role=Member.ADMIN,
                team__access__in=(Team.PUBLIC, Team.PRIVATE),
            ).order_by("team__name")
        ]

    @property
    def is_a_team_moderator(self):
        return (
            Member.objects.filter(
                user=self,
                role__in=(Member.ADMIN, Member.MODERATOR),
                team__access__in=(Team.PUBLIC, Team.PRIVATE),
            ).count()
            > 0
        )

    @property
    def moderating(self):
        return [
            member.team
            for member in Member.objects.filter(
                user=self,
                role__in=(Member.ADMIN, Member.MODERATOR),
                team__access__in=(Team.PUBLIC, Team.PRIVATE),
            ).order_by("team__name")
        ]

    def can_create_event(self, team):
        try:
            if self.user.is_superuser:
                return True
        except:
            return False
        if not self.user_id:
            return False
        if team.owner_profile == self:
            return True
        if self in team.moderators:
            return True
        return False

    def can_edit_series(self, series):
        try:
            if self.user.is_superuser:
                return True
        except:
            return False
        if series.created_by == self:
            return True
        if series.team.owner_profile == self:
            return True
        if self in series.team.moderators:
            return True
        return False

    def can_edit_event(self, event):
        try:
            if self.user.is_superuser:
                return True
        except:
            return False
        if event.created_by == self:
            return True
        if event.team.owner_profile == self:
            return True
        if self in event.team.moderators:
            return True
        return False

    def can_edit_org(self, org):
        try:
            if self.user.is_superuser:
                return True
        except:
            return False
        if not self.user_id:
            return False
        if org.owner_profile == self:
            return True
        return False

    def can_create_common_event(self, org):
        try:
            if self.user.is_superuser:
                return True
        except:
            return False
        if not self.user_id:
            return False
        if org.owner_profile == self:
            return True
        return False

    def can_edit_team(self, team):
        try:
            if self.user.is_superuser:
                return True
        except:
            return False
        if team.owner_profile == self:
            return True
        if self in team.administrators:
            return True
        return False

    def is_in_team(self, team):
        if team.owner_profile == self:
            return True
        return Member.objects.filter(team=team, user=self).count() > 0


def get_user_timezone(username):
    # TODO: find a smarter way to get timezone
    return "UTC"


def _getUserProfile(self):
    if not self.is_authenticated:
        return UserProfile()

    profile, created = UserProfile.objects.get_or_create(user=self)

    if created:
        profile.tz = get_user_timezone(self.username)
        if self.first_name:
            if self.last_name:
                profile.realname = "%s %s" % (self.first_name, self.last_name)
            else:
                profile.realname = self.first_name

        if self.email:
            h = hashlib.md5()
            h.update(bytearray(profile.user.email, "utf8"))
            profile.avatar = (
                "https://www.gravatar.com/avatar/%s.jpg?d=mm" % h.hexdigest()
            )

        profile.save()

    return profile


def _getAnonProfile(self):
    return UserProfile()


User.profile = property(_getUserProfile)
AnonymousUser.profile = property(_getAnonProfile)


class Organization(models.Model):
    name = models.CharField(max_length=256, null=False, blank=False)
    slug = models.CharField(max_length=256, null=False, blank=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    owner_profile = models.ForeignKey(
        UserProfile,
        related_name="owned_orgs",
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
    )

    cover_img = models.ImageField(
        verbose_name=_("Cover Image"), upload_to="org_covers", null=True, blank=True
    )
    tile_img = ImageSpecField(
        source="cover_img",
        processors=[Adjust(contrast=0.8, color=1), ResizeToFill(338, 200)],
        format="PNG",
    )

    banner_img = ImageSpecField(
        source="cover_img",
        processors=[Adjust(contrast=0.8, color=1), ResizeToFill(825, 200)],
        format="PNG",
    )

    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            new_slug = slugify(self.name)
            slug_matches = list(Organization.objects.filter(slug=new_slug))
            if len(slug_matches) == 0 or (
                len(slug_matches) == 1 and slug_matches[0].id == self.id
            ):
                self.slug = new_slug
            else:
                self.slug = "%s-%s" % (new_slug, self.id)
        super().save(*args, **kwargs)  # Call the "real" save() method.

    def get_absolute_url(self):
        return reverse("show-org", kwargs={"org_slug": self.slug})

    def __str__(self):
        return u"%s" % (self.name)


class OrgTeamRequest(models.Model):
    ORG = 0
    TEAM = 1
    ORIGINS = [(ORG, _("Organization")), (TEAM, _("Team"))]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    team = models.ForeignKey("Team", on_delete=models.CASCADE)
    request_origin = models.SmallIntegerField(
        _("Request from"), choices=ORIGINS, default=ORG, db_index=True
    )
    request_key = models.UUIDField(default=uuid.uuid4, editable=True)

    requested_by = models.ForeignKey(
        UserProfile,
        related_name="requested_org_memberships",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    requested_date = models.DateTimeField(default=datetime.datetime.now)
    accepted_by = models.ForeignKey(
        UserProfile,
        related_name="accepted_org_memberships",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    joined_date = models.DateTimeField(null=True, blank=True)

    @property
    def origin_name(self):
        return OrgTeamRequest.ORIGINS[self.request_origin][1]

    @property
    def can_resend(self):
        return self.requested_date.replace(tzinfo=None) < (
            datetime.datetime.now() - datetime.timedelta(days=1)
        )

    def __str__(self):
        return "%s in %s" % (self.team, self.organization)


class Sponsor(models.Model):
    name = models.CharField(_("Sponsor Name"), max_length=256, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    web_url = models.URLField(_("Website"), null=True, blank=True)
    logo = ProcessedImageField(
        verbose_name=_("Logo"),
        help_text=_("Will be scaled and cropped to max 250x200 px."),
        upload_to="sponsors",
        processors=[ResizeToFit(250, 200)],
        format="PNG",
        blank=False,
    )

    def __str__(self):
        return self.name


class SponsorSerializer(serializers.ModelSerializer):
    display = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = Sponsor
        fields = ("id", "name", "logo", "web_url")


class PublicTeamsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(access=Team.PUBLIC)


class Team(models.Model):
    PUBLIC = 0
    PERSONAL = 1
    PRIVATE = 2
    TYPES = [(PUBLIC, _("Public")), (PERSONAL, _("Personal")), (PRIVATE, _("Private"))]
    name = models.CharField(_("Team Name"), max_length=256, null=False, blank=False)
    slug = models.CharField(max_length=256, null=False, blank=False, unique=True)
    organization = models.ForeignKey(
        Organization,
        related_name="teams",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    access = models.SmallIntegerField(
        verbose_name=_("Access"), choices=TYPES, default=PUBLIC
    )

    cover_img = models.ImageField(
        verbose_name=_("Cover Image"), upload_to="team_covers", null=True, blank=True
    )
    tile_img = ImageSpecField(
        source="cover_img",
        processors=[Adjust(contrast=0.8, color=1), ResizeToFill(338, 200)],
        format="PNG",
    )

    banner_img = ImageSpecField(
        source="cover_img",
        processors=[Adjust(contrast=0.8, color=1), ResizeToFill(825, 200)],
        format="PNG",
    )

    description = models.TextField(blank=True, null=True)

    about_page = models.TextField(blank=True, null=True)

    country = models.ForeignKey(
        Country, null=True, blank=True, on_delete=models.CASCADE
    )
    spr = models.ForeignKey(SPR, null=True, blank=True, on_delete=models.CASCADE)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)

    web_url = models.URLField(_("Website"), null=True, blank=True)
    email = models.EmailField(_("Email Address"), null=True, blank=True)

    created_date = models.DateField(
        _("Date Created"), default=timezone.now, null=True, blank=True
    )

    owner_profile = models.ForeignKey(
        UserProfile, related_name="owned_teams", null=True, on_delete=models.CASCADE
    )
    admin_profiles = models.ManyToManyField(
        UserProfile, related_name="admins", blank=True
    )
    contact_profiles = models.ManyToManyField(
        UserProfile, related_name="contacts", blank=True
    )

    languages = models.ManyToManyField(Language, blank=True)
    active = models.BooleanField(_("Active Team"), default=True)
    tz = models.CharField(
        max_length=32,
        verbose_name=_("Default Timezone"),
        default="UTC",
        choices=location.TimezoneChoices(),
        blank=False,
        null=False,
        help_text=_("The most commonly used timezone for this Team."),
    )

    members = models.ManyToManyField(
        UserProfile, through="Member", related_name="memberships", blank=True
    )

    category = models.ForeignKey(
        "Category", on_delete=models.SET_NULL, blank=True, null=True
    )
    topics = models.ManyToManyField("Topic", blank=True)

    sponsors = models.ManyToManyField("Sponsor", related_name="teams", blank=True)

    objects = models.Manager()
    public_objects = PublicTeamsManager()

    @property
    def card_img_url(self):
        if self.tile_img is not None and self.tile_img.name is not None:
            return self.tile_img.url
        elif (
            self.organization
            and self.organization.tile_img
            and self.organization.tile_img.url is not None
        ):
            return self.organization.tile_img.url
        elif self.category is not None:
            return self.category.img_url
        else:
            return static("img/team_placeholder.png")

    @property
    def full_img_url(self):
        if self.card_img_url.startswith("http"):
            return self.card_img_url
        else:
            site = Site.objects.get(id=1)
            return "https://%s%s" % (site.domain, self.card_img_url)

    @property
    def location_name(self):
        if self.city:
            return str(self.city)
        elif self.spr:
            return str(self.spr)
        elif self.country:
            return str(self.country)
        else:
            return ""

    @property
    def latitude(self):
        if self.city:
            return self.city.latitude
        return None

    @property
    def longitude(self):
        if self.city:
            return self.city.longitude
        return None

    @property
    def administrators(self):
        return [
            member.user
            for member in Member.objects.filter(team=self, role=Member.ADMIN)
        ]

    @property
    def moderators(self):
        return [
            member.user
            for member in Member.objects.filter(
                team=self, role__in=(Member.ADMIN, Member.MODERATOR)
            )
        ]

    def get_absolute_url(self):
        return reverse("show-team", kwargs={"team_id": self.id})

    def __str__(self):
        return u"%s" % (self.name)

    def save(self, *args, **kwargs):
        if self.city is not None:
            self.spr = self.city.spr
            self.country = self.spr.country
        if self.slug is None or len(self.slug) < 1:
            new_slug = slugify(self.name)
        else:
            new_slug = self.slug
        slug_matches = list(Team.objects.filter(slug=new_slug))
        if len(slug_matches) == 0 or (
            len(slug_matches) == 1 and slug_matches[0].id == self.id
        ):
            self.slug = new_slug
        else:
            self.slug = "%s-%s" % (new_slug, self.id)
        super().save(*args, **kwargs)  # Call the "real" save() method.

    def get_absolute_url(self):
        return reverse("show-team-by-slug", kwargs={"team_slug": self.slug})


class TeamSerializer(serializers.ModelSerializer):
    web_url = serializers.CharField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Team
        fields = ("id", "name", "slug", "latitude", "longitude", "web_url")


class Member(models.Model):
    NORMAL = 0
    MODERATOR = 1
    ADMIN = 2
    ROLES = [
        (NORMAL, _("Normal")),
        (MODERATOR, _("Moderator")),
        (ADMIN, _("Administrator")),
    ]
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    role = models.SmallIntegerField(
        _("Member Role"), choices=ROLES, default=NORMAL, db_index=True
    )
    joined_date = models.DateTimeField(default=datetime.datetime.now)

    @property
    def role_name(self):
        return Member.ROLES[self.role][1]

    def __str__(self):
        return "%s in %s" % (self.user, self.team)


class Category(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()
    slug = models.CharField(max_length=256, blank=True)
    img_url = models.URLField(blank=False, null=False)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Topic(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=False, blank=False
    )
    name = models.CharField(max_length=256)
    slug = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
