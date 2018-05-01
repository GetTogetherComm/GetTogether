from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from events.models.profiles import UserProfile
from events.forms import (
    SpeakerBioForm,
    DeleteSpeakerForm,
    UserTalkForm,
    DeleteTalkForm,
    SchedulePresentationForm,
)

from events.models.events import Event
from events.models.speakers import Speaker, Talk, Presentation, SpeakerRequest
import datetime
import simplejson

from .teams import *
from .events import *

@login_required
def list_user_talks(request):
    profile = request.user.profile
    speaker_bios = Speaker.objects.filter(user=profile)
    talks = list(Talk.objects.filter(speaker__user=profile))
    context = {
        'speaker_bios': speaker_bios,
        'talks': talks,
    }
    return render(request, 'get_together/speakers/list_user_talks.html', context)

def show_speaker(request, speaker_id):
    speaker = get_object_or_404(Speaker, id=speaker_id)

    context = {
        'speaker': speaker,
        'talks': Talk.objects.filter(speaker=speaker),
        'presentations': Presentation.objects.filter(talk__speaker=speaker, status=Presentation.ACCEPTED),
    }
    return render(request, 'get_together/speakers/show_speaker.html', context)

def add_speaker(request):
    new_speaker = Speaker(user=request.user.profile)
    if request.method == 'GET':
        speaker_form = SpeakerBioForm(instance=new_speaker)
        context = {
            'speaker': new_speaker,
            'speaker_form': speaker_form,
        }
        return render(request, 'get_together/speakers/create_speaker.html', context)
    elif request.method == 'POST':
        speaker_form = SpeakerBioForm(request.POST, request.FILES, instance=new_speaker)
        if speaker_form.is_valid():
            new_speaker = speaker_form.save()
            return redirect('user-talks')
        else:
            context = {
                'speaker': new_speaker,
                'speaker_form': speaker_form,
            }
            return render(request, 'get_together/speakers/create_speaker.html', context)
    return redirect('home')

def edit_speaker(request, speaker_id):
    speaker = get_object_or_404(Speaker, id=speaker_id)
    if request.method == 'GET':
        speaker_form = SpeakerBioForm(instance=speaker)
        context = {
            'speaker': speaker,
            'speaker_form': speaker_form,
        }
        return render(request, 'get_together/speakers/edit_speaker.html', context)
    elif request.method == 'POST':
        speaker_form = SpeakerBioForm(request.POST, request.FILES, instance=speaker)
        if speaker_form.is_valid():
            speaker = speaker_form.save()
            return redirect('user-talks')
        else:
            context = {
                'speaker': speaker,
                'speaker_form': speaker_form,
            }
            return render(request, 'get_together/speakers/edit_speaker.html', context)
    return redirect('home')

def delete_speaker(request, speaker_id):
    speaker = get_object_or_404(Speaker, id=speaker_id)
    if not speaker.user == request.user.profile:
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this speaker bio.'))
        return redirect('show-speaker', speaker_id)

    if request.method == 'GET':
        form = DeleteSpeakerForm()

        context = {
            'speaker': speaker,
            'delete_form': form,
        }
        return render(request, 'get_together/speakers/delete_speaker.html', context)
    elif request.method == 'POST':
        form = DeleteSpeakerForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            speaker.delete()
            return redirect('user-talks')
        else:
            context = {
                'speaker': speaker,
                'delete_form': form,
            }
            return render(request, 'get_together/speakers/delete_speaker.html', context)
    else:
     return redirect('home')

def show_talk(request, talk_id):
    talk = get_object_or_404(Talk, id=talk_id)
    presentations = Presentation.objects.filter(talk=talk, status=Presentation.ACCEPTED).order_by('-event__start_time')
    context = {
        'talk': talk,
        'presentations': presentations,
    }
    return render(request, 'get_together/speakers/show_talk.html', context)

def add_talk(request):
    if Speaker.objects.filter(user=request.user.profile).count() < 1:
        messages.add_message(request, messages.WARNING, message=_('You must create a new Speaker profile before you can add a talk'))
        return redirect('add-speaker')

    new_talk = Talk()
    if request.method == 'GET':
        talk_form = UserTalkForm(instance=new_talk)
        talk_form.fields['speaker'].queryset = request.user.profile.speaker_set
        context = {
            'talk': new_talk,
            'talk_form': talk_form,
        }
        if 'event' in request.GET and request.GET['event']:
            context['event'] = get_object_or_404(Event, id=request.GET['event'])
        return render(request, 'get_together/speakers/create_talk.html', context)
    elif request.method == 'POST':
        talk_form = UserTalkForm(request.POST, instance=new_talk)
        talk_form.fields['speaker'].queryset = request.user.profile.speaker_set
        if talk_form.is_valid():
            new_talk = talk_form.save()
            if 'event' in request.POST and request.POST['event']:
                event = Event.objects.get(id=request.POST['event'])
                Presentation.objects.create(
                    event=event,
                    talk=new_talk,
                    status=Presentation.PROPOSED,
                    created_by=request.user.profile
                )
                return redirect(event.get_absolute_url())
            return redirect('show-talk', new_talk.id)
        else:
            context = {
                'talk': new_talk,
                'talk_form': talk_form,
            }
            return render(request, 'get_together/speakers/create_talk.html', context)
    return redirect('home')

def edit_talk(request, talk_id):
    talk = get_object_or_404(Talk, id=talk_id)
    if not talk.speaker.user == request.user.profile:
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this talk.'))
        return redirect('show-talk', talk_id)

    if request.method == 'GET':
        talk_form = UserTalkForm(instance=talk)
        talk_form.fields['speaker'].queryset = request.user.profile.speaker_set
        context = {
            'talk': talk,
            'talk_form': talk_form,
        }
        return render(request, 'get_together/speakers/edit_talk.html', context)
    elif request.method == 'POST':
        talk_form = UserTalkForm(request.POST, instance=talk)
        talk_form.fields['speaker'].queryset = request.user.profile.speaker_set
        if talk_form.is_valid():
            talk = talk_form.save()
            return redirect('show-talk', talk.id)
        else:
            context = {
                'talk': talk,
                'talk_form': talk_form,
            }
            return render(request, 'get_together/speakers/edit_talk.html', context)
    return redirect('home')

def delete_talk(request, talk_id):
    talk = get_object_or_404(Talk, id=talk_id)
    if not talk.speaker.user == request.user.profile:
        messages.add_message(request, messages.WARNING, message=_('You can not make changes to this talk.'))
        return redirect('show-talk', talk_id)

    if request.method == 'GET':
        form = DeleteTalkForm()

        context = {
            'talk': talk,
            'delete_form': form,
        }
        return render(request, 'get_together/speakers/delete_talk.html', context)
    elif request.method == 'POST':
        form = DeleteTalkForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            talk.delete()
            return redirect('user-talks')
        else:
            context = {
                'talk': talk,
                'delete_form': form,
            }
            return render(request, 'get_together/speakers/delete_talk.html', context)
    else:
     return redirect('home')

@login_required
def propose_event_talk(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not event.team.is_premium:
        messages.add_message(request, messages.ERROR, message=_("You can not manage talks for this event."))
        return redirect(event.get_absolute_url())

    if request.method == 'GET':
        profile = request.user.profile
        talks = list(Talk.objects.filter(speaker__user=profile))
        has_talks = len(talks) > 0
        presentations = event.presentations.filter(talk__speaker__user=profile).order_by('-status')
        for presentation in presentations:
            if presentation.talk in talks:
                talks.remove(presentation.talk)

        context = {
            'event': event,
            'has_talks': has_talks,
            'available_talks': talks,
            'proposed_talks': presentations,
        }
        return render(request, 'get_together/speakers/list_user_presentations.html', context)
    elif request.method == 'POST':
        talk = get_object_or_404(Talk, id=request.POST.get('talk_id'))
        new_proposal = Presentation.objects.create(
            event=event,
            talk=talk,
            status=Presentation.PROPOSED,
            start_time=event.local_start_time,
            created_by=request.user.profile,
        )
        messages.add_message(request, messages.SUCCESS, message=_('Your talk has been submitted to the event organizer.'))
        return redirect(event.get_absolute_url())
    else:
        redirect('home')

def schedule_event_talks(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(request, messages.ERROR, message=mark_safe(_('You can not manage talks for this event.')))
        return redirect(event.get_absolute_url())
    if not event.team.is_premium:
        messages.add_message(request, messages.ERROR, message=mark_safe(_('Upgrade this team to a <a href="/about/premium">Premium</a> account to use this feature.')))
        return redirect(event.get_absolute_url())

    if request.method == 'POST':
        presentation = get_object_or_404(Presentation, id=request.POST.get('presentation_id'))
        if request.POST.get('action') == 'accept':
            presentation.status = Presentation.ACCEPTED
        elif request.POST.get('action') == 'decline':
            presentation.status = Presentation.DECLINED
        elif request.POST.get('action') == 'propose':
            presentation.status = Presentation.PROPOSED
        presentation.save()

    context = {
        'event': event,
        'talks_count': event.presentations.count(),
        'accepted_talks': event.presentations.filter(status=Presentation.ACCEPTED).order_by('start_time'),
        'pending_talks': event.presentations.filter(status=Presentation.PROPOSED).order_by('start_time'),
        'declined_talks': event.presentations.filter(status=Presentation.DECLINED).order_by('start_time'),
    }
    return render(request, 'get_together/events/schedule_event_talks.html', context)

