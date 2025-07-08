import warnings

from django.test import SimpleTestCase

from seal.exceptions import UnsealedAttributeAccess


class UnsealedAttributeAccessTests(SimpleTestCase):
    def test_getattr_error_propagation(self):
        class Foo:
            @property
            def bar(self):
                warnings.warn("Test warning", category=UnsealedAttributeAccess)
                return "bar"

        warnings.filterwarnings("error", category=UnsealedAttributeAccess)
        self.addCleanup(warnings.resetwarnings)
        with self.assertRaisesMessage(UnsealedAttributeAccess, "Test warning"):
            getattr(Foo(), "bar", None)
