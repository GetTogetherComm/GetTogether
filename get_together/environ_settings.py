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

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', True)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'you.smtp.host.com')
EMAIL_PORT = os.environ.get('EMAIL_PORT', 587)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', None)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', None)

SOCIAL_AUTH_GITHUB_KEY = os.environ.get('SOCIAL_AUTH_GITHUB_KEY', None)
SOCIAL_AUTH_GITHUB_SECRET = os.environ.get('SOCIAL_AUTH_GITHUB_SECRET', None)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', None)

SOCIAL_AUTH_FACEBOOK_KEY = os.environ.get('SOCIAL_AUTH_FACEBOOK_KEY', None)
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ.get('SOCIAL_AUTH_FACEBOOK_SECRET', None)

SOCIAL_AUTH_TWITTER_KEY = os.environ.get('SOCIAL_AUTH_TWITTER_KEY', None)
SOCIAL_AUTH_TWITTER_SECRET = os.environ.get('SOCIAL_AUTH_TWITTER_SECRET', None)

SOCIAL_AUTH_LINKEDIN_KEY = os.environ.get('SOCIAL_AUTH_LINKEDIN_KEY', None)
SOCIAL_AUTH_LINKEDIN_SECRET = os.environ.get('SOCIAL_AUTH_LINKEDIN_SECRET', None)

# Needed to embed Google maps for event location
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', None)

# If set, will include Google Analytics javascript in pages
GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', None)

# Free Geoip lookup from ipstack.com still requires an access token
IPSTACK_ACCESS_KEY = os.environ.get('IPSTACK_ACCESS_KEY', None)
