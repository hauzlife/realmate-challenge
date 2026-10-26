"""Asynchronous entrypoint for the nightly catalog processing."""

import logging

from celery import shared_task

from apps.properties.models import Property
from apps.properties.services.processing import process_property

logger = logging.getLogger(__name__)


@shared_task(name="properties.process_catalog")
def process_properties() -> None:
    """Run the nightly processing over the whole catalog.

    Scheduled by Celery Beat to run once a night, after the portals have
    republished their catalogs.
    """
    logger.info("Starting catalog processing")

    properties = Property.objects.all()

    for property_ in properties:
        processed_description = process_property(property_.description)
        property_.description = processed_description
        property_.save()

    logger.info("Catalog processing finished: %s listings processed", len(properties))
