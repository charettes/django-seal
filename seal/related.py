from django.db.models.fields.related import (
    ForwardManyToOneDescriptor, ManyToManyDescriptor,
)
from django.utils.functional import cached_property

from .exceptions import SealedObject


class SealableForwardManyToOneDescriptor(ForwardManyToOneDescriptor):
    def get_object(self, instance):
        if getattr(instance._state, 'sealed', False):
            raise SealedObject('Cannot fetch related field %s on a sealed object.' % self.field.name)
        return super(SealableForwardManyToOneDescriptor, self).get_object(instance)


def create_sealable_related_manager(related_manager_cls, field):
    class SealableRelatedManager(related_manager_cls):
        def get_queryset(self):
            if getattr(self.instance._state, 'sealed', False):
                try:
                    return self.instance._prefetched_objects_cache[self.prefetch_cache_name]
                except (AttributeError, KeyError):
                    raise SealedObject('Cannot fetch many-to-many field %s on a sealed object.' % field.name)
            return super(SealableRelatedManager, self).get_queryset()
    return SealableRelatedManager


class SealableManyToManyDescriptor(ManyToManyDescriptor):
    @cached_property
    def related_manager_cls(self):
        related_manager_cls = super(SealableManyToManyDescriptor, self).related_manager_cls
        return create_sealable_related_manager(related_manager_cls, self.field)


def create_sealable_m2m_contribute_to_class(m2m):
    contribute_to_class = m2m.contribute_to_class

    def sealable_contribute_to_class(cls, *args, **kwargs):
        contribute_to_class(cls, *args, **kwargs)
        setattr(cls, m2m.name, SealableManyToManyDescriptor(m2m.remote_field, reverse=False))
    return sealable_contribute_to_class


sealable_accessor_classes = {
    ForwardManyToOneDescriptor: SealableForwardManyToOneDescriptor,
    ManyToManyDescriptor: SealableManyToManyDescriptor,
}
