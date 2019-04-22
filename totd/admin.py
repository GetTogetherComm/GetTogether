from django import forms
from django.contrib import admin
from django.urls.resolvers import get_resolver

from .models import Tip


def url_choices():
    choices = [("", "-- All Pages --")]
    for entry in get_resolver(None).url_patterns:
        if entry.pattern.name:
            choices.append((entry.pattern.name, entry.pattern.name))
    return choices


# Register your models here.
class TipForm(forms.ModelForm):
    class Meta:
        model = Tip
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["view"].widget = forms.Select(choices=url_choices())


class TipAdmin(admin.ModelAdmin):
    list_filter = ("level", "view")
    list_display = ("name", "level", "view", "run_start", "run_end", "seen_count")
    search_fields = ("name", "view")
    form = TipForm

    def seen_count(self, tip):
        return tip.seen_by.count()

    seen_count.short_description = "Seen by"


admin.site.register(Tip, TipAdmin)
