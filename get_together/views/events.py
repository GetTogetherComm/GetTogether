from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.sites.models import Site
from django.utils import timezone
from django.utils.datastructures import OrderedSet
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings
from django.http import JsonResponse

from events.models.events import (
    Event,
    EventComment,
    CommonEvent,
    EventSeries,
    EventPhoto,
    Place,
    Attendee,
    update_event_searchable,
    delete_event_searchable,
)
from events.models.speakers import Speaker, Talk, SpeakerRequest, Presentation
from events.models.profiles import Team, Organization, UserProfile, Member, Sponsor
from events.forms import (
    TeamEventForm,
    NewTeamEventForm,
    DeleteEventForm,
    CancelEventForm,
    EventSeriesForm,
    DeleteEventSeriesForm,
    EventCommentForm,
    DeleteCommentForm,
    NewPlaceForm,
    UploadEventPhotoForm,
    RemoveEventPhotoForm,
    EventInviteEmailForm,
    EventInviteMemberForm,
    EventContactForm,
    SponsorForm,
    ChangeEventHostForm,
)
from events import location
from events.utils import verify_csrf

from accounts.models import EmailRecord

import simple_ga as ga

import datetime
import simplejson

# Create your views here.
def events_list(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect('all-events')
    events = Event.objects.filter(attendees=request.user.profile, end_time__gt=timezone.now(), status__gt=Event.CANCELED).order_by('start_time')
    geo_ip = location.get_geoip(request)
    context = {
        'active': 'my',
        'events_list': sorted(events, key=lambda event: location.event_distance_from(geo_ip.latlng, event)),
    }
    return render(request, 'get_together/events/list_events.html', context)

def events_list_all(request, *args, **kwargs):
    events = Event.objects.filter(end_time__gt=timezone.now()).order_by('start_time')
    geo_ip = location.get_geoip(request)
    context = {
        'active': 'all',
        'events_list': sorted(events, key=lambda event: location.event_distance_from(geo_ip.latlng, event)),
    }
    return render(request, 'get_together/events/list_events.html', context)

def show_event(request, event_id, event_slug):
    event = get_object_or_404(Event, id=event_id)
    comment_form = EventCommentForm()
    context = {
        'team': event.team,
        'event': event,
        'comment_form': comment_form,
        'sponsor_count': event.sponsors.count(),
        'sponsor_list': event.sponsors.all(),
        'is_attending': request.user.profile in event.attendees.all(),
        'attendee_list': Attendee.objects.filter(event=event).order_by('-role', '-status'),
        'attendee_count': Attendee.objects.filter(event=event, status=Attendee.YES).count(),
        'presentation_list': event.presentations.filter(status=Presentation.ACCEPTED).order_by('start_time'),
        'pending_presentations': event.presentations.filter(status=Presentation.PROPOSED).count(),
        'can_edit_event': request.user.profile.can_edit_event(event),
        'can_edit_team': request.user.profile.can_edit_team(event.team),
        'is_in_team': request.user.profile.is_in_team(event.team),
        'is_email_confirmed': request.user.account.is_email_confirmed,
    }
    return render(request, 'get_together/events/show_event.html', context)

def show_series(request, series_id, series_slug):
    series = get_object_or_404(EventSeries, id=series_id)
    context = {
        'team': series.team,
        'series': series,
        'instances': series.instances.all().order_by('-start_time'),
        'can_edit_event': request.user.profile.can_create_event(series.team),
    }
    return render(request, 'get_together/events/show_series.html', context)

@login_required
def create_event_team_select(request):
    teams = request.user.profile.moderating
    if len(teams) == 0:
        return redirect('create-team')
    if len(teams) == 1:
        return redirect('create-event', team_id=teams[0].id)

    return render(request, 'get_together/events/create_event_team_select.html', {'teams': teams})

@login_required
def create_event(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if not request.user.profile.can_create_event(team):
        messages.add_message(request, messages.WARNING, message=_('You can not create events for this team.'))
        return redirect('show-team-by-slug', team_slug=team.slug)

    new_event = Event(team=team, created_by=request.user.profile)


    if request.method == 'GET':
        initial = {}
        if 'common' in request.GET and request.GET['common'] != '':
            new_event.parent = CommonEvent.objects.get(id=request.GET['common'])
            initial['name'] = new_event.parent.name
            initial['summary'] = new_event.parent.summary
            initial['start_time'] = new_event.parent.start_time
            initial['end_time'] = new_event.parent.end_time
        form = NewTeamEventForm(instance=new_event, initial=initial)

        context = {
            'event': new_event,
            'team': team,
            'event_form': form,
        }
        return render(request, 'get_together/events/create_event.html', context)
    elif request.method == 'POST':
        if 'common' in request.POST and request.POST['common'] != '':
            new_event.parent = CommonEvent.objects.get(id=request.POST['common'])
        form = NewTeamEventForm(request.POST, instance=new_event)
        if form.is_valid:
            new_event = form.save()
            Attendee.objects.create(event=new_event, user=request.user.profile, role=Attendee.HOST, status=Attendee.YES)

            if form.cleaned_data.get('recurrences', None):
                new_series = EventSeries.from_event(new_event, recurrences=form.cleaned_data['recurrences'])
                new_series.save()
                new_event.series = new_series
                new_event.save()

            messages.add_message(request, messages.SUCCESS, message=_('Your event has been scheduled! Next, find a place for your event.'))
            ga.add_event(request, action='new_event', category='activity', label=new_event.get_full_url())

            return redirect('add-place', new_event.id)
        else:
            context = {
                'event': new_event,
                'team': team,
                'event_form': form,
            }
            return render(request, 'get_together/events/create_event.html', context)
    else:
     return redirect('home')


@login_required
def manage_event_sponsors(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not manage this event\'s sponsorss.'))
        return redirect(event.get_absolute_url())

    team_sponsors = list(event.team.sponsors.all())
    events_sponsors = list(Sponsor.objects.filter(events__team=event.team))

    if request.method == 'POST':
        sponsor_form = SponsorForm(request.POST, request.FILES)
        if sponsor_form.is_valid():
            new_sponsor = sponsor_form.save()
            event.sponsors.add(new_sponsor)
            event.team.sponsors.add(new_sponsor)
            messages.add_message(request, messages.SUCCESS, message=_('Your sponsor has been added to this event.'))
            return redirect('manage-event-sponsors', event.id)

    else:
        sponsor_form = SponsorForm()
    context = {
        'event': event,
        'sponsors': OrderedSet(events_sponsors + team_sponsors),
        'sponsor_form': sponsor_form,
        'can_edit_event': request.user.profile.can_edit_event(event),
    }
    return render(request, 'get_together/events/manage_event_sponsors.html', context)


@login_required
def sponsor_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    sponsor = get_object_or_404(Sponsor, id=request.GET.get('sponsor', None))
    if request.user.is_anonymous:
        return JsonResponse({'status': 'ERROR', 'message': _("You must be logged in manage event sponsors.")})

    if not request.user.profile.can_edit_event(event):
        return JsonResponse({'status': 'ERROR', 'message': _("You can not manage this event's sponsors.")})

    action = 'none'
    if request.GET.get('action', None) == 'add':
        if sponsor in event.sponsors.all():
            return JsonResponse({'status': 'ERROR', 'message': _("Already sponsoring this event.")})

        event.sponsors.add(sponsor)
        action = 'Added'
    if request.GET.get('action', None) == 'remove':
        if sponsor not in event.sponsors.all():
            return JsonResponse({'status': 'ERROR', 'message': _("Not sponsoring this event.")})

        event.sponsors.remove(sponsor)
        action = 'Removed'

    return JsonResponse({'status': 'OK', 'sponsor_id': sponsor.id, 'action': action})


@login_required
def manage_attendees(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not manage this event\'s attendees.'))
        return redirect(event.get_absolute_url())
    attendees = Attendee.objects.filter(event=event).order_by('-actual', '-status', 'user__realname')

    attendee_choices = [(attendee.id, attendee.user) for attendee in attendees if attendee.user.user.account.is_email_confirmed]
    default_choices = [('all', 'Everyone (%s)' % len(attendee_choices)), ('hosts', 'Only Hosts')]
    if event.is_over:
        default_choices.append(('attended', 'Only Attended'))
    else:
        default_choices.append(('attending', 'Only Attending'))

    if request.method == 'POST':
        contact_form = EventContactForm(request.POST)
        contact_form.fields['to'].choices = default_choices + attendee_choices
        if contact_form.is_valid():
            to = contact_form.cleaned_data['to']
            body = contact_form.cleaned_data['body']
            if to is not 'hosts' and not request.user.profile.can_edit_event(event):
                messages.add_message(request, messages.WARNING, message=_('You can not contact this events\'s attendees.'))
                return redirect(event.get_absolute_url())
            if to == 'all':
                count = 0
                for attendee in Attendee.objects.filter(event=event):
                    if attendee.user.user.account.is_email_confirmed:
                        contact_attendee(attendee, body, request.user.profile)
                        count += 1
                messages.add_message(request, messages.SUCCESS, message=_('Emailed %s attendees' % count))
            elif to == 'hosts':
                count = 0
                for attendee in Attendee.objects.filter(event=event, role=Attendee.HOST):
                    if attendee.user.user.account.is_email_confirmed:
                        contact_attendee(attendee, body, request.user.profile)
                        count += 1
                messages.add_message(request, messages.SUCCESS, message=_('Emailed %s attendees' % count))
            elif to == 'attending':
                count = 0
                for attendee in Attendee.objects.filter(event=event, status=Attendee.YES):
                    if attendee.user.user.account.is_email_confirmed:
                        contact_attendee(attendee, body, request.user.profile)
                        count += 1
                messages.add_message(request, messages.SUCCESS, message=_('Emailed %s attendees' % count))
            elif to == 'attended':
                count = 0
                for attendee in Attendee.objects.filter(event=event, actual=Attendee.YES):
                    if attendee.user.user.account.is_email_confirmed:
                        contact_attendee(attendee, body, request.user.profile)
                        count += 1
                messages.add_message(request, messages.SUCCESS, message=_('Emailed %s attendees' % count))
            else:
                try:
                    attendee = Attendee.objects.get(id=to)
                    contact_attendee(attendee, body, request.user.profile)
                    messages.add_message(request, messages.SUCCESS, message=_('Emailed %s' % attendee.user))
                except Member.DoesNotExist:
                    messages.add_message(request, messages.ERROR, message=_('Error sending message: Unknown user (%s)'%to))
                    pass
            return redirect('manage-attendees', event.id)
        else:
            messages.add_message(request, messages.ERROR, message=_('Error sending message: %s' % contact_form.errors))
    else:
        contact_form = EventContactForm()
        contact_form.fields['to'].choices = default_choices + attendee_choices
    context = {
        'event': event,
        'attendees': attendees,
        'contact_form': contact_form,
        'can_edit_event': request.user.profile.can_edit_event(event),
    }
    return render(request, 'get_together/events/manage_attendees.html', context)

@login_required
def invite_attendees(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    attendee_userids = [attendee.user.id for attendee in Attendee.objects.filter(event=event)]
    members = Member.objects.filter(team=event.team, ).order_by('user__realname')
    member_choices = [(member.id, member.user) for member in members if member.user.user.account.is_email_confirmed and member.user.id not in attendee_userids]
    default_choices = [('all', 'All Members (%s)' % len(member_choices))]

    if request.method == 'POST' and request.POST.get('form', None) == 'email':
        email_form = EventInviteEmailForm(request.POST)
        if email_form.is_valid():
            to = email_form.cleaned_data['emails']
            for email in to:
                invite_attendee(email, event, request.user)
            messages.add_message(request, messages.SUCCESS, message=_('Sent %s invites' % len(to)))
            return redirect(event.get_absolute_url())
        team_form = EventInviteMemberForm()
        team_form.fields['member'].choices = default_choices + member_choices
    elif request.method == 'POST' and request.POST.get('form', None) == 'team':
        team_form = EventInviteMemberForm(request.POST)
        team_form.fields['member'].choices = default_choices + member_choices
        if team_form.is_valid():
            to = team_form.cleaned_data['member']
            if to == 'all':
                for (member_id, user) in member_choices:
                    try:
                        attendee = Attendee.objects.get(event=event, user=user)
                    except:
                        # No attendee record found, so send the invite
                        invite_attendee(user.user, event, request.user)
                messages.add_message(request, messages.SUCCESS, message=_('Sent %s invites' % len(member_choices)))
                return redirect(event.get_absolute_url())
            else:
                member = get_object_or_404(Member, id=to)
                try:
                    attendee = Attendee.objects.get(event=event, user=member.user)
                except:
                    # No attendee record found, so send the invite
                    invite_attendee(member.user.user, event, request.user)
                    messages.add_message(request, messages.SUCCESS, message=_('Invited %s' % member.user))
                return redirect(event.get_absolute_url())
        email_form = EventInviteEmailForm()
    else:
        email_form = EventInviteEmailForm()
        team_form = EventInviteMemberForm()
        team_form.fields['member'].choices = default_choices + member_choices

    context = {
        'event': event,
        'email_form': email_form,
        'team_form': team_form,
        'member_choice_count': len(member_choices),
        'can_edit_team': request.user.profile.can_edit_team(event.team),
        'is_email_confirmed': request.user.account.is_email_confirmed,
    }
    return render(request, 'get_together/events/invite_attendees.html', context)


def invite_attendee(email, event, sender):
    context = {
        'sender': sender.profile,
        'team': event.team,
        'event': event,
        'site': Site.objects.get(id=1),
    }
    recipient = None
    if type(email) == User:
        recipient = email
        email = recipient.email

    email_subject = 'Invitation to attend: %s' % event.name
    email_body_text = render_to_string('get_together/emails/events/attendee_invite.txt', context)
    email_body_html = render_to_string('get_together/emails/events/attendee_invite.html', context)
    email_recipients = [email]
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

    success = send_mail(
        from_email=email_from,
        html_message=email_body_html,
        message=email_body_text,
        recipient_list=email_recipients,
        subject=email_subject,
        fail_silently=True,
    )
    EmailRecord.objects.create(
        sender=sender,
        recipient=recipient,
        email=email,
        subject=email_subject,
        body=email_body_text,
        ok=success
    )


def contact_attendee(attendee, body, sender):
    context = {
        'sender': sender,
        'event': attendee.event,
        'body': body,
        'site': Site.objects.get(id=1),
    }
    email_subject = 'A message about: %s' % attendee.event.name
    email_body_text = render_to_string('get_together/emails/events/attendee_contact.txt', context)
    email_body_html = render_to_string('get_together/emails/events/attendee_contact.html', context)
    email_recipients = [attendee.user.user.email]
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

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
        recipient=attendee.user.user,
        email=attendee.user.user.email,
        subject=email_subject,
        body=email_body_text,
        ok=success
    )


@verify_csrf(token_key='csrftoken')
def attend_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user.is_anonymous:
        messages.add_message(request, messages.WARNING, message=_("You must be logged in to say you're attending."))
        return redirect(event.get_absolute_url())

    if event.is_over:
        messages.add_message(request, messages.WARNING, message=_("You can not change your status on an event that has ended."))
        return redirect(event.get_absolute_url())

    if event.status == event.CANCELED:
        messages.add_message(request, messages.WARNING, message=_("This event has been canceled."))
        return redirect(event.get_absolute_url())

    try:
        attendee = Attendee.objects.get(event=event, user=request.user.profile)
    except:
        attendee = Attendee(event=event, user=request.user.profile, role=Attendee.NORMAL)

    attendee.status = Attendee.YES
    if request.GET.get('response', None) == 'maybe':
        attendee.status = Attendee.MAYBE
    if request.GET.get('response', None) == 'no':
        attendee.status = Attendee.NO
    attendee.joined_date = timezone.now()
    attendee.save()
    if attendee.status == Attendee.YES:
        messages.add_message(request, messages.SUCCESS, message=_("We'll see you there!"))
    return redirect(event.get_absolute_url())


def attended_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    attendee = get_object_or_404(Attendee, id=request.GET.get('attendee', None))
    if request.user.is_anonymous:
        return JsonResponse({'status': 'ERROR', 'message': _("You must be logged in mark an attendee's actual status.")})

    if not event.is_over:
        return JsonResponse({'status': 'ERROR', 'message': _("You can not set an attendee's actual status until the event is over")})

    if request.GET.get('response', None) == 'yes':
        attendee.actual = Attendee.YES
    if request.GET.get('response', None) == 'no':
        attendee.actual = Attendee.NO
    attendee.save()

    return JsonResponse({'status': 'OK', 'attendee_id': attendee.id, 'actual': attendee.actual_name})


def comment_event(request, event_id):
    event = Event.objects.get(id=event_id)
    if not event.enable_comments:
        messages.add_message(request, messages.WARNING, message=_('This event does not allow comments.'))
        return redirect(event.get_absolute_url())

    if request.user.is_anonymous:
        messages.add_message(request, messages.WARNING, message=_("You must be logged in to comment."))
        return redirect(event.get_absolute_url())

    if request.method == 'POST':
        new_comment = EventComment(author=request.user.profile, event=event)
        comment_form = EventCommentForm(request.POST, instance=new_comment)
        if comment_form.is_valid():
            new_comment = comment_form.save()
            send_comment_emails(new_comment)
            return redirect(event.get_absolute_url()+'#comment-%s'%new_comment.id)

    return redirect(event.get_absolute_url())

def edit_comment(request, comment_id):
    comment = get_object_or_404(EventComment, id=comment_id)
    if not request.user.profile.can_edit_event(comment.event) and request.user.profile.id != comment.author.id:
        messages.add_message(request, messages.WARNING, message=_("You can not edit a comment that is not yours."))
        return redirect(comment.event.get_absolute_url())

    if request.method == 'POST':
        comment_form = EventCommentForm(request.POST, instance=comment)
        if comment_form.is_valid():
            comment_form.save()
            return redirect(comment.event.get_absolute_url()+'#comment-%s'%comment.id)
        else:
            messages.add_message(request, messages.ERROR, message=_("Error updating comment."))
            
    return redirect(comment.event.get_absolute_url())

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(EventComment, id=comment_id)
    event = comment.event
    if not request.user.profile.can_edit_event(comment.event) and request.user.profile.id != comment.author.id:
        messages.add_message(request, messages.WARNING, message=_('You can not make delete this comment.'))
        return redirect(event.get_absolute_url()+"#comment-"+comment_id)

    if request.method == 'GET':
        form = DeleteCommentForm()

        context = {
            'comment': comment,
            'event': event,
            'delete_form': form,
        }
        return render(request, 'get_together/events/delete_comment.html', context)
    elif request.method == 'POST':
        form = DeleteCommentForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            comment.delete()
            return redirect(event.get_absolute_url())
        else:
            context = {
                'comment': comment,
                'event': event,
                'delete_form': form,
            }
            return render(request, 'get_together/events/delete_comment.html', context)
    else:
     return redirect

def send_comment_emails(comment):
    context = {
        'comment': comment,
        'site': Site.objects.get(id=1),
    }
    email_subject = 'New comment on: %s' % comment.event.name
    email_body_text = render_to_string('get_together/emails/events/event_comment.txt', context)
    email_body_html = render_to_string('get_together/emails/events/event_comment.html', context)
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

    for attendee in comment.event.attendees.filter(user__account__is_email_confirmed=True):
        success = send_mail(
            from_email=email_from,
            html_message=email_body_html,
            message=email_body_text,
            recipient_list=[attendee.user.email],
            subject=email_subject,
            fail_silently=True,
        )
        EmailRecord.objects.create(
            sender=comment.author.user,
            recipient=attendee.user,
            email=attendee.user.email,
            subject=email_subject,
            body=email_body_text,
            ok=success
        )

@login_required
def add_event_photo(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.is_in_team(event.team):
        messages.add_message(request, messages.WARNING, message=_('You can not add photos this event.'))
        return redirect(event.get_absolute_url())

    if not event.enable_photos:
        messages.add_message(request, messages.WARNING, message=_('This event does not allow uploading photos.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = UploadEventPhotoForm()

        context = {
            'event': event,
            'photo_form': form,
        }
        return render(request, 'get_together/events/add_photo.html', context)
    elif request.method == 'POST':
        new_photo = EventPhoto(event=event, uploader=request.user.profile)
        form = UploadEventPhotoForm(request.POST, request.FILES, instance=new_photo)
        if form.is_valid():
            form.save()
            return redirect(event.get_absolute_url())
        else:
            context = {
                'event': event,
                'photo_form': form,
            }
            return render(request, 'get_together/events/add_photo.html', context)
    else:
     return redirect('home')

@login_required
def remove_event_photo(request, photo_id):
    photo = get_object_or_404(EventPhoto, id=photo_id)
    event = photo.event

    if not request.user.profile.can_edit_event(event) and photo.uploader != request.user.profile:
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this photo.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = RemoveEventPhotoForm()

        context = {
            'photo': photo,
            'event': event,
            'remove_form': form,
        }
        return render(request, 'get_together/events/remove_photo.html', context)
    elif request.method == 'POST':
        form = RemoveEventPhotoForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            photo.delete()
            return redirect(event.get_absolute_url())
    else:
        return redirect('home')

@login_required
def add_place_to_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = NewPlaceForm()

        context = {
            'event': event,
            'place_form': form,
        }
        return render(request, 'get_together/places/create_place.html', context)
    elif request.method == 'POST':
        form = NewPlaceForm(request.POST)
        if form.is_valid:
            if request.POST.get('id', None):
                form.instance.id = request.POST.get('id')
            new_place = form.save()
            event.place = new_place
            event.save()
            if event.series is not None and event.series.place is None:
                event.series.place = new_place;
                event.series.save()
            return redirect(event.get_absolute_url())
        else:
            context = {
                'event': event,
                'place_form': form,
            }
            return render(request, 'get_together/places/create_place.html', context)
    else:
     return redirect('home')

@login_required
def add_place_to_series(request, series_id):
    series = get_object_or_404(EventSeries, id=series_id)
    if not request.user.profile.can_edit_series(series):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(series.get_absolute_url())

    if request.method == 'GET':
        form = NewPlaceForm()

        context = {
            'series': series,
            'place_form': form,
        }
        return render(request, 'get_together/places/add_place_to_series.html', context)
    elif request.method == 'POST':
        form = NewPlaceForm(request.POST)
        if form.is_valid:
            if request.POST.get('id', None):
                form.instance.id = request.POST.get('id')
            new_place = form.save()
            series.place = new_place
            series.save()
            return redirect('show-series', series.id, series.slug)
        else:
            context = {
                'series': series,
                'place_form': form,
            }
            return render(request, 'get_together/places/add_place_to_series.html', context)
    else:
     return redirect('home')

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = TeamEventForm(instance=event)
        if event.series is not None:
            form.initial['recurrences'] = event.series.recurrences

        context = {
            'team': event.team,
            'event': event,
            'event_form': form,
        }
        return render(request, 'get_together/events/edit_event.html', context)
    elif request.method == 'POST':
        form = TeamEventForm(request.POST,instance=event)
        if form.is_valid:
            new_event = form.save()

            if form.cleaned_data.get('recurrences', None):
                if event.series is not None:
                    event.series.recurrences = form.cleaned_data['recurrences']
                    event.series.save()
                else:
                    new_series = EventSeries.from_event(new_event, recurrences=form.cleaned_data['recurrences'])
                    new_series.save()
                    new_event.series = new_series
                    new_event.save()
            else:
                if event.series is not None:
                    old_series = event.series
                    event.series = None
                    event.save()
                    if old_series.instances.count() < 1:
                        old_series.delete()
                else:
                    event.save()


            return redirect(new_event.get_absolute_url())
        else:
            context = {
                'team': event.team,
                'event': event,
                'event_form': form,
            }
            return render(request, 'get_together/events/edit_event.html', context)
    else:
     return redirect('home')

@login_required
def change_event_host(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not change this event\'s host'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = ChangeEventHostForm(instance=event)
        form.fields['team'].queryset = Team.objects.filter(member__user=request.user.profile, member__role__gte=Member.MODERATOR).order_by('name')

        context = {
            'event': event,
            'change_form': form,
        }
        return render(request, 'get_together/events/change_team.html', context)
    elif request.method == 'POST':
        form = ChangeEventHostForm(request.POST, instance=event)
        form.fields['team'].queryset = Team.objects.filter(member__user=request.user.profile, member__role__gte=Member.MODERATOR).order_by('name')
        if form.is_valid():
            new_event = form.save()
            messages.add_message(request, messages.SUCCESS, message=_('Your event host has been changed.'))
            return redirect(new_event.get_absolute_url())
        else:
            context = {
                'event': event,
                'change_form': form,
            }
            return render(request, 'get_together/orgs/request_to_join.html', context)
    else:
     return redirect('home')

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = DeleteEventForm()

        context = {
            'team': event.team,
            'event': event,
            'delete_form': form,
        }
        return render(request, 'get_together/events/delete_event.html', context)
    elif request.method == 'POST':
        form = DeleteEventForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            team_slug = event.team.slug
            delete_event_searchable(event)
            event.delete()
            return redirect('show-team-by-slug', team_slug)
        else:
            context = {
                'team': event.team,
                'event': event,
                'delete_form': form,
            }
            return render(request, 'get_together/events/delete_event.html', context)
    else:
     return redirect('home')

@login_required
def cancel_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        form = CancelEventForm()

        context = {
            'team': event.team,
            'event': event,
            'cancel_form': form,
        }
        return render(request, 'get_together/events/cancel_event.html', context)
    elif request.method == 'POST':
        form = CancelEventForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            event.status = Event.CANCELED
            event.save()
            send_cancellation_emails(event, form.cleaned_data['reason'], request.user)
            return redirect(event.get_absolute_url())
        else:
            context = {
                'team': event.team,
                'event': event,
                'cancel_form': form,
            }
            return render(request, 'get_together/events/cancel_event.html', context)
    else:
        return redirect('home')

def send_cancellation_emails(event, reason, canceled_by):
    context = {
        'event': event,
        'reason': reason,
        'by': canceled_by.profile,
        'site': Site.objects.get(id=1),
    }
    email_subject = 'Event canceled: %s' % event.name
    email_body_text = render_to_string('get_together/emails/events/event_canceled.txt', context)
    email_body_html = render_to_string('get_together/emails/events/event_canceled.html', context)
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gettogether.community')

    for attendee in event.attendees.filter(user__account__is_email_confirmed=True):
        success = send_mail(
            from_email=email_from,
            html_message=email_body_html,
            message=email_body_text,
            recipient_list=[attendee.user.email],
            subject=email_subject,
            fail_silently=True,
        )
        EmailRecord.objects.create(
            sender=canceled_by,
            recipient=attendee.user,
            email=attendee.user.email,
            subject=email_subject,
            body=email_body_text,
            ok=success
        )

@login_required
def restore_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(event.get_absolute_url())

    event.status = Event.CONFIRMED
    event.save()
    return redirect(event.get_absolute_url())

@login_required
def edit_series(request, series_id):
    series = get_object_or_404(EventSeries, id=series_id)

    if not request.user.profile.can_edit_series(series):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(series.get_absolute_url())

    if request.method == 'GET':
        form = EventSeriesForm(instance=series)

        context = {
            'team': series.team,
            'series': series,
            'series_form': form,
        }
        return render(request, 'get_together/events/edit_series.html', context)
    elif request.method == 'POST':
        form = EventSeriesForm(request.POST,instance=series)
        if form.is_valid:
            new_series = form.save()
            return redirect(new_series.get_absolute_url())
        else:
            context = {
                'team': event.team,
                'series': series,
                'series_form': form,
            }
            return render(request, 'get_together/events/edit_series.html', context)
    else:
     return redirect('home')

@login_required
def delete_series(request, series_id):
    series = get_object_or_404(EventSeries, id=series_id)
    if not request.user.profile.can_edit_series(series):
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this event.'))
        return redirect(series.get_absolute_url())

    if request.method == 'GET':
        form = DeleteEventSeriesForm()

        context = {
            'team': series.team,
            'series': series,
            'delete_form': form,
        }
        return render(request, 'get_together/events/delete_series.html', context)
    elif request.method == 'POST':
        form = DeleteEventSeriesForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            team_slug = series.team.slug
            series.delete()
            return redirect('show-team-by-slug', team_slug)
        else:
            context = {
                'team': series.team,
                'series': series,
                'delete_form': form,
            }
            return render(request, 'get_together/events/delete_series.html', context)
    else:
     return redirect('home')


