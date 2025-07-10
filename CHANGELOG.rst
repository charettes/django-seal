1.7.1
=====
:release-date: 2025-07-10

- Document and check that ``'seal'`` must be part of ``INSTALLED_APPS`` (#85).

1.7.0
=====
:release-date: 2025-07-08

- Drop support for Python < 3.9.
- Add tested support for Django 5.2 and Python 3.13.
- Lift restriction on ``django.contrib.contenttypes`` being installed (#84).
- Ensure ``UnsealedAttributeAccess`` propagates through ``getattr`` (#83).

1.6.3
=====
:release-date: 2024-09-05

- Address a crash on unrestricted ``select_related()`` usage (#81)

1.6.2
=====
:release-date: 2024-08-12

- Add tested support for Django 5.1 and Python 3.12.
- Drop support for Python < 3.8 and Django < 4.2.

1.6.1
=====
:release-date: 2023-09-21

- Add tested support for Django 5.0 (#78)
- Adjust declarative sealing to respect MRO (#77)

1.6.0
=====
:release-date: 2023-08-26

- Add declarative sealing for models and managers (#74)

1.5.1
=====
:release-date: 2023-04-26

- Fixed a bug when pickling related queryset of sealed objects (#71)

1.5.0
=====
:release-date: 2023-02-20

- Added tested support for Python 3.10, 3.11 and Django 4.0, 4.1, and 4.2.
- Dropped support for Python < 3.7 and Django < 3.2.

1.4.4
=====
:release-date: 2021-07-30

- Fixed a bug with prefetching of sealed models reverse one-to-one
  descriptors (#65)

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
