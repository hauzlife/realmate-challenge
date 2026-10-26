"""Celery application bootstrap, shared by the worker and the beat scheduler."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("properties_portal")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
