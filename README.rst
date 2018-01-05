django-seal
===========

.. image:: https://publicdomainvectors.org/photos/Seal2.png
    :target: https://publicdomainvectors.org
    :alt: Seal

------------

.. image:: https://travis-ci.org/charettes/django-seal.svg?branch=master
    :target: https://travis-ci.org/charettes/django-seal
    :alt: Build Status

.. image:: https://coveralls.io/repos/github/charettes/django-seal/badge.svg?branch=master
    :target: https://coveralls.io/github/charettes/django-seal?branch=master
    :alt: Coverage status


Django application providing queryset sealing capability to force appropriate usage of ``only()``/``defer()`` and
``select_related()``/``prefetch_related()``.

Installation
------------

.. code:: sh

    pip install -e git+https://github.com/charettes/django-seal#egg=seal

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

.. code:: python

    >>> location = Location.objects.create(latitude=51.585474, longitude=156.634331)
    >>> sealion = SeaLion.objects.create(height=1, weight=100, location=cls.location)
    >>> sealion.previous_locations.add(cls.location)
    >>> SeaLion.objects.only('height').seal().get().weight
    Traceback (most recent call last)
    ...
    SealedObject: Cannot fetch deferred field weight on a sealed object.
    >>> SeaLion.objects.seal().get().location
    Traceback (most recent call last)
    ...
    SealedObject: Cannot fetch related field location on a sealed object.
    >>> SeaLion.objects.seal().get().previous_locations.all()
    Traceback (most recent call last)
    ...
    SealedObject: Cannot fetch many-to-many field previous_locations on a sealed object.

Development
-----------

Make your changes, and then run tests via tox:

.. code:: sh

    tox
