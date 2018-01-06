from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation,
)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from seal.managers import SealableQuerySet
from seal.models import SealableModel


class Nickname(SealableModel):
    name = models.CharField(max_length=24)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


class Location(SealableModel):
    latitude = models.FloatField()
    longitude = models.FloatField()

    nicknames = GenericRelation(Nickname, related_query_name='locations')


class SeaLion(SealableModel):
    height = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()
    location = models.ForeignKey(Location, models.CASCADE, null=True, related_name='visitors')
    previous_locations = models.ManyToManyField(Location, related_name='previous_visitors')

    nicknames = GenericRelation(Nickname, related_query_name='sealions')


class GreatSeaLion(SeaLion):
    # TODO: add support for auto-generated o2os parent_link and non-parent link o2o.
    sealion_ptr = models.OneToOneField(SeaLion, models.CASCADE, parent_link=True, primary_key=True)


class Koala(models.Model):
    height = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()

    objects = SealableQuerySet.as_manager()
