from django.db import models
from django.utils.six import with_metaclass

from .exceptions import SealedObject
from .managers import SealableQuerySet
from .related import (
    create_sealable_m2m_contribute_to_class,
    create_sealable_m2m_contribute_to_related_class, sealable_accessor_classes,
)


class SealaleModelBase(models.base.ModelBase):
    def __new__(cls, name, bases, attrs):
        meta = attrs.get('Meta')
        abstract = meta and getattr(meta, 'abstract', False)
        proxy = meta and getattr(meta, 'proxy', False)
        if not (abstract or proxy):
            # Turn implicit one-to-one parent link into explicit ones in order
            # to replace their related accessors below.
            concrete_bases = (
                base for base in bases
                if isinstance(base, models.base.ModelBase) and not base._meta.abstract
            )
            parent_links = {
                models.utils.make_model_tuple(value.remote_field.model) for value in attrs.values()
                if isinstance(value, models.OneToOneField) and value.remote_field.parent_link
            }
            for base in concrete_bases:
                if models.utils.make_model_tuple(base) in parent_links:
                    continue
                parent_link_name = '%s_ptr' % base._meta.model_name
                attrs[parent_link_name] = models.OneToOneField(
                    base,
                    on_delete=models.CASCADE,
                    name=parent_link_name,
                    auto_created=True,
                    parent_link=True,
                )
        for attr, value in attrs.items():
            if isinstance(value, models.ForeignObject):
                sealable_accessor_class = sealable_accessor_classes.get(value.related_accessor_class)
                if sealable_accessor_class:
                    value.related_accessor_class = sealable_accessor_class
                sealable_forward_accessor_class = sealable_accessor_classes.get(value.forward_related_accessor_class)
                if sealable_forward_accessor_class:
                    value.forward_related_accessor_class = sealable_forward_accessor_class
            elif isinstance(value, models.ManyToManyField):
                # ManyToManyField doesn't declare a class level attribute for
                # its forward and reverse accessor class. We must provide
                # override contribute_to_class/contribute_to_related_class to
                # work around it.
                value.contribute_to_class = create_sealable_m2m_contribute_to_class(value)
                value.contribute_to_related_class = create_sealable_m2m_contribute_to_related_class(value)
        return super(SealaleModelBase, cls).__new__(cls, name, bases, attrs)


class SealableModel(with_metaclass(SealaleModelBase, models.Model)):
    objects = SealableQuerySet.as_manager()

    def seal(self):
        self._state.sealed = True

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
