from django.db import models


class Pirate(models.Model):
    name = models.CharField(max_length=50)


class Island(models.Model):
    title = models.CharField(max_length=50)


class Treasure(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    pirate = models.ForeignKey(Pirate, null=True, blank=True)
    island = models.ForeignKey(Island)


class Boat(models.Model):
    title = models.CharField(max_length=50)
    pirate = models.ForeignKey(Pirate)
