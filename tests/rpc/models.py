from django.db import models


class Test(models.Model):
    name = models.CharField(max_length=100)


class Root(models.Model):
    name = models.CharField(max_length=100)


class Child(models.Model):
    name = models.CharField(max_length=100)
    odd = models.IntegerField(default=0)
    root = models.ForeignKey(Root)
