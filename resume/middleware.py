import json

from django.utils.deprecation import MiddlewareMixin


class ResumeStorage:
    session_key = "_resume"

    def __init__(self, request):
        self.request = request
        self._resume_points = self.load()

    def __len__(self):
        return len(self._resume_points)

    def __iter__(self):
        return iter(self._resume_points)

    def __contains__(self, item):
        return item in self._resume_points

    def load(self):
        """
        Retrieve a list of resume points from the request's session.
        """
        if self.session_key not in self.request.session:
            return []
        return json.loads(self.request.session.get(self.session_key))

    def store(self):
        """
        Store a list of resume points to the request's session.
        """
        if self._resume_points:
            self.request.session[self.session_key] = json.dumps(self._resume_points)
        else:
            self.request.session.pop(self.session_key, None)
        return []

    def add(self, path):
        self._resume_points.append(path)

    def pop(self):
        if len(self._resume_points) > 0:
            return self._resume_points.pop()
        else:
            return None


class ResumeMiddleware(MiddlewareMixin):
    """
    Middleware that handles setting resume points in a user flow.
    """

    def process_request(self, request):
        request._resume_points = ResumeStorage(request)

    def process_response(self, request, response):
        """
        Update the storage backend (i.e., save the resume points).

        Raise ValueError if not all resume points could be stored and DEBUG is True.
        """
        # A higher middleware layer may return a request which does not contain
        # resume storage, so make no assumption that it will be there.
        if hasattr(request, "_resume_points"):
            request._resume_points.store()
        return response
