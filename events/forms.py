from django.utils.safestring import mark_safe
from django.forms import ModelForm, Field
from django.forms.widgets import Select, Media
from .models.profiles import Team
from .models.events import Event

class LookupMedia(Media):
    def render(self):
        return mark_safe('''<script type="text/javascript"><script>
$(document).ready(function(){
    $("#{{ widget.name }}_search").keyup(function() {
	var searchText = this.value;
	$.getJSON("{{ widget.source }}?q="+searchText, function(data) {
	    var selectField = $("#{{ widget.name }}_select");
	    selectField.empty();
	    $.each(data, function(){
		selectField.append('<option value="'+ this.{{ widget.key }} +'">'+ this.{{ widget.label }} + '</option>')
	    });
	});
    });
});
</script>''')

class Lookup(Select):
    input_type = 'select'
    template_name = 'forms/widgets/lookup.html'
    add_id_index = False
    checked_attribute = {'selected': True}
    option_inherits_attrs = False

    def __init__(self, source='#', key="id", label="name", attrs=None):
        super().__init__(attrs)
        self.source = source
        self.key = key
        self.label = label
        self.name = 'place'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['source'] = self.source
        context['widget']['key'] = self.key
        context['widget']['label'] = self.label
        return context

class TeamForm(ModelForm):
    class Meta:
        model = Team
        fields = '__all__'

class NewTeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'country', 'spr', 'city', 'web_url', 'tz']
        widgets = {
            'country': Lookup(source='/api/country/', label='name'),
            'spr': Lookup(source='/api/spr/', label='name'),
            'city': Lookup(source='/api/cities/', label='name'),
        }

class TeamEventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'start_time', 'end_time', 'summary', 'place', 'web_url', 'announce_url', 'tags']
        widgets = {
            'country': Lookup(source='/api/country/', label='name'),
            'spr': Lookup(source='/api/spr/', label='name'),
            'city': Lookup(source='/api/cities/', label='name'),
        }

class NewTeamEventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'start_time', 'end_time', 'summary', 'place']
        widgets = {
            'place': Lookup(source='/api/places/', label='name'),
        }


