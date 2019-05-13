from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _

import simple_ga as ga
from events import location
from events.forms import NewEventDetailsForm, NewEventForm, NewPlaceForm
from events.models.events import Attendee, Event, EventSeries
from events.models.profiles import Team, UserProfile


@login_required
def new_event_start(request):
    team = request.user.profile.personal_team

    new_event = Event(team=team, created_by=request.user.profile)

    if request.method == "GET":
        form = NewEventForm(instance=new_event)

        context = {"event": new_event, "team": team, "event_form": form}
        return render(request, "get_together/new_event/create_event.html", context)
    elif request.method == "POST":
        form = NewEventForm(request.POST, instance=new_event)
        if form.is_valid:
            new_event = form.save()
            Attendee.objects.create(
                event=new_event,
                user=request.user.profile,
                role=Attendee.HOST,
                status=Attendee.YES,
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                message=_(
                    "Your event has been scheduled! Next, find a place for your event."
                ),
            )
            ga.add_event(
                request,
                action="new_event",
                category="activity",
                label=new_event.get_full_url(),
            )

            return redirect("new-event-add-place", new_event.id)
        else:
            context = {"event": new_event, "team": team, "event_form": form}
            return render(request, "get_together/new_event/create_event.html", context)
    else:
        return redirect("home")


@login_required
def new_event_add_place(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(
            request,
            messages.WARNING,
            message=_("You can not make changes to this event."),
        )
        return redirect(event.get_absolute_url())

    if request.method == "GET":
        form = NewPlaceForm()

        context = {"event": event, "place_form": form}
        return render(request, "get_together/new_event/add_place.html", context)
    elif request.method == "POST":
        form = NewPlaceForm(request.POST)
        if form.is_valid:
            if request.POST.get("id", None):
                form.instance.id = request.POST.get("id")
            new_place = form.save()
            event.place = new_place
            event.save()
            if event.series is not None and event.series.place is None:
                event.series.place = new_place
                event.series.save()
            return redirect("new-event-add-details", event.id)
        else:
            context = {"event": event, "place_form": form}
            return render(request, "get_together/new_event/add_place.html", context)
    else:
        return redirect("home")


@login_required
def new_event_add_details(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(
            request,
            messages.WARNING,
            message=_("You can not make changes to this event."),
        )
        return redirect(event.get_absolute_url())

    if request.method == "GET":
        form = NewEventDetailsForm(instance=event)

        context = {"event": event, "team": event.team, "event_form": form}
        return render(request, "get_together/new_event/detail_event.html", context)
    elif request.method == "POST":
        form = NewEventDetailsForm(request.POST, instance=event)
        if form.is_valid:
            new_event = form.save()

            if form.cleaned_data.get("recurrences", None):
                new_series = EventSeries.from_event(
                    new_event, recurrences=form.cleaned_data["recurrences"]
                )
                new_series.save()
                new_event.series = new_series
                new_event.save()

            return redirect("new-event-add-team", new_event.id)
        else:
            context = {"event": event, "team": event.team, "event_form": form}
            return render(request, "get_together/new_event/detail_event.html", context)
    else:
        return redirect("home")


@login_required
def new_event_add_team(request, event_id):
    teams = request.user.profile.moderating
    event = get_object_or_404(Event, id=event_id)
    if not request.user.profile.can_edit_event(event):
        messages.add_message(
            request,
            messages.WARNING,
            message=_("You can not make changes to this event."),
        )
        return redirect(event.get_absolute_url())

    context = {"event": event, "teams": teams}
    if request.method == "GET":
        return render(request, "get_together/new_event/pick_team.html", context)
    elif request.method == "POST":
        if "team_id" in request.POST:
            team = Team.objects.get(id=request.POST.get("team_id"))
            event.team = team
            event.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                message=_(
                    "Your event is ready! Now you can start inviting people to join you"
                ),
            )
            return redirect(event.get_absolute_url())
        else:
            return render(request, "get_together/new_event/pick_team.html", context)
    else:
        return redirect("home")
