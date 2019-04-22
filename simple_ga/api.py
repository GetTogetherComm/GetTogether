class GAFailure(Exception):
    pass


def add_event(request, action, category=None, label=None, value=1, fail_silently=False):
    """
    Attempt to add a message to the request using the 'messages' app.
    """
    try:
        events = request._ga_events
    except AttributeError:
        if not hasattr(request, "META"):
            raise TypeError(
                "add_message() argument must be an HttpRequest object, not "
                "'%s'." % request.__class__.__name__
            )
        if not fail_silently:
            raise GAFailure(
                "You cannot add messages without installing "
                "django.contrib.messages.middleware.MessageMiddleware"
            )
    else:
        return events.add(action, category, label, value)


def get_events(request):
    """
    Return the message storage on the request if it exists, otherwise return
    an empty list.
    """
    if not hasattr(request, "_ga_events"):
        return []
    return request._ga_events
