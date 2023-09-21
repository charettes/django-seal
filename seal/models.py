from django.core import checks
from django.db import models
from django.db.models.fields.related import lazy_related_operation
from django.dispatch import receiver

from . import descriptors
from .query import SealableQuerySet


class BaseSealableManager(models.manager.Manager):
    def __init__(self, seal=None):
        self._seal_queryset = seal
        super().__init__()

    def _get_model(self):
        return self._model

    def _set_model(self, model):
        self._model = model
        if self._seal_queryset is None:
            self._seal_queryset = getattr(model, "_seal_managers", None)

    # Intercept .model assignment to inherit ._seal_managers as the
    # contribute_to_class() method is not called abstract model inheritance
    # of managers.
    model = property(_get_model, _set_model)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self._seal_queryset:
            queryset = queryset.seal()
        return queryset

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        if not issubclass(self.model, SealableModel):
            if getattr(self, "_built_with_as_manager", False):
                origin = "%s.as_manager()" % self._queryset_class.__name__
            else:
                origin = self.__class__.__name__
            errors.append(
                checks.Error(
                    "%s can only be used on seal.SealableModel subclasses." % origin,
                    id="seal.E001",
                    hint="Make %s inherit from seal.SealableModel."
                    % self.model._meta.label,
                    obj=self,
                )
            )
        return errors


SealableQuerySet._base_manager_class = BaseSealableManager
SealableManager = BaseSealableManager.from_queryset(SealableQuerySet, "SealableManager")


class SealableModel(models.Model):
    """
    Abstract model class that turns deferred and related fields accesses that
    would incur a database query into exceptions once sealed.
    """

    def __init_subclass__(cls, seal=None, **kwargs):
        if seal is None:
            seal = getattr(cls, "_seal_managers", seal)
        cls._seal_managers = seal
        return super().__init_subclass__(**kwargs)

    objects = SealableManager()

    class Meta:
        abstract = True

    def seal(self):
        """
        Seal the instance to turn deferred and related fields access that would
        required fetching from the database into exceptions.
        """
        self._state.sealed = True


def make_descriptor_sealable(model, attname):
    """
    Make a descriptor sealable if a sealable class is defined.
    """
    try:
        descriptor = getattr(model, attname)
    except AttributeError:
        # Handle hidden reverse accessor case. e.g. related_name='+'
        return
    sealable_descriptor_class = descriptors.sealable_descriptor_classes.get(
        descriptor.__class__
    )
    if sealable_descriptor_class:
        descriptor.__class__ = sealable_descriptor_class


def make_remote_field_descriptor_sealable(model, related_model, remote_field):
    """
    Make a remote field descriptor sealable if a sealable class is defined.
    """
    if not issubclass(related_model, SealableModel):
        return
    accessor_name = remote_field.get_accessor_name()
    # Self-referential many-to-many fields don't have a reverse accessor.
    if accessor_name is None:
        return
    make_descriptor_sealable(related_model, accessor_name)


def make_model_sealable(model):
    """
    Replace forward fields descriptors by sealable ones and reverse fields
    descriptors attached to SealableModel subclasses as well.

    This function should be called on a third-party model once all apps are
    done loading models such as from an AppConfig.ready().
    """
    opts = model._meta
    for field in opts.local_fields + opts.local_many_to_many + opts.private_fields:
        name = field.name
        attnames = {name, getattr(field, "attname", name)}
        for attname in attnames:
            make_descriptor_sealable(model, attname)
        remote_field = field.remote_field
        if remote_field:
            # Use lazy_related_operation because lazy relationships might not
            # be resolved yet.
            lazy_related_operation(
                make_remote_field_descriptor_sealable,
                model,
                remote_field.model,
                remote_field=remote_field,
            )
    # Non SealableModel subclasses won't have remote fields descriptors
    # attached to them made sealable so make sure to make locally defined
    # related objects sealable.
    if not issubclass(model, SealableModel):
        for related_object in opts.related_objects:
            make_descriptor_sealable(model, related_object.get_accessor_name())


@receiver(models.signals.class_prepared)
def _make_field_descriptors_sealable(sender, **kwargs):
    """
    Automatically make concrete SealableModel subclasses fields sealable.
    """
    if not issubclass(sender, SealableModel):
        return
    opts = sender._meta
    if opts.abstract or opts.proxy:
        return
    make_model_sealable(sender)
