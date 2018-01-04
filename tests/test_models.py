from django.test import SimpleTestCase
from seal.exceptions import SealedObject

from .models import Location, SeaLion


class SealableModelTests(SimpleTestCase):
    def test_sealed_instance_deferred_attribute_access(self):
        instance = SeaLion.from_db('default', ['id'], [1])
        instance._state.sealed = True
        message = "Cannot fetch deferred fields weight on a sealed object."
        with self.assertRaisesMessage(SealedObject, message):
            instance.weight

    def test_sealed_instance_foreign_key_access(self):
        instance = SeaLion.from_db('default', ['id', 'location_id'], [1, 1])
        instance._state.sealed = True
        message = "Cannot fetch related field location on a sealed object."
        with self.assertRaisesMessage(SealedObject, message):
            instance.location

    def test_sealed_instance_reverse_foreign_key_access(self):
        instance = Location.from_db('default', ['latitude', 'longitude'], [1.2, 3.4])
        instance._state.sealed = True
        message = "Cannot fetch many-to-many field visitors on a sealed object."
        with self.assertRaisesMessage(SealedObject, message):
            instance.visitors.all()

    def test_sealed_instance_m2m_access(self):
        instance = SeaLion.from_db('default', ['id'], [1])
        instance._state.sealed = True
        message = "Cannot fetch many-to-many field previous_locations on a sealed object."
        with self.assertRaisesMessage(SealedObject, message):
            instance.previous_locations.all()
