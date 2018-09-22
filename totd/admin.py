from django.contrib import admin
from django.urls.resolvers import get_resolver
from django import forms

from .models import Tip

def url_choices():
    choices = [('', '-- All Pages --')]
    for entry in get_resolver(None).url_patterns:
        if entry.pattern.name:
            choices.append((entry.pattern.name, entry.pattern.name))
    return choices

# Register your models here.
class TipForm(forms.ModelForm):
    class Meta:
        model = Tip
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['view'].widget = forms.Select(choices=url_choices())

class TipAdmin(admin.ModelAdmin):
    #raw_id_fields = ('seen_by',)
    list_filter =('level', 'view')
    list_display = ('name', 'level', 'view', 'run_start', 'run_end')
    search_fields = ('name', 'view')
    form = TipForm


admin.site.register(Tip, TipAdmin)
