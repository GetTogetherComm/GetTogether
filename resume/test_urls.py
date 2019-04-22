"""
Testing URL configuration for this app only
"""
from django.http import HttpResponse
from django.urls import include, path


def test_view():
    return HttpResponse("Test View")


urlpatterns = [path("test/view", test_view, name="test-view")]
