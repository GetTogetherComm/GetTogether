from django.forms import ModelForm
from .models.profiles import Team
from .models.events import Event

class TeamForm(ModelForm):
    class Meta:
        model = Team
        fields = '__all__'

class NewTeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'country', 'spr', 'city', 'web_url', 'tz']

class TeamEventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'start_time', 'end_time', 'summary', 'place', 'web_url', 'announce_url', 'tags']

class NewTeamEventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'start_time', 'end_time', 'summary', 'place']

