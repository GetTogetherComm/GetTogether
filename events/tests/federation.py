from django.test import TestCase
from model_mommy import mommy

from ..models.events import Event, delete_event_searchable
from ..models.search import Searchable
from ..models.profiles import Category, Team

# Create your tests here.
class SearchableCreationTest(TestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_searchable_creation(self):
        searchables = Searchable.objects.all()
        assert(searchables.count() == 0)

        event = mommy.make(Event)
        event.save()

        searchables = Searchable.objects.all()
        assert(searchables.count() == 1)

    def test_searchable_update(self):
        event = mommy.make(Event, name="Old Title")
        event.save()

        searchables = Searchable.objects.all()
        assert(searchables.count() == 1)
        assert(searchables[0].event_title == "Old Title")

        event.name = "New Title"
        event.save()

        searchables = Searchable.objects.all()
        assert(searchables.count() == 1)
        assert(searchables[0].event_title == "New Title")

    def test_delete_searchable_with_event(self):
        searchables = Searchable.objects.all()
        assert(searchables.count() == 0)

        event = mommy.make(Event)
        event.save()

        searchables = Searchable.objects.all()
        assert(searchables.count() == 1)

        delete_event_searchable(event)
        event.delete()

        searchables = Searchable.objects.all()
        assert(searchables.count() == 0)

    def test_searchable_img_url(self):
        category = mommy.make(Category, img_url='/test/foo.png')
        team = mommy.make(Team, category=category)
        event = mommy.make(Event, team=team)
        event.save()

        searchables = Searchable.objects.all()
        assert(searchables.count() == 1)
        assert(searchables[0].img_url == 'https://example.com/test/foo.png')

        category.img_url = 'http://test.com/img/bar.png'
        category.save()
        searchables = Searchable.objects.all()
        assert(searchables.count() == 1)
        assert(searchables[0].img_url == 'https://example.com/test/foo.png')

        event.save()
        searchables = Searchable.objects.all()
        assert(searchables.count() == 1)
        assert(searchables[0].img_url == 'http://test.com/img/bar.png')
