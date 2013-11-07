from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200, help_text='Name of author')


class Book(models.Model):
    name = models.CharField(max_length=200, help_text='Name of book')
    author = models.ForeignKey(Author)
