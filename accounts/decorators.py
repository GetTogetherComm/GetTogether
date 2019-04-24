from functools import wraps

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render, resolve_url

from .models import Account


def setup_wanted(view_func, setup_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user has completed the setup
    process, redirecting to settings.SETUP_URL if required
    """

    @wraps(view_func)
    def wrap(request, *args, **kwargs):
        if (
            not request.user.is_authenticated
            or request.user.account.has_completed_setup
        ):
            return view_func(request, *args, **kwargs)
        else:
            resolved_setup_url = resolve_url(setup_url or settings.SETUP_URL)
            path = request.get_full_path()
            return redirect_to_login(path, resolved_setup_url, redirect_field_name)

    return wrap


setup_required = login_required(setup_wanted)


def check_setup(request):
    """
    Checks if a user has completed setup
    """
    if not request.user.is_authenticated or request.user.account.has_completed_setup:
        return {"account_needs_setup": False, "current_user_account": None}
    elif request.user.account.has_completed_setup:
        return {
            "account_needs_setup": False,
            "current_user_account": request.user.account,
        }
    else:
        resolved_setup_url = resolve_url(settings.SETUP_URL)
        return {
            "account_needs_setup": True,
            "account_setup_url": resolved_setup_url,
            "current_user_account": request.user.account,
        }
