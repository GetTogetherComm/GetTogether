import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.translation import ugettext_lazy as _

import simplejson

from accounts.models import EmailRecord
from events import location
from events.forms import (
    AcceptInviteToJoinTeamForm,
    AcceptRequestToJoinTeamForm,
    DeleteTeamForm,
    NewTeamForm,
    TeamContactForm,
    TeamForm,
    TeamInviteForm,
)
from events.models.events import (
    Attendee,
    CommonEvent,
    Event,
    EventSeries,
    Place,
    delete_event_searchable,
    update_event_searchable,
)
from events.models.profiles import (
    Member,
    Organization,
    Team,
    TeamMembershipRequest,
    UserProfile,
)
from events.utils import slugify, verify_csrf


# Create your views here.
def teams_list(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("all-teams")

    teams = request.user.profile.memberships.all().select_related("city").distinct()
    try:
        geo_ip = location.get_geoip(request)
        context = {
            "active": "my",
            "teams": sorted(
                teams, key=lambda team: location.team_distance_from(geo_ip.latlng, team)
            ),
        }
    except:
        context = {"active": "my", "teams": teams}
    return render(request, "get_together/teams/list_teams.html", context)


def teams_list_all(request, *args, **kwargs):
    if request.user.is_authenticated:
        teams = Team.objects.filter(
            Q(access=Team.PUBLIC)
            | Q(access=Team.PRIVATE, member__user=request.user.profile)
        )
    else:
        teams = Team.objects.filter(access=Team.PUBLIC)
    teams = teams.select_related("city")

    try:
        geo_ip = location.get_geoip(request)
        context = {
            "active": "all",
            "teams": sorted(
                teams, key=lambda team: location.team_distance_from(geo_ip.latlng, team)
            ),
        }
    except:
        context = {"active": "all", "teams": teams}
    return render(request, "get_together/teams/list_teams.html", context)


def show_team_by_slug(request, team_slug):
    team = get_object_or_404(Team, slug=team_slug)
    if team.access == Team.PERSONAL:
        return redirect("show-profile", team.owner_profile.id)
    if team.access == Team.PRIVATE and not request.user.profile.is_in_team(team):
        raise Http404()
    return show_team(request, team)


def show_team_by_id(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    return redirect("show-team-by-slug", team_slug=team.slug)


def show_team(request, team):
    if team.access == Team.PRIVATE and not request.user.profile.is_in_team(team):
        raise Http404()
    upcoming_events = Event.objects.filter(
        team=team, end_time__gt=datetime.datetime.now()
    ).order_by("start_time")
    recent_events = Event.objects.filter(
        team=team, end_time__lte=datetime.datetime.now()
    ).order_by("-start_time")[:3]
    context = {
        "team": team,
        "upcoming_events": upcoming_events,
        "recent_events": recent_events,
        "is_member": request.user.profile in team.members.all(),
        "member_list": Member.objects.filter(team=team).order_by(
            "-role", "joined_date"
        ),
        "can_create_event": request.user.profile.can_create_event(team),
        "can_edit_team": request.user.profile.can_edit_team(team),
    }
    return render(request, "get_together/teams/show_team.html", context)


def show_team_events_by_slug(request, team_slug):
    team = get_object_or_404(Team, slug=team_slug)
    if team.access == Team.PRIVATE and not request.user.profile.is_in_team(team):
        raise Http404()
    upcoming_events = Event.objects.filter(
        team=team, end_time__gt=datetime.datetime.now()
    ).order_by("start_time")
    recent_events = Event.objects.filter(
        team=team, end_time__lte=datetime.datetime.now()
    ).order_by("-start_time")
    recurring_events = EventSeries.objects.filter(team=team)

    context = {
        "team": team,
        "upcoming_events": upcoming_events,
        "recent_events": recent_events,
        "recurring_events": recurring_events,
        "is_member": request.user.profile in team.members.all(),
        "member_list": Member.objects.filter(team=team).order_by(
            "-role", "joined_date"
        ),
        "can_create_event": request.user.profile.can_create_event(team),
        "can_edit_team": request.user.profile.can_edit_team(team),
    }
    return render(request, "get_together/teams/team_events.html", context)


def show_team_about_by_slug(request, team_slug):
    team = get_object_or_404(Team, slug=team_slug)
    if team.access == Team.PRIVATE and not request.user.profile.is_in_team(team):
        raise Http404()
    if team.about_page:
        return show_team_about(request, team)
    else:
        return redirect("show-team-by-slug", team_slug=team.slug)


def show_team_about(request, team):
    context = {
        "team": team,
        "is_member": request.user.profile in team.members.all(),
        "member_list": Member.objects.filter(team=team).order_by(
            "-role", "joined_date"
        ),
        "can_create_event": request.user.profile.can_create_event(team),
        "can_edit_team": request.user.profile.can_edit_team(team),
    }
    return render(request, "get_together/teams/about_team.html", context)


@login_required
def create_team(request, *args, **kwargs):
    if request.method == "GET":
        form = NewTeamForm()

        context = {"team_form": form}
        return render(request, "get_together/teams/create_team.html", context)
    elif request.method == "POST":
        form = NewTeamForm(request.POST, request.FILES)
        if form.is_valid():
            new_team = form.save()
            new_team.owner_profile = request.user.profile
            new_team.save()
            Member.objects.create(
                team=new_team, user=request.user.profile, role=Member.ADMIN
            )
            return redirect("show-team-by-slug", team_slug=new_team.slug)
        else:
            context = {"team_form": form}
            return render(request, "get_together/teams/create_team.html", context)
    else:
        return redirect("home")


@login_required
def edit_team(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if not request.user.profile.can_edit_team(team):
        messages.add_message(
            request,
            messages.WARNING,
            message=_("You can not make changes to this team."),
        )
        return redirect("show-team-by-slug", team_slug=team.slug)

    if request.method == "GET":
        form = TeamForm(instance=team)

        context = {"team": team, "team_form": form}
        return render(request, "get_together/teams/edit_team.html", context)
    elif request.method == "POST":
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            new_team = form.save()
            new_team.owner_profile = request.user.profile
            new_team.save()
            return redirect("show-team-by-slug", team_slug=new_team.slug)
        else:
            context = {"team": team, "team_form": form}
            return render(request, "get_together/teams/edit_team.html", context)
    else:
        return redirect("home")


@login_required
def delete_team(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if not request.user.profile.can_edit_team(team):
        messages.add_message(
            request,
            messages.WARNING,
            message=_("You can not make changes to this team."),
        )
        return redirect("show-team-by-slug", team.slug)

    if request.method == "GET":
        form = DeleteTeamForm()

        context = {"team": team, "delete_form": form}
        return render(request, "get_together/teams/delete_team.html", context)
    elif request.method == "POST":
        form = DeleteTeamForm(request.POST)
        if form.is_valid() and form.cleaned_data["confirm"]:
            team.delete()
            return redirect("teams")
        else:
            context = {"team": team, "delete_form": form}
            return render(request, "get_together/teams/delete_team.html", context)
    else:
        return redirect("home")


@login_required
def manage_members(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if not request.user.profile.can_edit_team(team):
        messages.add_message(
            request,
            messages.WARNING,
            message=_("You can not manage this team's members."),
        )
        return redirect("show-team-by-slug", team.slug)

    members = Member.objects.filter(team=team).order_by("-role", "user__realname")
    member_choices = [
        (member.id, member.user)
        for member in members
        if member.user.user.account.is_email_confirmed
    ]
    default_choices = [
        ("all", _("All Members (%s)" % len(member_choices))),
        ("admins", _("Only Administrators")),
    ]
    if request.method == "POST":
        contact_form = TeamContactForm(request.POST)
        contact_form.fields["to"].choices = default_choices + member_choices
        if contact_form.is_valid():
            to = contact_form.cleaned_data["to"]
            body = contact_form.cleaned_data["body"]
            if to is not "admins" and not request.user.profile.can_edit_team(team):
                messages.add_message(
                    request,
                    messages.WARNING,
                    message=_("You can not contact this team's members."),
                )
                return redirect("show-team-by-slug", team.slug)
            if to == "all":
                count = 0
                for member in Member.objects.filter(team=team):
                    if member.user.user.account.is_email_confirmed:
                        contact_member(member, body, request.user.profile)
                        count += 1
                messages.add_message(
                    request, messages.SUCCESS, message=_("Emailed %s users" % count)
                )
            elif to == "admins":
                count = 0
                for member in Member.objects.filter(team=team, role=Member.ADMIN):
                    if member.user.user.account.is_email_confirmed:
                        contact_member(member, body, request.user.profile)
                        count += 1
                messages.add_message(
                    request, messages.SUCCESS, message=_("Emailed %s users" % count)
                )
            else:
                try:
                    member = Member.objects.get(id=to)
                    contact_member(member, body, request.user.profile)
                    messages.add_message(
                        request, messages.SUCCESS, message=_("Emailed %s" % member.user)
                    )
                except Member.DoesNotExist:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        message=_("Error sending message: Unknown user (%s)" % to),
                    )
                    pass
            return redirect("manage-members", team_id)
        else:
            messages.add_message(
                request,
                messages.ERROR,
                message=_("Error sending message: %s" % contact_form.errors),
            )
    else:
        contact_form = TeamContactForm()
        contact_form.fields["to"].choices = default_choices + member_choices

    invites = TeamMembershipRequest.objects.filter(team=team, joined_date__isnull=True)
    context = {
        "team": team,
        "members": members,
        "invites": invites,
        "contact_form": contact_form,
        "can_edit_team": request.user.profile.can_edit_team(team),
    }
    return render(request, "get_together/teams/manage_members.html", context)


@login_required
def invite_members(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if not request.user.profile.can_edit_team(team):
        messages.add_message(
            request,
            messages.WARNING,
            message=_("You can not manage this team's members."),
        )
        return redirect("manage-members", team_id)
    if not request.user.account.is_email_confirmed:
        messages.add_message(
            request,
            messages.WARNING,
            message=_(
                "You must confirm your own email address before you can invite others."
            ),
        )
        return redirect("edit-profile")

    if request.method == "POST":
        invite_form = TeamInviteForm(request.POST)
        if invite_form.is_valid():
            to = invite_form.cleaned_data["to"]
            remaining_emails = request.user.account.remaining_emails_allowed()
            if remaining_emails <= 0:
                messages.add_message(
                    request,
                    messages.WARNING,
                    message=_(
                        "You have exceeded the %s email messages you are allowed to send in one day. Please try again tomorrow."
                        % settings.ALLOWED_EMAILS_PER_DAY
                    ),
                )
                return redirect("invite-members", team_id=team_id)
            if len(to) > remaining_emails:
                messages.add_message(
                    request,
                    messages.WARNING,
                    message=_(
                        "You can only send %s more email messages today. Please choose fewer recipients or try again tomorrow."
                        % remaining_emails
                    ),
                )
                return redirect("invite-members", team_id=team_id)
            for email in to:
                invitation = TeamMembershipRequest.objects.create(
                    invite_email=email,
                    team=team,
                    request_origin=TeamMembershipRequest.TEAM,
                    requested_by=request.user.profile,
                )
                invite_member(invitation)

            messages.add_message(
                request, messages.SUCCESS, message=_("Sent %s invites" % len(to))
            )
            return redirect("manage-members", team_id)

    else:
        invite_form = TeamInviteForm()

    context = {
        "team": team,
        "invite_form": invite_form,
        "can_edit_team": request.user.profile.can_edit_team(team),
    }
    return render(request, "get_together/teams/invite_members.html", context)


def invite_member(invitation):
    email = invitation.invite_email
    team = invitation.team
    sender = invitation.requested_by
    context = {
        "sender": sender,
        "team": team,
        "invite_key": invitation.request_key,
        "site": Site.objects.get(id=1),
    }
    email_subject = "Invitation to join: %s" % team
    email_body_text = render_to_string(
        "get_together/emails/teams/member_invite.txt", context
    )
    email_body_html = render_to_string(
        "get_together/emails/teams/member_invite.html", context
    )
    email_recipients = [email]
    email_from = getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@gettogether.community"
    )

    success = send_mail(
        from_email=email_from,
        html_message=email_body_html,
        message=email_body_text,
        recipient_list=email_recipients,
        subject=email_subject,
        fail_silently=True,
    )

    EmailRecord.objects.create(
        sender=sender.user,
        recipient=None,
        email=email,
        subject=email_subject,
        body=email_body_text,
        ok=success,
    )


@login_required
@verify_csrf(token_key="csrftoken")
def resend_member_invite(request, invite_id):
    invite = get_object_or_404(TeamMembershipRequest, id=invite_id)
    invite_member(invite)
    invite.requested_date = datetime.datetime.now()
    invite.save()
    messages.add_message(
        request, messages.SUCCESS, message=_("Your request has been resent.")
    )
    return redirect("manage-members", team_id=invite.team.id)


@login_required
def confirm_request_to_join_team(request, invite_key):
    invite = get_object_or_404(TeamMembershipRequest, request_key=invite_key)
    if invite.accepted_by is not None:
        messages.add_message(
            request, messages.WARNING, message=_("Invalid team membership request.")
        )
        return redirect("home")

    if invite.request_origin == invite.TEAM:
        return accept_invite_to_join_team(request, invite)
    else:
        return accept_request_to_join_team(request, invite)


@login_required
def accept_invite_to_join_team(request, invite):
    if request.user.profile.is_in_team(invite.team):
        messages.add_message(
            request, messages.INFO, message=_("You are already a member of this team.")
        )
        return redirect("show-team-by-slug", team_slug=invite.team.slug)

    if request.method == "GET":
        form = AcceptInviteToJoinTeamForm()

        context = {"invite": invite, "team": invite.team, "invite_form": form}
        return render(request, "get_together/teams/accept_invite.html", context)
    elif request.method == "POST":
        form = AcceptInviteToJoinTeamForm(request.POST)
        if form.is_valid() and form.cleaned_data["confirm"]:
            invite.accepted_by = request.user.profile
            invite.joined_date = datetime.datetime.now()
            invite.save()
            new_member = Member.objects.create(
                team=invite.team, user=request.user.profile, role=Member.NORMAL
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                message=_("You have been added to %s." % invite.team.name),
            )
            return redirect("show-team-by-slug", team_slug=invite.team.slug)
        else:
            context = {"invite": invite, "team": req.team, "invite_form": form}
            return render(request, "get_together/teams/accept_invite.html", context)
    else:
        return redirect("home")


@login_required
def accept_request_to_join_team(request, invite):
    if not request.user.profile.can_edit_team(invite.team):
        messages.add_message(
            request,
            messages.WARNING,
            message=_("You do not have permission to accept new members to this team."),
        )
        return redirect("show-team-by-slug", team_slug=invite.team.slug)

    if request.method == "GET":
        form = AcceptRequestToJoinTeamForm()

        context = {"invite": invite, "team": invite.team, "request_form": form}
        return render(request, "get_together/teams/accept_request.html", context)
    elif request.method == "POST":
        form = AcceptRequestToJoinTeamForm(request.POST)
        if form.is_valid() and form.cleaned_data["confirm"]:
            invite.accepted_by = request.user.profile
            invite.joined_date = datetime.datetime.now()
            invite.save()
            new_member = Member.objects.create(
                team=invite.team, user=request.user.profile, role=Member.NORMAL
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                message=_("%s has been added to your team." % invite.user),
            )
            return redirect("manage-members", team_id=invite.team.id)
        else:
            context = {"invite": invite, "team": invite.team, "request_form": form}
            return render(request, "get_together/teams/accept_request.html", context)
    else:
        return redirect("home")


def contact_member(member, body, sender):
    context = {
        "sender": sender,
        "team": member.team,
        "body": body,
        "site": Site.objects.get(id=1),
    }
    email_subject = "A message from: %s" % member.team
    email_body_text = render_to_string(
        "get_together/emails/teams/member_contact.txt", context
    )
    email_body_html = render_to_string(
        "get_together/emails/teams/member_contact.html", context
    )
    email_recipients = [member.user.user.email]
    email_from = getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@gettogether.community"
    )

    success = send_mail(
        from_email=email_from,
        html_message=email_body_html,
        message=email_body_text,
        recipient_list=email_recipients,
        subject=email_subject,
        fail_silently=True,
    )
    EmailRecord.objects.create(
        sender=sender.user,
        recipient=member.user.user,
        email=member.user.user.email,
        subject=email_subject,
        body=email_body_text,
        ok=success,
    )


@verify_csrf(token_key="csrftoken")
def change_member_role(request, team_id, profile_id):
    membership = get_object_or_404(Member, team__id=team_id, user__id=profile_id)

    if not request.user.profile.can_edit_team(membership.team):
        messages.add_message(
            request,
            messages.WARNING,
            message=_("You can not change member roles for this team."),
        )
        return redirect(event.get_absolute_url())

    if request.GET.get("role", None) == "admin":
        membership.role = Member.ADMIN
    elif request.GET.get("role", None) == "moderator":
        membership.role = Member.MODERATOR
    elif request.GET.get("role", None) == "normal":
        membership.role = Member.NORMAL
    membership.save()

    return redirect("manage-members", team_id=membership.team.id)
