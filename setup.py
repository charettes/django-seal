#!/usr/bin/env python
from setuptools import find_packages, setup

with open('README.rst') as file_:
    long_description = file_.read()

setup(
    name='django-seal',
    version='1.6.3',
    description=(
        'Allows ORM constructs to be sealed to prevent them from executing '
        'queries on attribute accesses.'
    ),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url='https://github.com/charettes/django-seal',
    author='Simon Charette',
    author_email='simon.charette@zapier.com',
    install_requires=[
        'Django>=4.2',
    ],
    packages=find_packages(exclude=['tests', 'tests.*']),
    license='MIT License',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Framework :: Django :: 5.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
