import re
import unicodedata

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.middleware.csrf import _compare_salted_tokens, _sanitize_token

SLUG_OK = "-_~"


def slugify(s, ok=SLUG_OK, lower=True, spaces=False):
    # L and N signify letter/number.
    # http://www.unicode.org/reports/tr44/tr44-4.html#GC_Values_Table
    rv = []
    s = re.sub("\s*&\s*", " and ", s)
    for c in unicodedata.normalize("NFKC", s):
        cat = unicodedata.category(c)[0]
        if cat in "LN" or c in ok:
            rv.append(c)
        if cat == "Z":  # space
            rv.append(" ")
    new = "".join(rv).strip()
    if not spaces:
        new = re.sub("[-\s]+", "-", new)
    return new.lower() if lower else new


def verify_csrf(token_key="csrftoken"):
    def wrap_view(view_func):
        def check_csrf_token(request, *args, **kwargs):
            csrf_token = _sanitize_token(request.GET.get(token_key, ""))
            match = _compare_salted_tokens(
                csrf_token, request.COOKIES.get(settings.CSRF_COOKIE_NAME, "")
            )
            if not match and getattr(settings, "CSRF_VERIFY_TOKEN", True):
                raise PermissionDenied
            else:
                return view_func(request, *args, **kwargs)

        return check_csrf_token

    return wrap_view
