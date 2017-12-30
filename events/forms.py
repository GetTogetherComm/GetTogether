from django.forms import ModelForm
from .models.profiles import Team

class TeamForm(ModelForm):
    class Meta:
        model = Team
        fields = '__all__'

class NewTeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'country', 'spr', 'city', 'web_url', 'tz']
