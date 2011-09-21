from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase, Client, RequestFactory
from adrest.models import Access
from adrest.utils import serializer, paginator

from .api import api
from .resourses import AuthorResource, BookPrefixResource, ArticleResource, SomeOtherResource, BookResource
from .models import Author, Book, Article


class MetaTest(TestCase):

    def test_meta(self):
        self.assertTrue(AuthorResource.meta)
        self.assertTrue(AuthorResource.meta.parents is not None)
        self.assertTrue(AuthorResource.meta.models is not None)
        self.assertTrue(AuthorResource.meta.name is not None)
        self.assertTrue(AuthorResource.meta.urlname is not None)
        self.assertTrue(AuthorResource.meta.urlregex is not None)

    def test_meta_parents(self):
        self.assertEqual(AuthorResource.meta.parents, [])
        self.assertEqual(BookPrefixResource.meta.parents, [ AuthorResource ])
        self.assertEqual(ArticleResource.meta.parents, [ AuthorResource, BookPrefixResource ])

    def test_meta_models(self):
        self.assertEqual(AuthorResource.meta.models, [ Author ])
        self.assertEqual(BookPrefixResource.meta.models, [ Author, Book ])
        self.assertEqual(ArticleResource.meta.models, [ Author, Book, Article ])

    def test_meta_name(self):
        self.assertEqual(AuthorResource.meta.name, 'author')
        self.assertEqual(BookPrefixResource.meta.name, 'book')
        self.assertEqual(SomeOtherResource.meta.name, 'someother')

    def test_meta_urlname(self):
        self.assertEqual(AuthorResource.meta.urlname, 'author')
        self.assertEqual(BookResource.meta.urlname, 'author-book')
        self.assertEqual(BookPrefixResource.meta.urlname, 'author-test-book')
        self.assertEqual(ArticleResource.meta.urlname, 'author-test-book-article')
        self.assertEqual(SomeOtherResource.meta.urlname, 'author-device-someother')

    def test_meta_urlregex(self):
        self.assertEqual(AuthorResource.meta.urlregex, 'author/(?:(?P<author>[^/]+)/)?$')
        self.assertEqual(BookPrefixResource.meta.urlregex, 'author/(?P<author>[^/]+)/test/book/(?:(?P<book>[^/]+)/)?$')
        self.assertEqual(ArticleResource.meta.urlregex, 'author/(?P<author>[^/]+)/book/(?P<book>[^/]+)/article/(?:(?P<article>[^/]+)/)?$')
        self.assertEqual(SomeOtherResource.meta.urlregex, 'author/(?P<author>[^/]+)/device/(?P<device>[^/]+)/someother/(?:(?P<someother>[^/]+)/)?$')


class ApiTest(TestCase):

    def test_api(self):
        self.assertTrue(api.version)
        self.assertEqual(str(api), "1.0.0")
        self.assertTrue(api.urls)
        urlpattern = api.urls[1]
        self.assertEqual(urlpattern.name, "api-%s-%s" % (str(api), AuthorResource.meta.name ))


class AdrestTest(TestCase):

    def setUp(self):
        self.client = Client()
        user = User.objects.create(username='test')
        self.author = Author.objects.create(name='John', user=user)
        self.book = Book.objects.create(author=self.author, title='test',)

    def test_methods(self):
        uri = reverse("api-%s-%s" % (str(api), AuthorResource.meta.urlname))
        self.assertEqual(uri, '/1.0.0/author/')
        response = self.client.get(uri)
        self.assertContains(response, 'true')

        response = self.client.post(uri)
        self.assertContains(response, 'false', status_code=405)

    def test_owner(self):
        uri = reverse("api-%s-%s" % (str(api), ArticleResource.meta.urlname), kwargs=dict(author=self.author.pk, book=self.book.pk))
        response = self.client.get(uri)
        self.assertContains(response, 'true')

    def test_log(self):
        uri = reverse("api-%s-%s" % (str(api), ArticleResource.meta.urlname), kwargs=dict(author=self.author.pk, book=self.book.pk))
        self.client.get(uri)
        access = Access.objects.get()
        self.assertEqual(access.uri, uri)


class AdrestMapTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_methods(self):
        uri = reverse("api-%s-apimap" % str(api))
        response = self.client.get(uri)
        self.assertContains(response, 'MAP')

        response = self.client.get(uri, HTTP_ACCEPT="application/json")
        self.assertNotContains(response, 'MAP')


class SerializerTest(TestCase):

    def setUp(self):
        self.rf = RequestFactory()
        for i in range(1, 100):
            user = User.objects.create(username='test%s' % i)
            self.author = Author.objects.create(name='John %s' % i, user=user)
            self.book = Book.objects.create(author=self.author, title='test %s' % i)

    def test_json(self):
        authors = Author.objects.all()
        test = serializer.json_dumps(authors)
        self.assertTrue("main.author" in test)
        request = self.rf.get("/")
        pg = paginator.Paginator(request, authors, 10)
        test = serializer.json_dumps(pg)
        self.assertTrue("count" in test)
        books = Book.objects.all()
        test = serializer.json_dumps(books)
        self.assertTrue("author" in test)
        self.assertFalse("publisher" in test)

    def test_xml(self):
        authors = Author.objects.all()
        test = serializer.xml_dumps(authors)
        self.assertTrue("author" in test)
