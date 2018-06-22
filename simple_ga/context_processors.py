from simple_ga.api import get_events


def events(request):
    """
    Return a lazy 'messages' context variable as well as
    'DEFAULT_MESSAGE_LEVELS'.
    """
    return {
        'ga_events': get_events(request),
    }