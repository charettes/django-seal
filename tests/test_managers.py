from django.test import TestCase
from seal.exceptions import SealedObject

from .models import GreatSeaLion, Koala, Location, SeaLion


class SealableQuerySetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location = Location.objects.create(latitude=51.585474, longitude=156.634331)
        cls.great_sealion = GreatSeaLion.objects.create(height=1, weight=100, location=cls.location)
        cls.koala = Koala.objects.create(height=1, weight=10)
        cls.sealion = cls.great_sealion.sealion_ptr
        cls.sealion.previous_locations.add(cls.location)

    def test_state_sealed_assigned(self):
        instance = SeaLion.objects.seal().get()
        self.assertTrue(instance._state.sealed)

    def test_sealed_deferred_field(self):
        instance = SeaLion.objects.seal().defer('weight').get()
        with self.assertRaisesMessage(SealedObject, 'Cannot fetch deferred fields weight on a sealed object.'):
            instance.weight

    def test_not_sealed_deferred_field(self):
        instance = SeaLion.objects.defer('weight').get()
        self.assertEqual(instance.weight, 100)

    def test_sealed_foreign_key(self):
        instance = SeaLion.objects.seal().get()
        with self.assertRaisesMessage(SealedObject, 'Cannot fetch related field location on a sealed object.'):
            instance.location

    def test_not_sealed_foreign_key(self):
        instance = SeaLion.objects.get()
        self.assertEqual(instance.location, self.location)

    def test_sealed_select_related_foreign_key(self):
        instance = SeaLion.objects.select_related('location').seal().get()
        self.assertEqual(instance.location, self.location)

    def test_sealed_many_to_many(self):
        instance = SeaLion.objects.seal().get()
        message = 'Cannot fetch many-to-many field previous_locations on a sealed object.'
        with self.assertRaisesMessage(SealedObject, message):
            instance.previous_locations.all()

    def test_not_sealed_many_to_many(self):
        instance = SeaLion.objects.get()
        self.assertSequenceEqual(instance.previous_locations.all(), [self.location])

    def test_sealed_prefetched_many_to_many(self):
        instance = SeaLion.objects.prefetch_related('previous_locations').seal().get()
        self.assertSequenceEqual(instance.previous_locations.all(), [self.location])

    def test_sealed_deferred_parent_link(self):
        instance = GreatSeaLion.objects.only('pk').seal().get()
        with self.assertRaisesMessage(SealedObject, 'Cannot fetch related field sealion_ptr on a sealed object.'):
            instance.sealion_ptr

    def test_not_sealed_parent_link(self):
        instance = GreatSeaLion.objects.only('pk').get()
        self.assertEqual(instance.sealion_ptr, self.sealion)

    def test_sealed_parent_link(self):
        instance = GreatSeaLion.objects.seal().get()
        with self.assertNumQueries(0):
            self.assertEqual(instance.sealion_ptr, self.sealion)

    def test_sealed_reverse_foreign_key(self):
        instance = Location.objects.seal().get()
        message = 'Cannot fetch many-to-many field visitors on a sealed object.'
        with self.assertRaisesMessage(SealedObject, message):
            instance.visitors.all()

    def test_not_sealed_reverse_foreign_key(self):
        instance = Location.objects.get()
        self.assertSequenceEqual(instance.visitors.all(), [self.sealion])

    def test_sealed_prefetched_reverse_foreign_key(self):
        instance = Location.objects.prefetch_related('visitors').seal().get()
        self.assertSequenceEqual(instance.visitors.all(), [self.sealion])

    def test_sealed_reverse_parent_link(self):
        instance = SeaLion.objects.seal().get()
        with self.assertRaisesMessage(SealedObject, 'Cannot fetch related field greatsealion on a sealed object.'):
            instance.greatsealion

    def test_not_sealed_reverse_parent_link(self):
        instance = SeaLion.objects.get()
        self.assertEqual(instance.greatsealion, self.great_sealion)

    def test_sealed_select_related_reverse_parent_link(self):
        instance = SeaLion.objects.select_related('greatsealion').seal().get()
        self.assertEqual(instance.greatsealion, self.great_sealion)

    def test_sealed_reverse_many_to_many(self):
        instance = Location.objects.seal().get()
        message = 'Cannot fetch many-to-many field previous_visitors on a sealed object.'
        with self.assertRaisesMessage(SealedObject, message):
            instance.previous_visitors.all()

    def test_not_reverse_sealed_many_to_many(self):
        instance = Location.objects.get()
        self.assertSequenceEqual(instance.previous_visitors.all(), [self.sealion])

    def test_sealed_prefetched_reverse_many_to_many(self):
        instance = Location.objects.prefetch_related('previous_visitors').seal().get()
        self.assertSequenceEqual(instance.previous_visitors.all(), [self.sealion])

    def test_improper_usage_raises_error(self):
        with self.assertRaises(AttributeError):
            Koala.objects.only('pk').seal().get()
