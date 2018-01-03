from django.db import models
from seal.models import SealableModel


class SeaLion(SealableModel):
    height = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()
