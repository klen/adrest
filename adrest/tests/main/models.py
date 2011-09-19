#!/usr/bin/env python
# coding: utf-8

from django.contrib.auth.models import User
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100,
            help_text = u"Имя автора")
    user = models.ForeignKey(User)


class Publisher(models.Model):
    title = models.CharField(max_length=100)


class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author)
    publisher = models.ForeignKey(Publisher, null=True)


class Article(models.Model):
    title = models.CharField(max_length=100)
    book = models.ForeignKey(Book)
