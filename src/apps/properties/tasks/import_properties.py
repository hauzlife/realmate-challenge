"""Asynchronous entrypoints for the portal imports."""

import logging

from celery import shared_task

from apps.properties.services.importers import NexoImporter

logger = logging.getLogger(__name__)


@shared_task(name="properties.import_nexo")
def import_nexo_properties() -> None:
    """Sync the Nexo Portal catalog with our database.

    Scheduled by Celery Beat. The importer owns the business rules; this task
    is only the asynchronous entrypoint.
    """
    import_run = NexoImporter().run()
    logger.info("ImportRun %s finished with status %s", import_run.id, import_run.status)
