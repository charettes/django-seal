#!/usr/bin/env python
from __future__ import unicode_literals

from setuptools import find_packages, setup

setup(
    name='django-seal',
    version='1.1.0',
    description=(
        'Allows ORM constructs to be sealed to prevent them from executing '
        'queries on attribute accesses.'
    ),
    url='https://github.com/charettes/django-seal',
    author='Simon Charette',
    author_email='simon.charette@zapier.com',
    install_requires=[
        'Django>=1.11',
    ],
    packages=find_packages(exclude=['tests', 'tests.*']),
    license='MIT License',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
