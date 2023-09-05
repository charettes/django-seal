django-seal
===========

.. image:: https://publicdomainvectors.org/photos/Seal2.png
    :target: https://publicdomainvectors.org
    :alt: Seal

------------

.. image:: https://github.com/charettes/django-seal/workflows/Test/badge.svg
    :target: https://github.com/charettes/django-seal/actions
    :alt: Build Status

.. image:: https://coveralls.io/repos/github/charettes/django-seal/badge.svg?branch=master
    :target: https://coveralls.io/github/charettes/django-seal?branch=master
    :alt: Coverage status


Django application providing queryset sealing capability to force appropriate usage of ``only()``/``defer()`` and
``select_related()``/``prefetch_related()``.

Installation
------------

.. code:: sh

    pip install django-seal

Usage
-----

.. code:: python

    # models.py
    from django.db import models
    from seal.models import SealableModel

    class Location(SealableModel):
        latitude = models.FloatField()
        longitude = models.FloatField()

    class SeaLion(SealableModel):
        height = models.PositiveIntegerField()
        weight = models.PositiveIntegerField()
        location = models.ForeignKey(Location, models.CASCADE, null=True)
        previous_locations = models.ManyToManyField(Location, related_name='previous_visitors')

By default ``UnsealedAttributeAccess`` warnings will be raised on sealed objects attributes accesses

.. code:: python

    >>> location = Location.objects.create(latitude=51.585474, longitude=156.634331)
    >>> sealion = SeaLion.objects.create(height=1, weight=100, location=location)
    >>> sealion.previous_locations.add(location)
    >>> SeaLion.objects.only('height').seal().get().weight
    UnsealedAttributeAccess:: Attempt to fetch deferred field "weight" on sealed <SeaLion instance>.
    >>> SeaLion.objects.seal().get().location
    UnsealedAttributeAccess: Attempt to fetch related field "location" on sealed <SeaLion instance>.
    >>> SeaLion.objects.seal().get().previous_locations.all()
    UnsealedAttributeAccess: Attempt to fetch many-to-many field "previous_locations" on sealed <SeaLion instance>.

You can `elevate the warnings to exceptions by filtering them`_. This is useful to assert no unsealed attribute accesses are
performed when running your test suite for example.

.. code:: python

    >>> import warnings
    >>> from seal.exceptions import UnsealedAttributeAccess
    >>> warnings.filterwarnings('error', category=UnsealedAttributeAccess)
    >>> SeaLion.objects.only('height').seal().get().weight
    Traceback (most recent call last)
    ...
    UnsealedAttributeAccess:: Attempt to fetch deferred field "weight" on sealed <SeaLion instance>.
    >>> SeaLion.objects.seal().get().location
    Traceback (most recent call last)
    ...
    UnsealedAttributeAccess: Attempt to fetch related field "location" on sealed <SeaLion instance>.
    >>> SeaLion.objects.seal().get().previous_locations.all()
    Traceback (most recent call last)
    ...
    UnsealedAttributeAccess: Attempt to fetch many-to-many field "previous_locations" on sealed <SeaLion instance>.

Or you can `configure logging to capture warnings`_ to log unsealed attribute accesses to the ``py.warnings`` logger which is a
nice way to identify and address unsealed attributes accesses from production logs without taking your application down if some
instances happen to slip through your battery of tests.

.. code:: python

    >>> import logging
    >>> logging.captureWarnings(True)

.. _elevate the warnings to exceptions by filtering them: https://docs.python.org/3/library/warnings.html#warnings.filterwarnings
.. _configure logging to capture warnings: https://docs.python.org/3/library/logging.html#logging.captureWarnings

Sealable managers can also be automatically sealed at model definition time to avoid having to call ``seal()`` systematically
by passing ``seal=True`` to ``SealableModel`` subclasses, ``SealableManager`` and ``SealableQuerySet.as_manager``.

.. code-block:: python

    from django.db import models
    from seal.models import SealableManager, SealableModel, SealableQuerySet

    class Location(SealableModel, seal=True):
        latitude = models.FloatField()
        longitude = models.FloatField()

    class SeaLion(SealableModel):
        height = models.PositiveIntegerField()
        weight = models.PositiveIntegerField()
        location = models.ForeignKey(Location, models.CASCADE, null=True)
        previous_locations = models.ManyToManyField(Location, related_name='previous_visitors')

        objects = SealableManager(seal=True)
        others = SealableQuerySet.as_manager(seal=True)

Development
-----------

Make your changes, and then run tests via tox:

.. code:: sh

    tox
