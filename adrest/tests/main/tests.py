from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase, Client

from api import api
from resourses import AuthorResource, BookResource, ArticleResource, SomeOtherResource
from models import Author


class MetaTest(TestCase):

    def test_meta(self):
        self.assertTrue(AuthorResource._meta)
        self.assertTrue(AuthorResource._meta.parents is not None)
        self.assertTrue(AuthorResource._meta.name is not None)
        self.assertTrue(AuthorResource._meta.urlname is not None)
        self.assertTrue(AuthorResource._meta.urlregex is not None)

    def test_meta_parents(self):
        self.assertEqual(AuthorResource._meta.parents, [])
        self.assertEqual(BookResource._meta.parents, [ AuthorResource ])
        self.assertEqual(ArticleResource._meta.parents, [ AuthorResource, BookResource ])

    def test_meta_name(self):
        self.assertEqual(AuthorResource._meta.name, 'author')
        self.assertEqual(BookResource._meta.name, 'book')
        self.assertEqual(SomeOtherResource._meta.name, 'someother')

    def test_meta_urlname(self):
        self.assertEqual(AuthorResource._meta.urlname, 'author')
        self.assertEqual(BookResource._meta.urlname, 'author-test-book')
        self.assertEqual(ArticleResource._meta.urlname, 'author-test-book-article')
        self.assertEqual(SomeOtherResource._meta.urlname, 'author-device-someother')

    def test_meta_urlregex(self):
        self.assertEqual(AuthorResource._meta.urlregex, 'author/(?:(?P<author>[^/]+)/)?$')
        self.assertEqual(BookResource._meta.urlregex, 'author/(?P<author>[^/]+)/test/book/(?:(?P<book>[^/]+)/)?$')
        self.assertEqual(ArticleResource._meta.urlregex, 'author/(?P<author>[^/]+)/book/(?P<book>[^/]+)/article/(?:(?P<article>[^/]+)/)?$')
        self.assertEqual(SomeOtherResource._meta.urlregex, 'author/(?P<author>[^/]+)/device/(?P<device>[^/]+)/someother/(?:(?P<someother>[^/]+)/)?$')


class ApiTest(TestCase):

    def test_api(self):
        self.assertTrue(api.version)
        self.assertEqual(str(api), "1.0.0")
        self.assertTrue(api.urls)
        urlpattern = api.urls[1]
        self.assertEqual(urlpattern.name, "api-%s-%s" % (str(api), AuthorResource._meta.name ))


class AdrestTest(TestCase):

    def setUp(self):
        self.client = Client()
        user = User.objects.create(username='test')
        Author.objects.create(name='John', user=user)

    def test_methods(self):
        uri = reverse("api-%s-%s" % (str(api), AuthorResource._meta.urlname))
        self.assertEqual(uri, '/1.0.0/author/')
        response = self.client.get(uri)
        self.assertContains(response, 'true')

        response = self.client.post(uri)
        self.assertContains(response, 'false', status_code=405)
