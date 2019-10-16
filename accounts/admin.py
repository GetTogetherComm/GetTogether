from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Account, Badge, BadgeGrant, EmailConfirmation, EmailRecord


# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    search_fields = ("user__username", "user__email", "acctname")
    list_display = (
        "user",
        "acctname",
        "email",
        "is_email_confirmed",
        "has_completed_setup",
    )
    list_filter = ("is_email_confirmed", "has_completed_setup")

    def email(self, obj):
        return obj.user.email

    email.short_description = "Email"


admin.site.register(Account, AccountAdmin)


class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "img_url")

    def icon(self, obj):
        return mark_safe(
            '<img src="%s" title="%s" height="32px" width="32px"/>'
            % (obj.img_url, obj.name)
        )

    icon.short_description = "Icon"


admin.site.register(Badge, BadgeAdmin)


class GrantAdmin(admin.ModelAdmin):
    raw_id_fields = ("account", "granted_by")
    list_display = ("badge", "account", "expires", "granted_by")
    list_filter = ("badge", ("granted_by", admin.RelatedOnlyFieldListFilter))


admin.site.register(BadgeGrant, GrantAdmin)


class ConfirmationAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "key", "expires")


admin.site.register(EmailConfirmation, ConfirmationAdmin)


class EmailAdmin(admin.ModelAdmin):
    list_display = ["when", "recipient_display", "subject", "sender", "ok"]
    list_filter = ["ok", "when", ("sender", admin.RelatedOnlyFieldListFilter)]
    readonly_fields = ["when", "email", "subject", "body", "ok"]
    search_fields = ["subject", "body", "to"]

    def recipient_display(self, record):
        if record.recipient is not None:
            return "%s <%s>" % (record.recipient, record.email)
        else:
            return record.email

    recipient_display.short_description = "To"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(EmailRecord, EmailAdmin)
