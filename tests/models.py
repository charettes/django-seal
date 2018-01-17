from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation,
)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from seal.models import SealableModel


class Nickname(SealableModel):
    name = models.CharField(max_length=24)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


class Location(SealableModel):
    latitude = models.FloatField()
    longitude = models.FloatField()


class Leak(models.Model):
    description = models.TextField()


class SeaLion(SealableModel):
    height = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()
    location = models.ForeignKey(Location, models.CASCADE, null=True, related_name='visitors')
    previous_locations = models.ManyToManyField(Location, related_name='previous_visitors')
    leak = models.ForeignKey(Leak, models.CASCADE, null=True)


class SeaLionAbstractSubclass(SeaLion):
    class Meta:
        abstract = True


class SealionProxy(SeaLion):
    class Meta:
        proxy = True


class GreatSeaLion(SeaLion):
    pass


class SeaGull(SealableModel):
    sealion = models.OneToOneField(SeaLion, models.CASCADE, related_name='gull')
    nicknames = GenericRelation('Nickname')
