"""Shared base importer for partner property catalogs."""

import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.properties.models import ImportRun, Property, PropertyPhoto

logger = logging.getLogger(__name__)


class BasePortalImporter:
    """Common catalog import lifecycle and field normalisation utilities.

    Subclasses provide the portal-specific feed reader and field mapping while
    sharing the `ImportRun` lifecycle, orphan listing deactivation, atomic
    photo replacement, and pt-BR numeric/address parsers.
    """

    source: Property.Source
    portal_name: str
    external_id_field: str
    required_fields: tuple[str, ...]
    transaction_by_portal_value: dict[str, Property.Transaction]
    read_exceptions: tuple[type[Exception], ...] = (OSError,)

    def __init__(self, feed_path: Path) -> None:
        """Store the resolved catalog feed path."""
        self.feed_path = feed_path

    def run(self) -> ImportRun:
        """Import the whole catalog and record the outcome.

        Returns:
            The `ImportRun` describing this execution, already closed with its
            final status and counters. A feed that cannot be read produces a
            failed run rather than an exception.
        """
        import_run = ImportRun.objects.create(source=self.source)
        logger.info(
            "Starting %s import (run %s) from %s",
            self.portal_name,
            import_run.id,
            self.feed_path,
        )

        try:
            listings = self._read_listings()
        except self.read_exceptions as exc:
            logger.exception(
                "Could not read the %s catalog at %s",
                self.portal_name,
                self.feed_path,
            )
            import_run.status = ImportRun.Status.FAILED
            import_run.error_message = str(exc)
            import_run.finished_at = timezone.now()
            import_run.save(update_fields=["status", "error_message", "finished_at"])
            return import_run

        for listing in listings:
            self._import_listing(listing, import_run)

        seen_external_ids = {
            str(listing.get(self.external_id_field, "")).strip()
            for listing in listings
            if str(listing.get(self.external_id_field, "")).strip()
        }
        Property.objects.filter(source=self.source, is_active=True).exclude(
            external_id__in=seen_external_ids
        ).update(is_active=False, updated_at=timezone.now())

        import_run.status = ImportRun.Status.SUCCESS
        import_run.finished_at = timezone.now()
        import_run.save(
            update_fields=[
                "status",
                "finished_at",
                "created_count",
                "updated_count",
                "skipped_count",
            ]
        )
        logger.info(
            "%s import finished: %s created, %s updated, %s skipped",
            self.portal_name,
            import_run.created_count,
            import_run.updated_count,
            import_run.skipped_count,
        )
        return import_run

    def _read_listings(self) -> list[dict[str, Any]]:
        """Read the partner feed and return raw listing dictionaries."""
        raise NotImplementedError  # pragma: no cover

    def _import_listing(self, listing: dict[str, Any], import_run: ImportRun) -> None:
        """Normalise and persist a single partner listing."""
        raise NotImplementedError  # pragma: no cover

    def _save_property(
        self,
        external_id: str,
        fields: dict[str, Any],
        photo_urls: list[str],
        import_run: ImportRun,
    ) -> None:
        """Create or update a `Property` and synchronize its photos atomically."""
        existing = Property.objects.filter(source=self.source, external_id=external_id).first()

        if existing is None:
            created = Property.objects.create(
                source=self.source,
                external_id=external_id,
                **fields,
            )
            self._save_photos(created, photo_urls)
            import_run.created_count += 1
            logger.info("Listing %s created", external_id)
            return

        for name, value in fields.items():
            setattr(existing, name, value)
        existing.save(update_fields=[*fields.keys(), "updated_at"])
        self._save_photos(existing, photo_urls)
        import_run.updated_count += 1
        logger.info("Listing %s updated", external_id)

    def _save_photos(self, property_: Property, urls: list[str]) -> None:
        """Replace the photos of a listing with the ones the portal publishes now.

        Args:
            property_: The listing the photos belong to.
            urls: The photo URLs, in the order the portal displays them.
        """
        with transaction.atomic():
            property_.photos.all().delete()
            PropertyPhoto.objects.bulk_create(
                PropertyPhoto(property=property_, url=url, position=position)
                for position, url in enumerate(urls)
            )

    def _is_complete(self, listing: dict[str, Any]) -> bool:
        """Tell whether the listing carries every field we need to store it."""
        return all(listing.get(field) for field in self.required_fields)

    def _parse_price(self, raw: Any) -> Decimal | None:
        """Convert the portal price, written in pt-BR notation, into a Decimal.

        Partner portals send the price with comma as the decimal separator
        (e.g. "1.250.000,00" or "845000,00").

        Args:
            raw: The price exactly as published by the portal.

        Returns:
            The parsed amount, or None when the text is not a number.
        """
        normalized = str(raw).strip().replace(".", "").replace(",", ".")
        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    def _parse_int(self, raw: Any) -> int | None:
        """Convert an optional numeric field into an int.

        Args:
            raw: The value as published by the portal, possibly empty.

        Returns:
            The parsed number, or None when the field is empty or not numeric.
        """
        if raw in (None, ""):
            return None
        try:
            return int(str(raw).strip())
        except ValueError:
            return None

    def _join_address_parts(self, street: Any, number: Any, complement: Any) -> str:
        """Join non-empty street, number, and complement parts with commas."""
        cleaned_street = str(street).strip()
        cleaned_number = str(number).strip()
        cleaned_complement = str(complement).strip()

        parts = [
            part
            for part in (cleaned_street, cleaned_number, cleaned_complement)
            if part
        ]
        return ", ".join(parts)
