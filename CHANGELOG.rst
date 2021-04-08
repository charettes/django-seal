1.4.3
=====
:release-date: 2021-04-08

- Address a regression introduced in 1.4.2 that made sealing querysets
  prefetching generic relationships return the wrong results.

1.4.2
=====
:release-date: 2021-04-05

- Properly handled related descriptors ``get_prefetch_queryset`` overrides (#58)

1.4.1
=====
:release-date: 2021-03-30

- Properly handled ``ForeignKeyDeferredAttribute`` deferral (#56)

1.4.0
=====
:release-date: 2021-01-26

- Added tested support for Python 3.9 and Django 3.2
- Dropped support for Django 1.11

1.3.0
=====
:release-date: 2021-01-11

- Added tested support for Django 3.1
- Dropped support for Python 2.7 and 3.5.
- Allowed ``select_related()`` and ``prefetch_related()`` to be called after ``seal()`` (#45)
- Addressed an a crash when combining ``prefetch_related`` string prefixes (#39)
- Addressed a crash when dealing with self-referential many-to-many descriptors (#51)

1.2.3
=====
:release-date: 2020-02-23

- Added tested support for Python 3.8 and Django 3.0
- Dropped support for Python 3.4 and Django 2.0 and 2.1
- Addressed a ``prefetch_related`` crash against implicit ``related_name`` (#41)
- Prevented sealed accesses on related queryset indexing (#42, #43)

1.2.0, 1.2.1, 1.2.2
===================
:release-date: 2020-02-23

- Botched releases

1.1.0
=====
:release-date: 2019-02-20

- Added tested support for Python 3.7
- Added tested support for Django 2.2
- Changed inheritance chain of ``BaseSealableManager`` (#37)

1.0.0
=====
:release-date: 2018-06-05

- Initial release
