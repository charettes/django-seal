import pickle
import warnings

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Prefetch
from django.db.models.query import ModelIterable
from django.test import SimpleTestCase, TestCase
from django.test.utils import isolate_apps

from seal.descriptors import _SealedRelatedQuerySet
from seal.exceptions import UnsealedAttributeAccess
from seal.models import make_model_sealable
from seal.query import SealableQuerySet, SealedModelIterable

from .models import (
    Climate,
    GreatSeaLion,
    Island,
    Leak,
    Location,
    Nickname,
    SeaGull,
    SeaLion,
)


class SealableQuerySetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location = Location.objects.create(latitude=51.585474, longitude=156.634331)
        cls.climate = Climate.objects.create(temperature=100)
        cls.location.climates.add(cls.climate)
        cls.leak = Leak.objects.create(description="Salt water")
        cls.great_sealion = GreatSeaLion.objects.create(
            height=1,
            weight=100,
            location=cls.location,
            leak=cls.leak,
            leak_o2o=cls.leak,
        )
        cls.sealion = cls.great_sealion.sealion_ptr
        cls.sealion.previous_locations.add(cls.location)
        cls.gull = SeaGull.objects.create(sealion=cls.sealion)
        cls.nickname = Nickname.objects.create(
            name="Jonathan Livingston", content_object=cls.gull
        )
        cls.island = Island.objects.create(location=cls.location)
        tests_models = tuple(apps.get_app_config("tests").get_models())
        ContentType.objects.get_for_models(*tests_models, for_concrete_models=True)

    def setUp(self):
        warnings.filterwarnings("error", category=UnsealedAttributeAccess)
        self.addCleanup(warnings.resetwarnings)

    def test_state_sealed_assigned(self):
        instance = SeaLion.objects.seal().get()
        self.assertTrue(instance._state.sealed)

    def test_sealed_deferred_field(self):
        instance = SeaLion.objects.seal().defer("weight").get()
        message = (
            'Attempt to fetch deferred field "weight" on sealed <SeaLion instance>'
        )
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.weight
        self.assertEqual(ctx.filename, __file__)

    def test_not_sealed_deferred_field(self):
        instance = SeaLion.objects.defer("weight").get()
        self.assertEqual(instance.weight, 100)

    def test_sealed_foreign_key(self):
        instance = SeaLion.objects.seal().get()
        message = (
            'Attempt to fetch related field "location" on sealed <SeaLion instance>'
        )
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.location
        self.assertEqual(ctx.filename, __file__)

    def test_not_sealed_foreign_key(self):
        instance = SeaLion.objects.get()
        self.assertEqual(instance.location, self.location)

    def test_sealed_select_related_foreign_key(self):
        instance = SeaLion.objects.select_related("location").seal().get()
        self.assertEqual(instance.location, self.location)
        instance = SeaGull.objects.select_related("sealion").seal().get()
        message = (
            'Attempt to fetch related field "location" on sealed <SeaLion instance>'
        )
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.sealion.location
        instance = SeaGull.objects.select_related("sealion__location").seal().get()
        self.assertEqual(instance.sealion.location, self.location)
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_select_related_none_foreign_key(self):
        SeaLion.objects.update(location=None)
        instance = SeaLion.objects.select_related("location").seal().get()
        self.assertIsNone(instance.location)
        SeaGull.objects.update(sealion=None)
        instance = SeaGull.objects.select_related("sealion__location").seal().get()
        self.assertIsNone(instance.sealion)

    def test_select_related_foreign_key_leak(self):
        instance = SeaLion.objects.get()
        self.assertEqual(instance.leak.description, self.leak.description)

        instance = SeaLion.objects.select_related("leak").get()
        self.assertEqual(instance.leak.description, self.leak.description)

    def test_select_related_foreign_key_leak_o2o(self):
        instance = SeaLion.objects.get()
        self.assertEqual(instance.leak_o2o.description, self.leak.description)

        instance = SeaLion.objects.select_related("leak_o2o").get()
        self.assertEqual(instance.leak_o2o.description, self.leak.description)

    def test_sealed_select_related_foreign_key_leak(self):
        instance = (
            SeaLion.objects.select_related("leak")
            .defer("leak__description")
            .seal()
            .get()
        )
        with self.assertNumQueries(1):
            self.assertEqual(instance.leak.description, self.leak.description)

    def test_sealed_select_related_foreign_key_leak_o2o(self):
        instance = (
            SeaLion.objects.select_related("leak_o2o")
            .defer("leak_o2o__description")
            .seal()
            .get()
        )
        with self.assertNumQueries(1):
            self.assertEqual(instance.leak_o2o.description, self.leak.description)

    def test_sealed_select_related_deferred_field(self):
        instance = (
            SeaGull.objects.select_related(
                "sealion__location",
            )
            .only("sealion__location__latitude")
            .seal()
            .get()
        )
        self.assertEqual(instance.sealion.location, self.location)
        self.assertEqual(instance.sealion.location.latitude, self.location.latitude)
        message = (
            'Attempt to fetch deferred field "longitude" on sealed <Location instance>'
        )
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.sealion.location.longitude
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_one_to_one(self):
        instance = SeaGull.objects.seal().get()
        message = (
            'Attempt to fetch related field "sealion" on sealed <SeaGull instance>'
        )
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.sealion
        self.assertEqual(ctx.filename, __file__)

    def test_not_sealed_one_to_one(self):
        instance = SeaGull.objects.get()
        self.assertEqual(instance.sealion, self.sealion)

    def test_sealed_select_related_one_to_one(self):
        instance = SeaGull.objects.select_related("sealion").seal().get()
        self.assertEqual(instance.sealion, self.sealion)

    def test_sealed_select_related_reverse_one_to_one(self):
        instance = SeaLion.objects.select_related("gull").seal().get()
        self.assertEqual(instance.gull, self.gull)
        self.gull.sealion = None
        self.gull.save(update_fields={"sealion"})
        instance = SeaLion.objects.select_related("gull").seal().get()
        with self.assertRaises(SeaLion.gull.RelatedObjectDoesNotExist):
            instance.gull

    def test_sealed_select_related_unrestricted(self):
        instance = Island.objects.select_related().seal().get()
        self.assertEqual(instance.location, self.location)
        instance = SeaLion.objects.select_related().seal().get()
        message = (
            'Attempt to fetch related field "location" on sealed <SeaLion instance>'
        )
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            # null=True relationships are not followed when using
            # an unrestricted select_related()
            instance.location
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_prefetch_related_reverse_one_to_one(self):
        instance = SeaLion.objects.prefetch_related("gull").seal().get()
        self.assertEqual(instance.gull, self.gull)
        self.gull.sealion = None
        self.gull.save(update_fields={"sealion"})
        instance = SeaLion.objects.prefetch_related("gull").seal().get()
        with self.assertRaises(SeaLion.gull.RelatedObjectDoesNotExist):
            instance.gull

    def test_sealed_many_to_many(self):
        instance = SeaLion.objects.seal().get()
        message = 'Attempt to fetch many-to-many field "previous_locations" on sealed <SeaLion instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.previous_locations.all())
        self.assertEqual(ctx.filename, __file__)
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.previous_locations.all()[0]
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_many_to_many_queryset(self):
        instance = SeaLion.objects.seal().get()
        self.assertEqual(
            instance.previous_locations.get(pk=self.location.pk), self.location
        )
        self.assertFalse(
            isinstance(
                instance.previous_locations.filter(pk=self.location.pk),
                _SealedRelatedQuerySet,
            )
        )

    def test_not_sealed_many_to_many(self):
        instance = SeaLion.objects.get()
        self.assertSequenceEqual(instance.previous_locations.all(), [self.location])

    def test_sealed_string_prefetched_many_to_many(self):
        instance = SeaLion.objects.prefetch_related("previous_locations").seal().get()
        with self.assertNumQueries(0):
            self.assertSequenceEqual(instance.previous_locations.all(), [self.location])
        instance = instance.previous_locations.all()[0]
        message = 'Attempt to fetch many-to-many field "previous_visitors" on sealed <Location instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.previous_visitors.all())
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_prefetch_prefetched_many_to_many(self):
        instance = (
            SeaLion.objects.prefetch_related(
                Prefetch("previous_locations"),
            )
            .seal()
            .get()
        )
        with self.assertNumQueries(0):
            self.assertSequenceEqual(instance.previous_locations.all(), [self.location])
        instance = instance.previous_locations.all()[0]
        message = 'Attempt to fetch many-to-many field "previous_visitors" on sealed <Location instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.previous_visitors.all())
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_prefetch_queryset_prefetched_many_to_many(self):
        instance = (
            SeaLion.objects.prefetch_related(
                Prefetch("previous_locations", Location.objects.all()),
            )
            .seal()
            .get()
        )
        with self.assertNumQueries(0):
            self.assertSequenceEqual(instance.previous_locations.all(), [self.location])
        instance = instance.previous_locations.all()[0]
        message = 'Attempt to fetch many-to-many field "previous_visitors" on sealed <Location instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.previous_visitors.all())
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_string_prefetched_nested_many_to_many(self):
        with self.assertNumQueries(3):
            instance = (
                SeaLion.objects.prefetch_related(
                    "previous_locations__previous_visitors"
                )
                .seal()
                .get()
            )
        with self.assertNumQueries(0):
            self.assertSequenceEqual(instance.previous_locations.all(), [self.location])
            self.assertSequenceEqual(
                instance.previous_locations.all()[0].previous_visitors.all(),
                [self.sealion],
            )
        instance = instance.previous_locations.all()[0].previous_visitors.all()[0]
        message = 'Attempt to fetch many-to-many field "previous_locations" on sealed <SeaLion instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.previous_locations.all())
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_prefetch_prefetched_nested_many_to_many(self):
        instance = (
            SeaLion.objects.prefetch_related(
                Prefetch("previous_locations__previous_visitors"),
            )
            .seal()
            .get()
        )
        with self.assertNumQueries(0):
            self.assertSequenceEqual(instance.previous_locations.all(), [self.location])
            self.assertSequenceEqual(
                instance.previous_locations.all()[0].previous_visitors.all(),
                [self.sealion],
            )
        instance = instance.previous_locations.all()[0].previous_visitors.all()[0]
        message = 'Attempt to fetch many-to-many field "previous_locations" on sealed <SeaLion instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.previous_locations.all())
        self.assertEqual(ctx.filename, __file__)

    def test_prefetched_sealed_many_to_many(self):
        instance = SeaLion.objects.prefetch_related(
            Prefetch("previous_locations", Location.objects.seal()),
        ).get()
        with self.assertNumQueries(0):
            self.assertSequenceEqual(instance.previous_locations.all(), [self.location])
        message = 'Attempt to fetch many-to-many field "previous_visitors" on sealed <Location instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.previous_locations.all()[0].previous_visitors.all())
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_deferred_parent_link(self):
        instance = GreatSeaLion.objects.only("pk").seal().get()
        message = 'Attempt to fetch related field "sealion_ptr" on sealed <GreatSeaLion instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.sealion_ptr
        self.assertEqual(ctx.filename, __file__)

    def test_not_sealed_parent_link(self):
        instance = GreatSeaLion.objects.only("pk").get()
        self.assertEqual(instance.sealion_ptr, self.sealion)

    def test_sealed_parent_link(self):
        instance = GreatSeaLion.objects.seal().get()
        with self.assertNumQueries(0):
            self.assertEqual(instance.sealion_ptr, self.sealion)

    def test_sealed_generic_foreign_key(self):
        instance = Nickname.objects.seal().get()
        message = 'Attempt to fetch related field "content_object" on sealed <Nickname instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.content_object
        self.assertEqual(ctx.filename, __file__)

    def test_not_sealed_generic_foreign_key(self):
        instance = Nickname.objects.get()
        self.assertEqual(instance.content_object, self.gull)

    def test_sealed_prefetch_related_generic_foreign_key(self):
        instance = Nickname.objects.prefetch_related("content_object").seal().get()
        with self.assertNumQueries(0):
            self.assertEqual(instance.content_object, self.gull)

    def test_sealed_reverse_foreign_key(self):
        instance = Location.objects.seal().get()
        message = 'Attempt to fetch many-to-many field "visitors" on sealed <Location instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.visitors.all())
        self.assertEqual(ctx.filename, __file__)

    def test_not_sealed_reverse_foreign_key(self):
        instance = Location.objects.get()
        self.assertSequenceEqual(instance.visitors.all(), [self.sealion])

    def test_sealed_prefetched_reverse_foreign_key(self):
        instance = Location.objects.prefetch_related("visitors").seal().get()
        self.assertSequenceEqual(instance.visitors.all(), [self.sealion])

    def test_sealed_reverse_parent_link(self):
        instance = SeaLion.objects.seal().get()
        message = (
            'Attempt to fetch related field "greatsealion" on sealed <SeaLion instance>'
        )
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.greatsealion
        self.assertEqual(ctx.filename, __file__)

    def test_not_sealed_reverse_parent_link(self):
        instance = SeaLion.objects.get()
        self.assertEqual(instance.greatsealion, self.great_sealion)

    def test_sealed_select_related_reverse_parent_link(self):
        instance = SeaLion.objects.select_related("greatsealion").seal().get()
        self.assertEqual(instance.greatsealion, self.great_sealion)

    def test_sealed_reverse_many_to_many(self):
        instance = Location.objects.seal().get()
        message = 'Attempt to fetch many-to-many field "previous_visitors" on sealed <Location instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.previous_visitors.all())
        self.assertEqual(ctx.filename, __file__)
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.previous_visitors.all()[0]
        self.assertEqual(ctx.filename, __file__)

    def test_sealed_reverse_many_to_many_queryset(self):
        instance = Location.objects.seal().get()
        self.assertEqual(
            instance.previous_visitors.get(pk=self.sealion.pk), self.sealion
        )
        self.assertFalse(
            isinstance(
                instance.previous_visitors.filter(pk=self.sealion.pk),
                _SealedRelatedQuerySet,
            )
        )

    def test_not_reverse_sealed_many_to_many(self):
        instance = Location.objects.get()
        self.assertSequenceEqual(instance.previous_visitors.all(), [self.sealion])

    def test_sealed_prefetched_reverse_many_to_many(self):
        instance = Location.objects.prefetch_related("previous_visitors").seal().get()
        self.assertSequenceEqual(instance.previous_visitors.all(), [self.sealion])

    def test_sealed_generic_relation(self):
        instance = SeaGull.objects.seal().get()
        message = 'Attempt to fetch many-to-many field "nicknames" on sealed <SeaGull instance>'
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            list(instance.nicknames.all())
        self.assertEqual(ctx.filename, __file__)
        with self.assertWarnsMessage(UnsealedAttributeAccess, message) as ctx:
            instance.nicknames.all()[0]
        self.assertEqual(ctx.filename, __file__)

    def test_not_sealed_generic_relation(self):
        instance = SeaGull.objects.get()
        self.assertSequenceEqual(instance.nicknames.all(), [self.nickname])

    def test_sealed_prefetched_generic_relation(self):
        instance = SeaGull.objects.prefetch_related("nicknames").seal().get()
        self.assertSequenceEqual(instance.nicknames.all(), [self.nickname])

    def test_sealed_prefetched_select_related_many_to_many(self):
        with self.assertNumQueries(2):
            instance = (
                SeaLion.objects.select_related(
                    "location",
                )
                .prefetch_related(
                    "location__climates",
                )
                .seal()
                .get()
            )
        with self.assertNumQueries(0):
            self.assertSequenceEqual(instance.location.climates.all(), [self.climate])

    def test_prefetch_without_related_name(self):
        location = Location.objects.prefetch_related("island_set").seal().get()
        self.assertSequenceEqual(location.island_set.all(), [self.island])

    def test_prefetch_combine(self):
        with self.assertNumQueries(6):
            instance = (
                SeaLion.objects.prefetch_related(
                    "location",
                    "location__climates",
                    "location__previous_visitors__location",
                    "location__previous_visitors__previous_locations",
                )
                .seal()
                .get()
            )
        with self.assertNumQueries(0):
            self.assertEqual(instance.location, self.location)
            self.assertSequenceEqual(instance.location.climates.all(), [self.climate])
            self.assertSequenceEqual(
                instance.location.previous_visitors.all(), [self.sealion]
            )
            self.assertEqual(
                instance.location.previous_visitors.all()[0].location, self.location
            )
            self.assertSequenceEqual(
                instance.location.previous_visitors.all()[0].previous_locations.all(),
                [self.location],
            )

    def test_sealed_prefetch_related_results_cache(self):
        """Some related managers fetch objects in get_prefetch_queryset()."""
        location_relations = ["climates", "related_locations", "visitors"]
        for relation in location_relations:
            with self.subTest(relation=relation), self.assertNumQueries(2):
                list(Location.objects.seal().prefetch_related(relation).all())
        sea_lion_relations = ["location", "previous_locations", "leak", "leak_o2o"]
        for relation in sea_lion_relations:
            with self.subTest(relation=relation), self.assertNumQueries(2):
                list(SeaLion.objects.seal().prefetch_related(relation).all())

    def test_sealed_prefetch_many_to_many_results(self):
        other_location = Location.objects.create(
            latitude=51.585474, longitude=156.634331
        )
        other_climate = Climate.objects.create(temperature=60)
        other_location.climates.add(other_climate)
        with self.assertNumQueries(2):
            results = list(
                Location.objects.seal().prefetch_related("climates").order_by("pk")
            )
        self.assertEqual(results, [self.location, other_location])
        with self.assertNumQueries(0):
            self.assertEqual(list(results[0].climates.all()), [self.climate])
            self.assertEqual(list(results[1].climates.all()), [other_climate])

    def test_sealed_prefetch_reverse_many_to_one_results(self):
        other_location = Location.objects.create(
            latitude=51.585474, longitude=156.634331
        )
        other_sealion = SeaLion.objects.create(
            height=1, weight=2, location=other_location
        )
        with self.assertNumQueries(2):
            results = list(
                Location.objects.seal().prefetch_related("visitors").order_by("pk")
            )
        self.assertEqual(results, [self.location, other_location])
        with self.assertNumQueries(0):
            self.assertEqual(list(results[0].visitors.all()), [self.sealion])
            self.assertEqual(list(results[1].visitors.all()), [other_sealion])

    def test_sealed_prefetch_reverse_generic_many_to_one_results(self):
        other_sealion = SeaLion.objects.create(height=1, weight=2)
        other_gull = SeaGull.objects.create(sealion=other_sealion)
        other_nickname = Nickname.objects.create(
            name="Test Nickname", content_object=other_gull
        )
        with self.assertNumQueries(2):
            results = list(
                SeaGull.objects.seal().prefetch_related("nicknames").order_by("pk")
            )
        self.assertEqual(results, [self.gull, other_gull])
        with self.assertNumQueries(0):
            self.assertEqual(list(results[0].nicknames.all()), [self.nickname])
            self.assertEqual(list(results[1].nicknames.all()), [other_nickname])

    def test_related_sealed_pickleability(self):
        location = Location.objects.prefetch_related("climates").seal().get()
        climates_dump = pickle.dumps(location.climates.all())
        climates = pickle.loads(climates_dump)
        with self.assertNumQueries(0):
            self.assertEqual(list(climates)[0], self.climate)


class SealableQuerySetInteractionTests(SimpleTestCase):
    def test_values_seal_disallowed(self):
        with self.assertRaisesMessage(
            TypeError, "Cannot call seal() after .values() or .values_list()"
        ):
            SeaGull.objects.values("id").seal()

    def test_values_list_seal_disallowed(self):
        with self.assertRaisesMessage(
            TypeError, "Cannot call seal() after .values() or .values_list()"
        ):
            SeaGull.objects.values_list("id").seal()

    def test_seal_sealable_model_iterable_subclass(self):
        class SealableModelIterableSubclass(SealedModelIterable):
            pass

        queryset = SeaGull.objects.seal(iterable_class=SealableModelIterableSubclass)
        self.assertIs(queryset._iterable_class, SealableModelIterableSubclass)

    def test_seal_non_sealable_model_iterable_subclass(self):
        message = (
            "iterable_class <class 'django.db.models.query.ModelIterable'> "
            "is not a subclass of SealedModelIterable"
        )
        with self.assertRaisesMessage(TypeError, message):
            SeaGull.objects.seal(iterable_class=ModelIterable)


class SealableQuerySetNonSealableModelTests(TestCase):
    """
    A SealableQuerySet should be usable on non SealableModel subclasses.
    """

    @classmethod
    def setUpTestData(cls):
        cls.location = Location.objects.create(latitude=51.585474, longitude=156.634331)
        cls.climate = Climate.objects.create(temperature=100)
        cls.location.climates.add(cls.climate)
        cls.sealion = SeaLion.objects.create(
            height=1, weight=100, location=cls.location
        )

    @isolate_apps("tests")
    def test_sealed_non_sealable_model(self):
        class NonSealableLocation(models.Model):
            class Meta:
                db_table = Location._meta.db_table

        queryset = SealableQuerySet(model=NonSealableLocation)
        instance = queryset.seal().get()
        self.assertTrue(instance._state.sealed)

    @isolate_apps("tests")
    def test_sealed_select_related_non_sealable_model(self):
        class NonSealableLocation(models.Model):
            class Meta:
                db_table = Location._meta.db_table

        class NonSealableSeaLion(models.Model):
            location = models.ForeignKey(NonSealableLocation, models.CASCADE)

            class Meta:
                db_table = SeaLion._meta.db_table

        queryset = SealableQuerySet(model=NonSealableSeaLion)
        instance = queryset.select_related("location").seal().get()
        self.assertTrue(instance._state.sealed)
        self.assertTrue(instance.location._state.sealed)

    @isolate_apps("tests")
    def test_sealed_prefetch_related_non_sealable_model(self):
        class NonSealableClimate(models.Model):
            objects = SealableQuerySet.as_manager()

            class Meta:
                db_table = Climate._meta.db_table

        class NonSealableLocationClimatesThrough(models.Model):
            climate = models.ForeignKey(NonSealableClimate, models.CASCADE)
            location = models.ForeignKey("NonSealableLocation", models.CASCADE)

            class Meta:
                db_table = Location.climates.through._meta.db_table

        class NonSealableLocation(models.Model):
            climates = models.ManyToManyField(
                NonSealableClimate, through=NonSealableLocationClimatesThrough
            )

            class Meta:
                db_table = Location._meta.db_table

        make_model_sealable(NonSealableLocation)
        queryset = SealableQuerySet(model=NonSealableLocation)
        instance = queryset.prefetch_related("climates").seal().get()
        self.assertTrue(instance._state.sealed)
        with self.assertNumQueries(0):
            self.assertTrue(instance.climates.all()[0]._state.sealed)
