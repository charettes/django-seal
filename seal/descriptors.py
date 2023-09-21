import warnings
from functools import lru_cache

from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    ReverseGenericManyToOneDescriptor,
)
from django.db.models import QuerySet
from django.db.models.fields import DeferredAttribute
from django.db.models.fields.related import (
    ForeignKeyDeferredAttribute,
    ForwardManyToOneDescriptor,
    ForwardOneToOneDescriptor,
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from django.utils.functional import cached_property

from . import models
from .exceptions import UnsealedAttributeAccess
from .query import SealableQuerySet


def _bare_repr(instance):
    return "<%s instance>" % instance.__class__.__name__


class _SealedRelatedQuerySet(QuerySet):
    """
    QuerySet that prevents any fetching from taking place on its current form.

    As soon as the query is cloned it gets unsealed.
    """

    def _clone(self, *args, **kwargs):
        clone = super()._clone(*args, **kwargs)
        clone.__class__ = self._unsealed_class
        return clone

    def __getitem__(self, item):
        if self._result_cache is None:
            warnings.warn(
                self._sealed_warning, category=UnsealedAttributeAccess, stacklevel=2
            )
        return super().__getitem__(item)

    def _fetch_all(self):
        if self._result_cache is None:
            warnings.warn(
                self._sealed_warning, category=UnsealedAttributeAccess, stacklevel=3
            )
        super()._fetch_all()

    def __reduce__(self):
        return (
            _unpickle_sealed_related_queryset,
            (self._unsealed_class,),
            self.__getstate__(),
        )


class SealedPrefetchMixin(object):
    def _get_default_prefetch_queryset(self):
        return self.get_queryset()

    def get_prefetch_queryset(self, instances, queryset=None):
        if queryset is None:
            queryset = self._get_default_prefetch_queryset()
        if getattr(instances[0]._state, "sealed", False) and isinstance(
            queryset, SealableQuerySet
        ):
            queryset = queryset.seal()
        return super().get_prefetch_queryset(instances, queryset)

    def get_prefetch_querysets(self, instances, querysets=None):
        if querysets is None:
            querysets = [self._get_default_prefetch_queryset()]
        if getattr(instances[0]._state, "sealed", False):
            querysets = [
                queryset.seal() if isinstance(queryset, SealableQuerySet) else queryset
                for queryset in querysets
            ]
        return super().get_prefetch_querysets(instances, querysets)


@lru_cache(maxsize=100)
def _sealed_related_queryset_type_factory(queryset_cls):
    if issubclass(queryset_cls, _SealedRelatedQuerySet):
        return queryset_cls
    return type(
        f"Sealed{queryset_cls.__name__}",
        (_SealedRelatedQuerySet, queryset_cls),
        {
            "_unsealed_class": queryset_cls,
        },
    )


def _unpickle_sealed_related_queryset(queryset_cls):
    cls = _sealed_related_queryset_type_factory(queryset_cls)
    return cls.__new__(cls)


def seal_related_queryset(queryset, warning):
    """
    Seal a related queryset to prevent it from being fetched directly.
    """
    queryset.__class__ = _sealed_related_queryset_type_factory(queryset.__class__)
    queryset._sealed_warning = warning
    return queryset


def create_sealable_related_manager(related_manager_cls, field_name):
    class SealableRelatedManager(SealedPrefetchMixin, related_manager_cls):
        def _get_default_prefetch_queryset(self):
            # By-pass `related_manager_cls.get_queryset()` as that's the default
            # for dynamically created manager's `get_prefetch_queryset` when
            # no `queryset` is specified.
            return super(related_manager_cls, self).get_queryset()

        def get_queryset(self):
            if getattr(self.instance._state, "sealed", False):
                try:
                    prefetch_cache_name = self.prefetch_cache_name
                except AttributeError:
                    prefetch_cache_name = self.field.related_query_name()
                try:
                    return self.instance._prefetched_objects_cache[prefetch_cache_name]
                except (AttributeError, KeyError):
                    warning = (
                        'Attempt to fetch many-to-many field "%s" on sealed %s.'
                        % (
                            field_name,
                            _bare_repr(self.instance),
                        )
                    )
                    related_queryset = super().get_queryset()
                    return seal_related_queryset(related_queryset, warning)
            return super().get_queryset()

    return SealableRelatedManager


class SealableDeferredAttribute(DeferredAttribute):
    @cached_property
    def field_name(self):
        return self.field.attname

    def _check_parent_chain(self, instance, field_name=None):
        super()._check_parent_chain(instance)

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        if (
            getattr(instance._state, "sealed", False)
            and instance.__dict__.get(self.field_name, self) is self
            and self._check_parent_chain(instance, self.field_name) is None
        ):
            message = 'Attempt to fetch deferred field "%s" on sealed %s.' % (
                self.field_name,
                _bare_repr(instance),
            )
            warnings.warn(message, category=UnsealedAttributeAccess, stacklevel=2)
        return super().__get__(instance, cls)


class SealableForwardOneToOneDescriptor(SealedPrefetchMixin, ForwardOneToOneDescriptor):
    def get_object(self, instance):
        sealed = getattr(instance._state, "sealed", False)
        if sealed:
            rel_model = self.field.remote_field.model
            if self.field.remote_field.parent_link and issubclass(
                rel_model, models.SealableModel
            ):
                deferred = instance.get_deferred_fields()
                # Because it's a parent link, all the data is available in the
                # instance, so populate the parent model with this data.

                fields = {field.attname for field in rel_model._meta.concrete_fields}

                # If any of the related model's fields are deferred, prevent
                # the query from being performed.
                if any(field in fields for field in deferred):
                    message = 'Attempt to fetch related field "%s" on sealed %s.' % (
                        self.field.name,
                        _bare_repr(instance),
                    )
                    warnings.warn(
                        message, category=UnsealedAttributeAccess, stacklevel=3
                    )
                else:
                    # When none of the fields inherited from the parent link
                    # are deferred ForwardOneToOneDescriptor.get_object() simply
                    # create an in-memory object from the existing field values.
                    # Make sure this in-memory instance is sealed as well.
                    obj = super().get_object(instance)
                    obj.seal()
                    return obj
            else:
                message = 'Attempt to fetch related field "%s" on sealed %s.' % (
                    self.field.name,
                    _bare_repr(instance),
                )
                warnings.warn(message, category=UnsealedAttributeAccess, stacklevel=3)
        return super().get_object(instance)


class SealableReverseOneToOneDescriptor(SealedPrefetchMixin, ReverseOneToOneDescriptor):
    def get_queryset(self, **hints):
        instance = hints.get("instance")
        if instance and getattr(instance._state, "sealed", False):
            message = 'Attempt to fetch related field "%s" on sealed %s.' % (
                self.related.name,
                _bare_repr(instance),
            )
            warnings.warn(message, category=UnsealedAttributeAccess, stacklevel=3)
        return super().get_queryset(**hints)


class SealableForwardManyToOneDescriptor(ForwardManyToOneDescriptor):
    def get_object(self, instance):
        if getattr(instance._state, "sealed", False):
            message = 'Attempt to fetch related field "%s" on sealed %s.' % (
                self.field.name,
                _bare_repr(instance),
            )
            warnings.warn(message, category=UnsealedAttributeAccess, stacklevel=3)
        return super().get_object(instance)


class SealableReverseManyToOneDescriptor(ReverseManyToOneDescriptor):
    @cached_property
    def related_manager_cls(self):
        related_manager_cls = super().related_manager_cls
        return create_sealable_related_manager(related_manager_cls, self.rel.name)


class SealableManyToManyDescriptor(ManyToManyDescriptor):
    @cached_property
    def related_manager_cls(self):
        related_manager_cls = super().related_manager_cls
        field_name = self.rel.name if self.reverse else self.field.name
        return create_sealable_related_manager(related_manager_cls, field_name)


class SealableGenericForeignKey(GenericForeignKey):
    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        if getattr(instance._state, "sealed", False) and not self.is_cached(instance):
            message = 'Attempt to fetch related field "%s" on sealed %s.' % (
                self.name,
                _bare_repr(instance),
            )
            warnings.warn(message, category=UnsealedAttributeAccess, stacklevel=2)

        return super().__get__(instance, cls=cls)


class SealableReverseGenericManyToOneDescriptor(ReverseGenericManyToOneDescriptor):
    @cached_property
    def related_manager_cls(self):
        related_manager_cls = super().related_manager_cls
        return create_sealable_related_manager(related_manager_cls, self.field.name)


class SealableForeignKeyDeferredAttribute(
    SealableDeferredAttribute, ForeignKeyDeferredAttribute
):
    pass


sealable_descriptor_classes = {
    DeferredAttribute: SealableDeferredAttribute,
    ForwardOneToOneDescriptor: SealableForwardOneToOneDescriptor,
    ReverseOneToOneDescriptor: SealableReverseOneToOneDescriptor,
    ForwardManyToOneDescriptor: SealableForwardManyToOneDescriptor,
    ReverseManyToOneDescriptor: SealableReverseManyToOneDescriptor,
    ManyToManyDescriptor: SealableManyToManyDescriptor,
    GenericForeignKey: SealableGenericForeignKey,
    ReverseGenericManyToOneDescriptor: SealableReverseGenericManyToOneDescriptor,
    ForeignKeyDeferredAttribute: SealableForeignKeyDeferredAttribute,
}
