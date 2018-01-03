from django.test import TestCase
from seal.exceptions import SealedObject

from .models import SeaLion


class SealableModelTests(TestCase):
    def test_sealed_instance_deferred_attribute_access(self):
        instance = SeaLion.from_db('default', ['id'], [1])
        instance._state.sealed = True
        message = "Cannot fetch deferred fields weight on a sealed object."
        with self.assertRaisesMessage(SealedObject, message):
            instance.weight
