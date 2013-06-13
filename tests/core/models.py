""" Models for tests. """

from django.db import models


class Pirate(models.Model):

    """ Mighty pirates. """

    name = models.CharField(max_length=50)
    captain = models.BooleanField(default=False)
    character = models.CharField(max_length=10, choices=(
        ('good', 'good'),
        ('evil', 'evil'),
        ('sorrow', 'sorrow'),
    ))

    def __unicode__(self):
        return self.name


class Island(models.Model):

    """ Magical islands. """

    title = models.CharField(max_length=50)


class Treasure(models.Model):

    """ Incrediable treasures. """

    created_at = models.DateTimeField(auto_now_add=True)
    pirate = models.ForeignKey(Pirate, null=True, blank=True)
    island = models.ForeignKey(Island)


class Boat(models.Model):

    """ Fastest boats. """

    title = models.CharField(max_length=50)
    pirate = models.ForeignKey(Pirate)
