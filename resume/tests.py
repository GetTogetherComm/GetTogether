from django.test import TestCase, override_settings
from django.http.request import HttpRequest
from resume import set_resume, resume_or_redirect
from resume.middleware import ResumeStorage

@override_settings(ROOT_URLCONF='resume.test_urls')
class ResumeTests(TestCase):

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()
        self.request.path = '/test/foo'
        self.request.session = {}
        self.request._resume_points = ResumeStorage(self.request)

    def tearDown(self):
        super().tearDown()
        del self.request

    def test_redirect_to_view(self):

        assert(len(self.request._resume_points) == 0)

        no_resume_point = self.request._resume_points.pop()
        assert(no_resume_point is None)

        response = resume_or_redirect(self.request, 'test-view')
        assert(response.status_code == 302)
        assert(response.url == '/test/view')

    def test_redirect_to_path(self):

        assert(len(self.request._resume_points) == 0)

        no_resume_point = self.request._resume_points.pop()
        assert(no_resume_point is None)

        response = resume_or_redirect(self.request, '/test/path')
        assert(response.status_code == 302)
        assert(response.url == '/test/path')

    def test_resume_point_storage(self):

        assert(len(self.request._resume_points) == 0)

        no_resume_point = self.request._resume_points.pop()
        assert(no_resume_point is None)

        set_resume(self.request)

        assert(len(self.request._resume_points) == 1)

        one_resume_point = self.request._resume_points.pop()
        assert(one_resume_point == '/test/foo')
        assert(len(self.request._resume_points) == 0)
