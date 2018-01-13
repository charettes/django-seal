from django.db import models
from seal.managers import SealableQuerySet
from seal.models import SealableModel


class Location(SealableModel):
    latitude = models.FloatField()
    longitude = models.FloatField()


class SeaLion(SealableModel):
    height = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()
    location = models.ForeignKey(Location, models.CASCADE, null=True, related_name='visitors')
    previous_locations = models.ManyToManyField(Location, related_name='previous_visitors')


class GreatSeaLion(SeaLion):
    # TODO: add support for auto-generated o2os parent_link and non-parent link o2o.
    sealion_ptr = models.OneToOneField(SeaLion, models.CASCADE, parent_link=True, primary_key=True)


class Koala(models.Model):
    height = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()

    objects = SealableQuerySet.as_manager()


class Gull(SealableModel):
    sealion = models.OneToOneField(SeaLion, models.CASCADE, related_name='gull')
