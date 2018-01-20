"""
WSGI config for get_together project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "get_together.settings")

application = get_wsgi_application()
