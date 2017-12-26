from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from .models.search import Searchable, SearchableSerializer
from .models.events import Event

import simplejson

# Create your views here.
def searchable_list(request, *args, **kwargs):
    searchables = Searchable.objects.all()
    serializer = SearchableSerializer(searchables, many=True)
    return JsonResponse(serializer.data, safe=False)

def events_list(request, *args, **kwargs):
    events = Event.objects.all()
    context = {
        'events_list': events,
    }
    return render(request, 'events/event_list.html', context)
