from django.db import models

from .exceptions import SealedObject
from .managers import SealableQuerySet


class SealableModel(models.Model):
    objects = SealableQuerySet.as_manager()

    class Meta:
        abstract = True

    def refresh_from_db(self, using=None, fields=None):
        sealed = getattr(self._state, 'sealed', False)
        if sealed and fields is not None:
            fields = set(fields)
            deferred_fields = self.get_deferred_fields()
            if fields.intersection(deferred_fields):
                raise SealedObject('Cannot fetch deferred fields %s on a sealed object.' % ','.join(sorted(fields)))
        super(SealableModel, self).refresh_from_db(using=using, fields=fields)
