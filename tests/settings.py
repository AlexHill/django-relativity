
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
    },
}

INSTALLED_APPS = [
    'testapp',
]

SECRET_KEY = 'test_secret_key'

TEST_NON_SERIALIZED_APPS = ['testapp']

DEBUG = True
