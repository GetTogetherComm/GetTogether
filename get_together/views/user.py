from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from events.models.profiles import Team, UserProfile, Member
from events.forms import TeamForm, NewTeamForm, TeamEventForm, NewTeamEventForm, NewPlaceForm

from events.models.events import Event, Place, Attendee

import datetime
import simplejson

from .teams import *
from .events import *
