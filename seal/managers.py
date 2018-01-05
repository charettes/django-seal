from __future__ import unicode_literals

from django.db import models
from django.db.models.constants import LOOKUP_SEP
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

    def _unsealed_prefetch_lookup(self, prefetch_lookup, to_attr=None):
        """
        Turn a string prefetch lookup or a Prefetch instance without an
        explicit queryset into a Prefetch object with an explicit queryset
        to prevent the prefetching logic from accessing sealed related
        managers and triggering a SealedObject exception.
        """
        if isinstance(prefetch_lookup, string_types):
            parts = prefetch_lookup.split(LOOKUP_SEP, 1)
            if len(parts) > 1:
                head, tail = parts
            else:
                head, tail = parts[0], None
            queryset = self.model._meta.get_field(head).remote_field.model._default_manager.all()
            if tail:
                queryset = queryset.prefetch_related(tail)
            return models.Prefetch(head, queryset, to_attr=to_attr)
        elif isinstance(prefetch_lookup, models.Prefetch) and prefetch_lookup.queryset is None:
            return self._unsealed_prefetch_lookup(
                prefetch_lookup.prefetch_through,
                to_attr=prefetch_lookup.to_attr,
            )
        return prefetch_lookup

    def seal(self):
        clone = self._clone(_sealed=True)
        clone._prefetch_related_lookups = tuple(
            self._unsealed_prefetch_lookup(looukp) for looukp in clone._prefetch_related_lookups
        )
        if issubclass(clone._iterable_class, models.query.ModelIterable):
            clone._iterable_class = SealedModelIterable
        return clone
