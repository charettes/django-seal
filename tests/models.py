from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation,
)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import force_text

from seal.models import SealableModel

try:
    from django.utils.encoding import python_2_unicode_compatible
except ImportError:
    def python_2_unicode_compatible(cls):
        return cls


class Nickname(SealableModel):
    name = models.CharField(max_length=24)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


class Climate(SealableModel):
    temperature = models.IntegerField()


class Location(SealableModel):
    latitude = models.FloatField()
    longitude = models.FloatField()
    climates = models.ManyToManyField(Climate, blank=True, related_name='locations')


class Leak(models.Model):
    description = models.TextField()


@python_2_unicode_compatible
class SeaLion(SealableModel):
    height = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()
    location = models.ForeignKey(Location, models.CASCADE, null=True, related_name='visitors')
    previous_locations = models.ManyToManyField(Location, related_name='previous_visitors')
    leak = models.ForeignKey(Leak, models.CASCADE, null=True, related_name='sealion_just_friends')
    leak_o2o = models.OneToOneField(Leak, models.CASCADE, null=True, related_name='sealion_soulmate')

    def __str__(self):
        return force_text(repr(self))

    def __repr__(self):
        return str('<SeaLion %s %s %s>' % (self.id, self.height, self.weight))


class SeaLionAbstractSubclass(SeaLion):
    class Meta:
        abstract = True


class SealionProxy(SeaLion):
    class Meta:
        proxy = True


class GreatSeaLion(SeaLion):
    pass


class SeaGull(SealableModel):
    sealion = models.OneToOneField(SeaLion, models.CASCADE, null=True, related_name='gull')
    nicknames = GenericRelation('Nickname')
