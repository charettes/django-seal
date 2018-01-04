from django.db.models.fields.related import (
    ForwardManyToOneDescriptor, ForwardOneToOneDescriptor,
    ManyToManyDescriptor, ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from django.utils.functional import cached_property

from .exceptions import SealedObject


def create_sealable_related_manager(related_manager_cls, field_name):
    class SealableRelatedManager(related_manager_cls):
        def get_queryset(self):
            if getattr(self.instance._state, 'sealed', False):
                try:
                    prefetch_cache_name = self.prefetch_cache_name
                except AttributeError:
                    prefetch_cache_name = self.field.related_query_name()
                try:
                    return self.instance._prefetched_objects_cache[prefetch_cache_name]
                except (AttributeError, KeyError):
                    raise SealedObject('Cannot fetch many-to-many field %s on a sealed object.' % field_name)
            return super(SealableRelatedManager, self).get_queryset()
    return SealableRelatedManager


class SealableReverseManyToOneDescriptor(ReverseManyToOneDescriptor):
    @cached_property
    def related_manager_cls(self):
        related_manager_cls = super(SealableReverseManyToOneDescriptor, self).related_manager_cls
        return create_sealable_related_manager(related_manager_cls, self.rel.name)


class SealableForwardManyToOneDescriptor(ForwardManyToOneDescriptor):
    def get_object(self, instance):
        if getattr(instance._state, 'sealed', False):
            raise SealedObject('Cannot fetch related field %s on a sealed object.' % self.field.name)
        return super(SealableForwardManyToOneDescriptor, self).get_object(instance)


class SealableReverseOneToOneDescriptor(ReverseOneToOneDescriptor):
    def get_queryset(self, instance, **hints):
        if getattr(instance._state, 'sealed', False):
            raise SealedObject('Cannot fetch related field %s on a sealed object.' % self.related.name)
        return super(SealableReverseOneToOneDescriptor, self).get_queryset(instance=instance, **hints)


class SealableForwardOneToOneDescriptor(ForwardOneToOneDescriptor):
    def get_object(self, instance):
        if getattr(instance._state, 'sealed', False):
            if self.field.remote_field.parent_link:
                deferred = instance.get_deferred_fields()
                # Because it's a parent link, all the data is available in the
                # instance, so populate the parent model with this data.
                rel_model = self.field.remote_field.model
                fields = {field.attname for field in rel_model._meta.concrete_fields}

                # If any of the related model's fields are deferred, prevent
                # the query from being performed.
                if any(field in fields for field in deferred):
                    raise SealedObject('Cannot fetch related field %s on a sealed object.' % self.field.name)
        return super(SealableForwardOneToOneDescriptor, self).get_object(instance)


class SealableManyToManyDescriptor(ManyToManyDescriptor):
    @cached_property
    def related_manager_cls(self):
        related_manager_cls = super(SealableManyToManyDescriptor, self).related_manager_cls
        return create_sealable_related_manager(related_manager_cls, self.field.name)


def create_sealable_m2m_contribute_to_class(m2m):
    contribute_to_class = m2m.contribute_to_class

    def sealable_contribute_to_class(cls, *args, **kwargs):
        contribute_to_class(cls, *args, **kwargs)
        setattr(cls, m2m.name, SealableManyToManyDescriptor(m2m.remote_field, reverse=False))
    return sealable_contribute_to_class


sealable_accessor_classes = {
    ReverseManyToOneDescriptor: SealableReverseManyToOneDescriptor,
    ForwardManyToOneDescriptor: SealableForwardManyToOneDescriptor,
    ReverseOneToOneDescriptor: SealableReverseOneToOneDescriptor,
    ForwardOneToOneDescriptor: SealableForwardOneToOneDescriptor,
    ManyToManyDescriptor: SealableManyToManyDescriptor,
}
