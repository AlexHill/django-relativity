import environ

env = environ.Env()
DATABASES = {'default': env.db(default="sqlite:///")}

INSTALLED_APPS = ["tests"]

SECRET_KEY = "test_secret_key"

TEST_NON_SERIALIZED_APPS = ["tests"]

DEBUG = True
