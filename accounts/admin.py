from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Account, Badge, BadgeGrant

# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'acctname')
admin.site.register(Account, AccountAdmin)

class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'img_url')
    def icon(self, obj):
        return (mark_safe('<img src="%s" title="%s" height="32px" width="32px"/>' % (obj.img_url, obj.name)))
    icon.short_description = 'Icon'
admin.site.register(Badge, BadgeAdmin)

class GrantAdmin(admin.ModelAdmin):
    list_display = ('badge', 'account', 'expires', 'granted_by')
admin.site.register(BadgeGrant, GrantAdmin)


