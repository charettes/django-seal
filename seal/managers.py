from __future__ import unicode_literals

from django.db import models
from django.utils.six import string_types


class SealedModelIterable(models.query.ModelIterable):
    def __iter__(self):
        objs = super(SealedModelIterable, self).__iter__()
        for obj in objs:
            obj.seal()
            yield obj


class SealableQuerySet(models.QuerySet):
    def __init__(self, *args, **kwargs):
        self._sealed = False
        super(SealableQuerySet, self).__init__(*args, **kwargs)

    def _clone(self, **kwargs):
        sealed = kwargs.pop('_sealed', False)
        clone = super(SealableQuerySet, self)._clone(**kwargs)
        clone._sealed = sealed
        return clone

    def seal(self):
        clone = self._clone(_sealed=True)
        clone._prefetch_related_lookups = tuple(
            models.Prefetch(
                lookup,
                self.model._meta.get_field(lookup).remote_field.model._default_manager.all(),
            ) if isinstance(lookup, string_types) else lookup
            for lookup in clone._prefetch_related_lookups
        )
        if issubclass(clone._iterable_class, models.query.ModelIterable):
            clone._iterable_class = SealedModelIterable
        return clone
