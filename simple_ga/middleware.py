import json

from django.utils.deprecation import MiddlewareMixin
from django.utils.safestring import SafeData, mark_safe


class GAEvent:
    def __init__(self, action, category=None, label=None, value=1):
        self.action = action
        self.category = category
        self.label = label
        self.value = value

    def gtag(self):
        return mark_safe(self._to_gtag_js())

    def _to_gtag_js(self):
        return (
            "gtag('event', '%(action)s', {'event_category' : '%(category)s', 'event_label' : '%(label)s' , 'value' : '%(value)s' });"
            % {
                "action": self.action,
                "category": self.category,
                "label": self.label,
                "value": self.value,
            }
        )


class EventEncoder(json.JSONEncoder):
    """
    Compactly serialize instances of the ``Message`` class as JSON.
    """

    message_key = "__json_message"

    def default(self, obj):
        if isinstance(obj, GAEvent):
            event = {
                "type": "GAEvent",
                "action": obj.action,
                "category": obj.category,
                "label": obj.label,
                "value": obj.value,
            }
            return event
        return super().default(obj)


class EventDecoder(json.JSONDecoder):
    """
    Decode JSON that includes serialized ``Message`` instances.
    """

    def process_events(self, obj):
        if isinstance(obj, list) and obj:
            return [self.process_events(item) for item in obj]
        if isinstance(obj, dict):
            if obj.get("type", None) == "GAEvent":
                del obj["type"]
                return GAEvent(**obj)
            return {key: self.process_events(value) for key, value in obj.items()}
        return obj

    def decode(self, s, **kwargs):
        decoded = super().decode(s, **kwargs)
        return self.process_events(decoded)


class EventStorage:
    session_key = "_ga_events"

    def __init__(self, request):
        self.request = request
        self._ga_events = self.load()

    def __len__(self):
        return len(self._ga_events)

    def __iter__(self):
        next_event = True
        while next_event is not None:
            next_event = self.pop()
            yield next_event

    def __contains__(self, item):
        return item in self._ga_events

    def load(self):
        """
        Retrieve a list of resume points from the request's session.
        """
        if self.session_key not in self.request.session:
            return []
        return self.deserialize_events(self.request.session.get(self.session_key))

    def store(self):
        """
        Store a list of resume points to the request's session.
        """
        if self._ga_events:
            self.request.session[self.session_key] = self.serialize_events(
                self._ga_events
            )
        else:
            self.request.session.pop(self.session_key, None)
        return []

    def serialize_events(self, events):
        encoder = EventEncoder(separators=(",", ":"))
        return encoder.encode(events)

    def deserialize_events(self, data):
        if data and isinstance(data, str):
            return json.loads(data, cls=EventDecoder)
        return data

    def add(self, action, category=None, label=None, value=None):
        self._ga_events.append(GAEvent(action, category, label, value))

    def pop(self):
        if len(self._ga_events) > 0:
            return self._ga_events.pop()
        else:
            return None


class GAEventMiddleware(MiddlewareMixin):
    """
    Middleware that handles setting resume points in a user flow.
    """

    def process_request(self, request):
        request._ga_events = EventStorage(request)

    def process_response(self, request, response):
        """
        Update the storage backend (i.e., save the resume points).

        Raise ValueError if not all resume points could be stored and DEBUG is True.
        """
        # A higher middleware layer may return a request which does not contain
        # resume storage, so make no assumption that it will be there.
        if hasattr(request, "_ga_events"):
            request._ga_events.store()
        return response
