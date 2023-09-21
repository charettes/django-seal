import warnings

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core import checks
from django.db import models
from django.test import SimpleTestCase, TestCase
from django.test.utils import isolate_apps

from seal.descriptors import (
    SealableDeferredAttribute,
    SealableForwardManyToOneDescriptor,
    SealableForwardOneToOneDescriptor,
    SealableManyToManyDescriptor,
    SealableReverseManyToOneDescriptor,
    SealableReverseOneToOneDescriptor,
)
from seal.exceptions import UnsealedAttributeAccess
from seal.models import SealableManager, SealableModel, make_model_sealable
from seal.query import SealableQuerySet

from .models import GreatSeaLion, Location, Nickname, SeaGull, SeaLion


class SealableModelTests(SimpleTestCase):
    def setUp(self):
        warnings.filterwarnings("error", category=UnsealedAttributeAccess)
        self.addCleanup(warnings.resetwarnings)

    def test_sealed_instance_deferred_attribute_access(self):
        instance = SeaLion.from_db("default", ["id"], [1])
        instance.seal()
        message = (
            'Attempt to fetch deferred field "weight" on sealed <SeaLion instance>'
        )
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            instance.weight

    def test_sealed_instance_deferred_foreign_key_attribute_access(self):
        instance = SeaLion.from_db("default", ["id"], [1])
        instance.seal()
        message = (
            'Attempt to fetch deferred field "location_id" on sealed <SeaLion instance>'
        )
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            instance.location_id

    def test_sealed_instance_foreign_key_access(self):
        instance = SeaLion.from_db("default", ["id", "location_id"], [1, 1])
        instance.seal()
        message = (
            'Attempt to fetch related field "location" on sealed <SeaLion instance>'
        )
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            instance.location

    def test_sealed_instance_reverse_foreign_key_access(self):
        instance = Location.from_db("default", ["id"], [1])
        instance.seal()
        message = 'Attempt to fetch many-to-many field "visitors" on sealed <Location instance>'
        visitors = instance.visitors.all()
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            list(visitors)

    def test_sealed_instance_one_to_one_access(self):
        instance = SeaGull.from_db("default", ["id", "sealion_id"], [1, 1])
        instance.seal()
        message = (
            'Attempt to fetch related field "sealion" on sealed <SeaGull instance>'
        )
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            instance.sealion

    def test_sealed_instance_reverse_one_to_one_access(self):
        instance = SeaLion.from_db("default", ["id"], [1])
        instance.seal()
        message = 'Attempt to fetch related field "gull" on sealed <SeaLion instance>'
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            instance.gull

    def test_sealed_instance_parent_link_access(self):
        instance = SeaLion.from_db("default", ["id"], [1])
        instance.seal()
        message = (
            'Attempt to fetch related field "greatsealion" on sealed <SeaLion instance>'
        )
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            instance.greatsealion

    def test_sealed_instance_reverse_parent_link_access(self):
        instance = GreatSeaLion.from_db("default", ["sealion_ptr_id"], [1])
        instance.seal()
        message = 'Attempt to fetch related field "sealion_ptr" on sealed <GreatSeaLion instance>'
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            instance.sealion_ptr

    def test_sealed_instance_reverse_parent_link_access_sealed(self):
        instance = GreatSeaLion.from_db(
            "default",
            [
                "id",
                "sealion_ptr_id",
                "height",
                "weight",
                "location_id",
                "leak_id",
                "leak_o2o_id",
            ],
            [1, 1, 1, 1, 1, 1, 1],
        )
        instance.seal()
        message = (
            'Attempt to fetch related field "location" on sealed <SeaLion instance>'
        )
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            instance.sealion_ptr.location

    def test_sealed_instance_m2m_access(self):
        instance = SeaLion.from_db("default", ["id"], [1])
        instance.seal()
        message = 'Attempt to fetch many-to-many field "previous_locations" on sealed <SeaLion instance>'
        previous_locations = instance.previous_locations.all()
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            list(previous_locations)

    def test_sealed_instance_reverse_m2m_access(self):
        instance = Location.from_db("default", ["id"], [1])
        instance.seal()
        message = 'Attempt to fetch many-to-many field "previous_visitors" on sealed <Location instance>'
        previous_visitors = instance.previous_visitors.all()
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            list(previous_visitors)

    def test_sealed_instance_self_referential_m2m_acccess(self):
        instance = Location.from_db("default", ["id"], [1])
        instance.seal()
        message = 'Attempt to fetch many-to-many field "related_locations" on sealed <Location instance>'
        previous_visitors = instance.related_locations.all()
        with self.assertRaisesMessage(UnsealedAttributeAccess, message):
            list(previous_visitors)


class ContentTypesSealableModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        tests_models = tuple(apps.get_app_config("tests").get_models())
        ContentType.objects.get_for_models(*tests_models, for_concrete_models=True)

    def setUp(self):
        warnings.filterwarnings("error", category=UnsealedAttributeAccess)
        self.addCleanup(warnings.resetwarnings)

    def test_sealed_instance_generic_foreign_key(self):
        instance = Nickname.from_db(
            "default", ["id", "content_type_id", "object_id"], [1, 1, 1]
        )
        instance.seal()
        message = 'Attempt to fetch related field "content_object" on sealed <Nickname instance>'
        with self.assertNumQueries(0), self.assertRaisesMessage(
            UnsealedAttributeAccess, message
        ):
            instance.content_object

    def test_sealed_instance_generic_relation(self):
        instance = SeaGull.from_db("default", ["id"], [1])
        instance.seal()
        message = 'Attempt to fetch many-to-many field "nicknames" on sealed <SeaGull instance>'
        nicknames = instance.nicknames.all()
        with self.assertNumQueries(0), self.assertRaisesMessage(
            UnsealedAttributeAccess, message
        ):
            list(nicknames)


class SealableManagerTests(SimpleTestCase):
    def test_isinstance_manager(self):
        """Manager classes are subclasses of Manager as many third-party apps expect."""
        self.assertIsInstance(SealableManager(), models.Manager)
        self.assertIsInstance(SealableQuerySet.as_manager(), models.Manager)

    @isolate_apps("tests")
    def test_declarative_seal(self):
        class SealedManagers(SealableModel):
            manager = SealableManager(seal=True)
            as_manager = SealableQuerySet.as_manager(seal=True)

        sealed_iterable_class = SealedManagers.objects.seal()._iterable_class
        self.assertIsNot(
            SealedManagers.objects.all()._iterable_class, sealed_iterable_class
        )
        self.assertIs(
            SealedManagers.manager.all()._iterable_class, sealed_iterable_class
        )
        self.assertIs(
            SealedManagers.as_manager.all()._iterable_class, sealed_iterable_class
        )

        class MixinInitSubclass:
            def __init_subclass__(cls, foo=None, **kwargs):
                cls.foo = foo
                super().__init_subclass__(**kwargs)

        class SealedBaseModel(MixinInitSubclass, SealableModel, foo="bar", seal=True):
            class Meta:
                abstract = True

        self.assertEqual(SealedBaseModel.foo, "bar")

        class SealedModel(SealedBaseModel):
            manager = SealableManager(seal=False)
            as_manager = SealableQuerySet.as_manager(seal=False)

        self.assertIs(SealedModel.objects.all()._iterable_class, sealed_iterable_class)
        self.assertIsNot(
            SealedModel.manager.all()._iterable_class, sealed_iterable_class
        )
        self.assertIsNot(
            SealedModel.as_manager.all()._iterable_class, sealed_iterable_class
        )

    @isolate_apps("tests")
    def test_non_sealable_model(self):
        class Foo(models.Model):
            manager = SealableManager()
            as_manager = SealableQuerySet.as_manager()

        self.assertEqual(
            Foo.manager.check(),
            [
                checks.Error(
                    "SealableManager can only be used on seal.SealableModel subclasses.",
                    id="seal.E001",
                    hint="Make tests.Foo inherit from seal.SealableModel.",
                    obj=Foo.manager,
                )
            ],
        )
        self.assertEqual(
            Foo.as_manager.check(),
            [
                checks.Error(
                    "SealableQuerySet.as_manager() can only be used on seal.SealableModel subclasses.",
                    id="seal.E001",
                    hint="Make tests.Foo inherit from seal.SealableModel.",
                    obj=Foo.as_manager,
                )
            ],
        )


class MakeModelSealableTests(SimpleTestCase):
    @isolate_apps("tests")
    def test_make_non_sealable_model_subclass(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            foo = models.BooleanField(default=False)
            fk = models.ForeignKey(Foo, models.CASCADE, related_name="fk_bar")
            o2o = models.OneToOneField(Foo, models.CASCADE, related_name="o2o_bar")
            m2m = models.ManyToManyField(Foo, related_name="m2m_bar")

        make_model_sealable(Bar)

        # Forward fields descriptors should have been made sealable.
        self.assertIsInstance(Bar.foo, SealableDeferredAttribute)
        self.assertIsInstance(Bar.fk, SealableForwardManyToOneDescriptor)
        self.assertIsInstance(Bar.o2o, SealableForwardOneToOneDescriptor)
        self.assertIsInstance(Bar.m2m, SealableManyToManyDescriptor)

        # But not the remote fields.
        self.assertNotIsInstance(Foo.fk_bar, SealableReverseManyToOneDescriptor)
        self.assertNotIsInstance(Foo.o2o_bar, SealableReverseOneToOneDescriptor)
        self.assertNotIsInstance(Foo.m2m_bar, SealableManyToManyDescriptor)

        # Should seal local related objects.
        make_model_sealable(Foo)
        self.assertIsInstance(Foo.fk_bar, SealableReverseManyToOneDescriptor)
        self.assertIsInstance(Foo.o2o_bar, SealableReverseOneToOneDescriptor)
        self.assertIsInstance(Foo.m2m_bar, SealableManyToManyDescriptor)
