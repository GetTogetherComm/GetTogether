from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from events.models.profiles import Team, UserProfile, Member
from events.forms import UserForm, UserProfileForm

from events.models.events import Event, Place, Attendee

import datetime
import simplejson

from .teams import *
from .events import *

def logout(request):
    if request.user.is_authenticated:
        logout_user(request)
    return redirect('home')

def login(request):
    if request.user.is_authenticated:
        messages.add_message(request, messages.INFO, message=_('You are already logged in.'))
        return redirect('home')
    return render(request, 'get_together/users/login.html')


def show_profile(request, user_id):
    user = get_object_or_404(UserProfile, id=user_id)

    teams = user.memberships.all()

    context = {
            'user': user,
            'teams': teams,
    }

    return render(request, 'get_together/users/show_profile.html', context)


def edit_profile(request):
    if not request.user.is_authenticated:
        messages.add_message(request, messages.WARNING, message=_('You must be logged in to edit your profile.'))
        return redirect('login')

    user = request.user
    profile = request.user.profile
    account = request.user.account

    if request.method == 'GET':
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

        context = {
            'user': user,
            'profile': profile,
            'user_form': user_form,
            'profile_form': profile_form,
        }
        return render(request, 'get_together/users/edit_profile.html', context)
    elif request.method == 'POST':
        old_email = request.user.email
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save()
            if user.email != old_email:
                if user.email is None or user.email == "":
                    messages.add_message(request, messages.ERROR, message=_('Your email address has been removed.'))
                    account.is_email_confirmed = False
                    account.save()
                else:
                    messages.add_message(request, messages.WARNING, message=_('Your email address has changed, please confirm your new address.'))
                    return redirect('send-confirm-email')
            return redirect('show-profile', profile.id)
        else:
            context = {
            'user_form': user_form,
            'profile_form': profile_form,
            }
            return render(request, 'get_together/users/edit_profile.html', context)
    else:
     return redirect('home')

