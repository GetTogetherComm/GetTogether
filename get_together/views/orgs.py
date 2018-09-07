from django.utils.translation import ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings


from events.models.profiles import Organization, Team, UserProfile, Member, OrgTeamRequest
from events.models.events import Event, CommonEvent, Place, Attendee
from events.forms import OrganizationForm, CommonEventForm, RequestToJoinOrgForm, InviteToJoinOrgForm, AcceptRequestToJoinOrgForm, AcceptInviteToJoinOrgForm
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
    total_members = UserProfile.objects.filter(member__team__organization=org).distinct().count()
    total_events= Event.objects.filter(team__organization=org).distinct().count()

    context = {
        'org': org,
        'upcoming_events': upcoming_events,
        'recent_events': recent_events,
        'member_list': Team.objects.filter(organization=org).order_by('name'),
        'can_create_event': request.user.profile.can_create_common_event(org),
        'can_edit_org': request.user.profile.can_edit_org(org),
        'member_count': total_members,
        'event_count': total_events,
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


@login_required
def request_to_join_org(request, org_slug):
    org = get_object_or_404(Organization, slug=org_slug)
    if not len(request.user.profile.administering) > 0:
        messages.add_message(request, messages.WARNING, message=_('You are not the administrator for any teams.'))
        return redirect('show-org', org_slug=org.slug)

    req = OrgTeamRequest(organization=org, request_origin=OrgTeamRequest.TEAM, requested_by=request.user.profile)
    if request.method == 'GET':
        form = RequestToJoinOrgForm(instance=req)
        form.fields['team'].queryset = Team.objects.filter(member__user=request.user.profile, member__role=Member.ADMIN).order_by('name')

        context = {
            'org': org,
            'request_form': form,
        }
        return render(request, 'get_together/orgs/request_to_join.html', context)
    elif request.method == 'POST':
        form = RequestToJoinOrgForm(request.POST, instance=req)
        form.fields['team'].queryset = Team.objects.filter(member__user=request.user.profile, member__role=Member.ADMIN).order_by('name')
        if form.is_valid():
            req = form.save()
            send_org_request(req)
            messages.add_message(request, messages.SUCCESS, message=_('Your request has been send to the organization administrators.'))
            return redirect('show-org', org_slug=org.slug)
        else:
            context = {
                'org': org,
                'request_form': form,
            }
            return render(request, 'get_together/orgs/request_to_join.html', context)
    else:
     return redirect('home')


def send_org_request(req):
    context = {
        'sender': req.requested_by,
        'req': req,
        'org': req.organization,
        'team': req.team,
        'site': Site.objects.get(id=1),
    }
    email_subject = 'Request to join: %s' % req.team.name
    email_body_text = render_to_string('get_together/emails/orgs/request_to_org.txt', context)
    email_body_html = render_to_string('get_together/emails/orgs/request_to_org.html', context)
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

    admin = req.organization.owner_profile
    success = send_mail(
        from_email=email_from,
        html_message=email_body_html,
        message=email_body_text,
        recipient_list=[admin.user.email],
        subject=email_subject,
        fail_silently=True,
    )
    EmailRecord.objects.create(
        sender=req.requested_by.user,
        recipient=admin.user,
        email=admin.user.email,
        subject=email_subject,
        body=email_body_text,
        ok=success
    )


@login_required
def invite_to_join_org(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if not request.user.profile.owned_orgs.count() > 0:
        messages.add_message(request, messages.WARNING, message=_('You are not the administrator for any organizations.'))
        return redirect('show-team', team_id=team_id)

    invite = OrgTeamRequest(team=team, request_origin=OrgTeamRequest.ORG, requested_by=request.user.profile)
    if request.method == 'GET':
        form = InviteToJoinOrgForm(instance=invite)
        form.fields['organization'].queryset = Organization.objects.filter(owner_profile=request.user.profile).order_by('name')

        context = {
            'team': team,
            'invite_form': form,
        }
        return render(request, 'get_together/orgs/invite_to_join.html', context)
    elif request.method == 'POST':
        form = InviteToJoinOrgForm(request.POST, instance=invite)
        if form.is_valid():
            invite = form.save()
            send_org_invite(invite)
            messages.add_message(request, messages.SUCCESS, message=_('Your request has been send to the team administrators.'))
            return redirect('show-team', team_id=team_id)
        else:
            context = {
                'team': team,
                'invite_form': form,
            }
            return render(request, 'get_together/orgs/invite_to_join.html', context)
    else:
     return redirect('home')


def send_org_invite(req):
    context = {
        'sender': req.requested_by,
        'req': req,
        'org': req.organization,
        'team': req.team,
        'site': Site.objects.get(id=1),
    }
    email_subject = 'Invitation to join: %s' % req.organization.name
    email_body_text = render_to_string('get_together/emails/orgs/invite_to_org.txt', context)
    email_body_html = render_to_string('get_together/emails/orgs/invite_to_org.html', context)
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

    for admin in Member.objects.filter(team=req.team, role=Member.ADMIN, user__user__account__is_email_confirmed=True):
        success = send_mail(
            from_email=email_from,
            html_message=email_body_html,
            message=email_body_text,
            recipient_list=[admin.user.user.email],
            subject=email_subject,
            fail_silently=True,
        )
        EmailRecord.objects.create(
            sender=req.requested_by.user,
            recipient=admin.user.user,
            email=admin.user.user.email,
            subject=email_subject,
            body=email_body_text,
            ok=success
        )


@login_required
def confirm_request_to_join_org(request, request_key):
    req = get_object_or_404(OrgTeamRequest, request_key=request_key)
    if req.request_origin == req.ORG:
        return accept_invite_to_join_org(request, req)
    else:
        return accept_request_to_join_org(request, req)

@login_required
def accept_request_to_join_org(request, req):
    if not request.user.profile.can_edit_org(req.organization):
        messages.add_message(request, messages.WARNING, message=_('You do not have permission to accept new teams to this organization.'))
        return redirect('show-org', org_slug=req.organization.slug)

    if request.method == 'GET':
        form = AcceptRequestToJoinOrgForm()

        context = {
            'invite': req,
            'org': req.organization,
            'team': req.team,
            'request_form': form,
        }
        return render(request, 'get_together/orgs/accept_request.html', context)
    elif request.method == 'POST':
        form = AcceptRequestToJoinOrgForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            req.accepted_by = request.user.profile
            req.joined_date = datetime.datetime.now()
            req.save()
            req.team.organization = req.organization
            req.team.save()
            messages.add_message(request, messages.SUCCESS, message=_('%s has been added to your organization.' % req.team.name))
            return redirect('show-org', org_slug=req.organization.slug)
        else:
            context = {
                'invite': req,
                'org': req.organization,
                'team': req.team,
                'request_form': form,
            }
            return render(request, 'get_together/orgs/accept_request.html', context)
    else:
     return redirect('home')

@login_required
def accept_invite_to_join_org(request, req):
    if not request.user.profile.can_edit_team(req.team):
        messages.add_message(request, messages.WARNING, message=_('You do not have permission to add this team to an orgnization.'))
        return redirect('show-team-by-slug', team_slug=req.team.slug)

    if request.method == 'GET':
        form = AcceptInviteToJoinOrgForm()

        context = {
            'invite': req,
            'org': req.organization,
            'team': req.team,
            'invite_form': form,
        }
        return render(request, 'get_together/orgs/accept_invite.html', context)
    elif request.method == 'POST':
        form = AcceptInviteToJoinOrgForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            req.accepted_by = request.user.profile
            req.joined_date = datetime.datetime.now()
            req.save()
            req.team.organization = req.organization
            req.team.save()
            messages.add_message(request, messages.SUCCESS, message=_('You team has been added to %s.' % req.organization.name))
            return redirect('show-team-by-slug', team_slug=req.team.slug)
        else:
            context = {
                'invite': req,
                'org': req.organization,
                'team': req.team,
                'invite_form': form,
            }
            return render(request, 'get_together/orgs/accept_invite.html', context)
    else:
     return redirect('home')


def show_common_event(request, event_id, event_slug):
    event = get_object_or_404(CommonEvent, id=event_id)
    context = {
        'org': event.organization,
        'common_event': event,
        'participating_events': event.participating_events.all().order_by('start_time'),
        'can_edit_event': request.user.profile.can_create_common_event(event.organization),
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
        form = CommonEventForm(instance=new_event)

        context = {
            'org': org,
            'event_form': form,
        }
        return render(request, 'get_together/orgs/create_common_event.html', context)
    elif request.method == 'POST':
        form = CommonEventForm(request.POST, instance=new_event)
        if form.is_valid:
            new_event = form.save()
            send_common_event_invite(new_event)
            return redirect('show-common-event', new_event.id, new_event.slug)
        else:
            context = {
                'org': org,
                'event_form': form,
            }
            return render(request, 'get_together/orgs/create_common_event.html', context)
    else:
     return redirect('home')


def send_common_event_invite(event):
    context = {
        'sender': event.created_by,
        'org': event.organization,
        'event': event,
        'site': Site.objects.get(id=1),
    }
    email_subject = 'Participate in our event: %s' % event.name
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

    teams = event.organization.teams.all()
    if event.city:
        teams = teams.filter(city=event.city)
    elif event.spr:
        teams = teams.filter(city__spr=event.spr)
    elif event.country:
        teams = teams.filter(city__spr__country=event.country)

    for admin in Member.objects.filter(team__in=teams, role=Member.ADMIN, user__user__account__is_email_confirmed=True):
        context['team'] = admin.team
        email_body_text = render_to_string('get_together/emails/orgs/invite_to_common_event.txt', context)
        email_body_html = render_to_string('get_together/emails/orgs/invite_to_common_event.html', context)
        success = send_mail(
            from_email=email_from,
            html_message=email_body_html,
            message=email_body_text,
            recipient_list=[admin.user.user.email],
            subject=email_subject,
            fail_silently=True,
        )
        EmailRecord.objects.create(
            sender=event.created_by.user,
            recipient=admin.user.user,
            email=admin.user.user.email,
            subject=email_subject,
            body=email_body_text,
            ok=success
        )


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


@login_required
def edit_common_event(request, event_id):
    event = get_object_or_404(CommonEvent, id=event_id)
    org = event.organization
    if not request.user.profile.can_create_common_event(org):
        messages.add_message(request, messages.WARNING, message=_('You can not edit events for this org.'))
        return redirect('show-org', org_id=org.pk)

    if request.method == 'GET':
        form = CommonEventForm(instance=event)

        context = {
            'org': org,
            'event': event,
            'event_form': form,
        }
        return render(request, 'get_together/orgs/edit_common_event.html', context)
    elif request.method == 'POST':
        form = CommonEventForm(request.POST, instance=event)
        if form.is_valid():
            new_event = form.save()
            return redirect('show-common-event', new_event.id, new_event.slug)
        else:
            context = {
                'org': org,
                'event': event,
                'event_form': form,
            }
            return render(request, 'get_together/orgs/edit_common_event.html', context)
    else:
     return redirect('home')


