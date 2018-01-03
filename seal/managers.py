from __future__ import unicode_literals

from django.db import models


class SealedModelIterable(models.query.ModelIterable):
    def __iter__(self):
        objs = super(SealedModelIterable, self).__iter__()
        for obj in objs:
            obj._state.sealed = True
            yield obj


class SealableQuerySet(models.QuerySet):
    def __init__(self, *args, **kwargs):
        super(SealableQuerySet, self).__init__(*args, **kwargs)
        self._sealed = False
        self._iterable_class = SealedModelIterable

    def _clone(self, **kwargs):
        sealed = kwargs.pop('_sealed', False)
        clone = super(SealableQuerySet, self)._clone(**kwargs)
        clone._sealed = sealed
        return clone

    def seal(self):
        return self._clone(_sealed=True)
