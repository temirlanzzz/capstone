"""
WSGI config for agricloud project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from celery import current_app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agricloud.settings')

application = get_wsgi_application()
current_app.conf.update(task_always_eager=False)
