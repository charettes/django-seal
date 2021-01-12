from functools import partial
from operator import attrgetter

import django
from django.db import models

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
        yield from walk_select_relateds(related_obj, nested_getters)


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
        yield from iterator


class SealableQuerySet(models.QuerySet):
    _base_manager_class = None

    def as_manager(cls):
        manager = cls._base_manager_class.from_queryset(cls)()
        manager._built_with_as_manager = True
        return manager
    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)

    def seal(self, iterable_class=SealedModelIterable):
        if self._fields is not None:
            raise TypeError('Cannot call seal() after .values() or .values_list()')
        if not issubclass(iterable_class, SealedModelIterable):
            raise TypeError('iterable_class %r is not a subclass of SealedModelIterable' % iterable_class)
        clone = self._clone()
        clone._iterable_class = iterable_class
        return clone
