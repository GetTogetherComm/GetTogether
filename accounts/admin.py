from django.contrib import admin

from .models import Account, Badge, BadgeGrant

# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'acctname')
admin.site.register(Account, AccountAdmin)

class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'img_url')
admin.site.register(Badge, BadgeAdmin)

class GrantAdmin(admin.ModelAdmin):
    list_display = ('badge', 'account', 'expires', 'granted_by')
admin.site.register(BadgeGrant, GrantAdmin)


