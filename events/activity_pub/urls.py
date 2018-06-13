"""
ActivityPub compliant views
"""
from django.urls import path, include

from . import views

urlpatterns = [

    path('events.json', views.events_list, name='ap-events-list'),
    path('places.json', views.places_list, name='ap-places-list'),
]
