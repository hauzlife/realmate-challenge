"""Django app declaration for the properties domain."""

from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    """Django app holding the property catalog and the portal importers."""

    name = "apps.properties"
    verbose_name = "Properties"
