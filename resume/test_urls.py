"""
Testing URL configuration for this app only
"""
from django.urls import path, include
from django.http import HttpResponse


def test_view():
    return HttpResponse('Test View')


urlpatterns = [
    path('test/view', test_view, name='test-view'),
]
