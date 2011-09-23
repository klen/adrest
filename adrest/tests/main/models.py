#!/usr/bin/env python
# coding: utf-8

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy


class Author(models.Model):
    name = models.CharField(max_length=100,
            help_text = u"Имя автора")
    user = models.ForeignKey(User,
            help_text = gettext_lazy('User')
            )


class Publisher(models.Model):
    title = models.CharField(max_length=100)


class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author)
    price = models.PositiveIntegerField(default=0, blank=True)
    publisher = models.ForeignKey(Publisher, null=True, blank=True)


class Article(models.Model):
    title = models.CharField(max_length=100)
    book = models.ForeignKey(Book)
