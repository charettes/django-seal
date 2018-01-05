from __future__ import unicode_literals

SECRET_KEY = 'not-secret-anymore'

TIME_ZONE = 'America/Montreal'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    },
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'seal',
    'tests',
]
