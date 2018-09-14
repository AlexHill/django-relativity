
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

INSTALLED_APPS = ["tests"]

SECRET_KEY = "test_secret_key"

TEST_NON_SERIALIZED_APPS = ["tests"]

DEBUG = True
