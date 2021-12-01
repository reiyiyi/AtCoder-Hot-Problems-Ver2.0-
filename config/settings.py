# 本番環境

from .settings_common import *
import dj_database_url

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
DEBUG_PROPAGATE_EXCEPTIONS = True

ALLOWED_HOSTS = ['new-hot-problems.herokuapp.com']

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

db_from_env = dj_database_url.config()

DATABASES = {
    'default': dj_database_url.config()
}