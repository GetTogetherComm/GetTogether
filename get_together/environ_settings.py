# Use environment variables to configure settings

import os
from get_together.settings import *

DEBUG=os.environ.get('DEBUG_MODE', False)=="True"
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1').split(',')

SECRET_KEY=os.environ.get('SECRET_KEY', '')

# Database configs
import dj_database_url
DATABASES['default'].update(dj_database_url.config())

MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')
STATIC_URL = os.environ.get('STATIC_URL', '/static/')

