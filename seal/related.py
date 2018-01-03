from django.db.models.fields.related import ForwardManyToOneDescriptor

from .exceptions import SealedObject


class SealableForwardManyToOneDescriptor(ForwardManyToOneDescriptor):
    def get_object(self, instance):
        if getattr(instance._state, 'sealed', False):
            raise SealedObject('Cannot fetch related field %s on a sealed object.' % self.field.name)
        return super(SealableForwardManyToOneDescriptor, self).get_object(instance)


sealable_accessor_classes = {
    ForwardManyToOneDescriptor: SealableForwardManyToOneDescriptor,
}
