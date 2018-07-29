from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings


from events.models.profiles import Organization, Team, UserProfile, Member
from events.models.events import Event, CommonEvent, Place, Attendee
from events.forms import OrganizationForm, NewCommonEventForm
from events import location
from events.utils import slugify

from accounts.models import EmailRecord

import datetime
import simplejson


# Create your views here.
def show_org(request, org_slug):
    org = get_object_or_404(Organization, slug=org_slug)
    upcoming_events = CommonEvent.objects.filter(organization=org, end_time__gt=datetime.datetime.now()).order_by('start_time')
    recent_events = CommonEvent.objects.filter(organization=org, end_time__lte=datetime.datetime.now()).order_by('-start_time')[:5]
    context = {
        'org': org,
        'upcoming_events': upcoming_events,
        'recent_events': recent_events,
        'member_list': Team.objects.filter(organization=org).order_by('name'),
        'can_create_event': request.user.profile.can_create_common_event(org),
        'can_edit_org': request.user.profile.can_edit_org(org),
    }
    return render(request, 'get_together/orgs/show_org.html', context)


@login_required
def edit_org(request, org_slug):
    org = get_object_or_404(Organization, slug=org_slug)
    if not request.user.profile.can_edit_org(org):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this organization.'))
        return redirect('show-org', org_slug=org.slug)

    if request.method == 'GET':
        form = OrganizationForm(instance=org)

        context = {
            'org': org,
            'org_form': form,
        }
        return render(request, 'get_together/orgs/edit_org.html', context)
    elif request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=org)
        if form.is_valid():
            form.save()
            return redirect('show-org', org_slug=org.slug)
        else:
            context = {
                'org': org,
                'org_form': form,
            }
            return render(request, 'get_together/orgs/edit_org.html', context)
    else:
     return redirect('home')


def show_common_event(request, event_id, event_slug):
    event = get_object_or_404(CommonEvent, id=event_id)
    context = {
        'org': event.organization,
        'common_event': event,
        'participating_events': event.participating_events.all().order_by('start_time'),
        'can_edit_event': False,
    }
    return render(request, 'get_together/orgs/show_common_event.html', context)


@login_required
def create_common_event(request, org_slug):
    org = get_object_or_404(Organization, slug=org_slug)
    if not request.user.profile.can_create_common_event(org):
        messages.add_message(request, messages.WARNING, message=_('You can not create events for this org.'))
        return redirect('show-org', org_id=org.pk)

    new_event = CommonEvent(organization=org, created_by=request.user.profile)
    if request.method == 'GET':
        form = NewCommonEventForm(instance=new_event)

        context = {
            'org': org,
            'event_form': form,
        }
        return render(request, 'get_together/orgs/create_common_event.html', context)
    elif request.method == 'POST':
        form = NewCommonEventForm(request.POST, instance=new_event)
        if form.is_valid:
            new_event = form.save()
            return redirect('show-common-event', new_event.id, new_event.slug)
        else:
            context = {
                'org': org,
                'event_form': form,
            }
            return render(request, 'get_together/orgs/create_common_event.html', context)
    else:
     return redirect('home')


@login_required
def create_common_event_team_select(request, event_id):
    teams = request.user.profile.moderating
    if len(teams) == 1:
        return redirect(reverse('create-event', kwargs={'team_id':teams[0].id}) + '?common=%s'%event_id)
    context = {
        'common_event_id': event_id,
        'teams': teams
    }
    return render(request, 'get_together/orgs/create_common_event_team_select.html', context)

