from django.test import TestCase
from seal.exceptions import SealedObject

from .models import SeaLion


class SealableQuerySetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sealion = SeaLion.objects.create(height=1, weight=100)

    def test_state_sealed_assigned(self):
        instance = SeaLion.objects.seal().get()
        self.assertTrue(instance._state.sealed)

    def test_sealed_deferred_field(self):
        instance = SeaLion.objects.seal().defer('weight').get()
        with self.assertRaisesMessage(SealedObject, 'Cannot fetch deferred fields weight on a sealed object.'):
            instance.weight
