from __future__ import unicode_literals

from functools import partial
from operator import attrgetter

from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.utils.six import string_types


def get_select_related_getters(lookups):
    """Turn a select_related dict structure into a tree of attribute getters"""
    for lookup, nested_lookups in lookups.items():
        yield (attrgetter(lookup), tuple(get_select_related_getters(nested_lookups)))


def walk_select_relateds(obj, getters):
    """Walk select related of obj from getters."""
    for getter, nested_getters in getters:
        related_obj = getter(obj)
        yield related_obj
        # yield from walk_select_relateds(related_obj, nested_getters)
        for nested_related_obj in walk_select_relateds(related_obj, nested_getters):
            yield nested_related_obj


class SealedModelIterable(models.query.ModelIterable):
    def _sealed_iterator(self):
        """Iterate over objects and seal them."""
        objs = super(SealedModelIterable, self).__iter__()
        for obj in objs:
            obj.seal()
            yield obj

    def _sealed_related_iterator(self, related_walker):
        """Iterate over objects and seal them and their select related."""
        for obj in self._sealed_iterator():
            for related_obj in related_walker(obj):
                related_obj.seal()
            yield obj

    def __iter__(self):
        select_related = self.queryset.query.select_related
        if select_related:
            select_related_getters = tuple(get_select_related_getters(self.queryset.query.select_related))
            related_walker = partial(walk_select_relateds, getters=select_related_getters)
            iterator = self._sealed_related_iterator(related_walker)
        else:
            iterator = self._sealed_iterator()
        # yield from iterator
        for obj in iterator:
            yield obj


class SealableQuerySet(models.QuerySet):
    _sealed = False

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
            remote_field = self.model._meta.get_field(head).remote_field
            if remote_field:
                queryset = remote_field.model._default_manager.all()
                if tail:
                    queryset = queryset.prefetch_related(tail)
                return models.Prefetch(head, queryset, to_attr=to_attr)
            # Some private fields such as GenericForeignKey don't have a remote
            # field as reverse relationships have to be explicit defined using
            # GenericRelation instances.
            return prefetch_lookup
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
