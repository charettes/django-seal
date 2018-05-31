from __future__ import unicode_literals

from functools import partial
from operator import attrgetter

import django
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.utils.six import string_types

if django.VERSION >= (2, 0):
    cached_value_getter = attrgetter('get_cached_value')
else:
    def cached_value_getter(field):
        return attrgetter(field.get_cache_name())


def get_select_related_getters(lookups, opts):
    """Turn a select_related dict structure into a tree of attribute getters"""
    for lookup, nested_lookups in lookups.items():
        field = opts.get_field(lookup)
        lookup_opts = field.related_model._meta
        yield (cached_value_getter(field), tuple(get_select_related_getters(nested_lookups, lookup_opts)))


def walk_select_relateds(obj, getters):
    """Walk select related of obj from getters."""
    for getter, nested_getters in getters:
        related_obj = getter(obj)
        if related_obj is None:
            # We don't need to seal a None relation or any of its children.
            continue
        yield related_obj
        # yield from walk_select_relateds(related_obj, nested_getters)
        for nested_related_obj in walk_select_relateds(related_obj, nested_getters):
            yield nested_related_obj


class SealedModelIterable(models.query.ModelIterable):
    def _sealed_iterator(self):
        """Iterate over objects and seal them."""
        objs = super(SealedModelIterable, self).__iter__()
        for obj in objs:
            obj._state.sealed = True
            yield obj

    def _sealed_related_iterator(self, related_walker):
        """Iterate over objects and seal them and their select related."""
        for obj in self._sealed_iterator():
            for related_obj in related_walker(obj):
                related_obj._state.sealed = True
            yield obj

    def __iter__(self):
        select_related = self.queryset.query.select_related
        if select_related:
            opts = self.queryset.model._meta
            select_related_getters = tuple(get_select_related_getters(self.queryset.query.select_related, opts))
            related_walker = partial(walk_select_relateds, getters=select_related_getters)
            iterator = self._sealed_related_iterator(related_walker)
        else:
            iterator = self._sealed_iterator()
        # yield from iterator
        for obj in iterator:
            yield obj


class SealableQuerySet(models.QuerySet):
    _base_manager_class = None
    _sealed = False

    def as_manager(cls):
        manager = cls._base_manager_class.from_queryset(cls)()
        manager._built_with_as_manager = True
        return manager
    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)

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
            parts = prefetch_lookup.split(LOOKUP_SEP)
            opts = self.model._meta
            select_related = self.query.select_related or {}
            # Walk to the first non-select_related part of the prefetch lookup.
            for index, part in enumerate(parts, start=1):
                related_model = opts.get_field(part).related_model
                try:
                    select_related = select_related[part]
                except KeyError:
                    break
                opts = related_model._meta
            head, tail = LOOKUP_SEP.join(parts[:index]), LOOKUP_SEP.join(parts[index:])
            if related_model:
                queryset = related_model._default_manager.all()
                if tail:
                    queryset = queryset.prefetch_related(tail)
                if isinstance(queryset, SealableQuerySet):
                    queryset = queryset.seal()
                return models.Prefetch(head, queryset, to_attr=to_attr)
            # Some private fields such as GenericForeignKey don't have a remote
            # field as reverse relationships have to be explicit defined using
            # GenericRelation instances.
            return prefetch_lookup
        elif isinstance(prefetch_lookup, models.Prefetch):
            if prefetch_lookup.queryset is None:
                return self._unsealed_prefetch_lookup(
                    prefetch_lookup.prefetch_through,
                    to_attr=prefetch_lookup.to_attr,
                )
            elif isinstance(prefetch_lookup.queryset, SealableQuerySet):
                prefetch_lookup.queryset = prefetch_lookup.queryset.seal()
        return prefetch_lookup

    def seal(self, iterable_class=SealedModelIterable):
        if self._fields is not None:
            raise TypeError('Cannot call seal() after .values() or .values_list()')
        if not issubclass(iterable_class, SealedModelIterable):
            raise TypeError('iterable_class %r is not a subclass of SealedModelIterable' % iterable_class)
        clone = self._clone(_sealed=True)
        clone._iterable_class = iterable_class
        clone._prefetch_related_lookups = tuple(
            self._unsealed_prefetch_lookup(looukp) for looukp in clone._prefetch_related_lookups
        )
        return clone

    def select_related(self, *fields):
        if self._sealed:
            raise TypeError('Cannot call select_related() after .seal()')
        return super(SealableQuerySet, self).select_related(*fields)

    def prefetch_related(self, *lookups):
        if self._sealed:
            raise TypeError('Cannot call prefetch_related() after .seal()')
        return super(SealableQuerySet, self).prefetch_related(*lookups)
