"""Importer for the catalog published by the Vitrine Imoveis portal."""

import json
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.properties.models import ImportRun, Property, PropertyPhoto

logger = logging.getLogger(__name__)

TRANSACTION_BY_PORTAL_VALUE = {
    "venda": Property.Transaction.SALE,
    "locacao": Property.Transaction.RENT,
}

REQUIRED_FIELDS = ("referencia", "nome", "negocio", "preco", "localizacao")


class VitrineImporter:
    """Imports the property catalog published by Vitrine Imoveis.

    The portal publishes the partner's whole catalog as a JSON file, which it
    regenerates overnight. Listings we already know are updated in place and
    the remaining ones are created. Listings that are no longer offered stay in
    our database, flagged as inactive, so their history is not lost.
    """

    source = Property.Source.VITRINE

    def __init__(self, feed_path: Path | str | None = None) -> None:
        """Build the importer.

        Args:
            feed_path: Location of the JSON catalog. Defaults to the path
                configured in `settings.VITRINE_FEED_PATH`.
        """
        self.feed_path = Path(feed_path or settings.VITRINE_FEED_PATH)

    def run(self) -> ImportRun:
        """Import the whole catalog and record the outcome.

        Returns:
            The `ImportRun` describing this execution, already closed with its
            final status and counters. A feed that cannot be read produces a
            failed run rather than an exception.
        """
        import_run = ImportRun.objects.create(source=self.source)
        logger.info("Starting Vitrine import (run %s) from %s", import_run.id, self.feed_path)

        try:
            listings = self._read_listings()
        except (OSError, json.JSONDecodeError) as exc:
            logger.exception("Could not read the Vitrine catalog at %s", self.feed_path)
            import_run.status = ImportRun.Status.FAILED
            import_run.error_message = str(exc)
            import_run.finished_at = timezone.now()
            import_run.save(update_fields=["status", "error_message", "finished_at"])
            return import_run

        for listing in listings:
            self._import_listing(listing, import_run)

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
            "Vitrine import finished: %s created, %s updated, %s skipped",
            import_run.created_count,
            import_run.updated_count,
            import_run.skipped_count,
        )
        return import_run

    def _read_listings(self) -> list[dict[str, Any]]:
        """Read the feed and return one dictionary per listing.

        Returns:
            The listings found in the catalog, still using the portal's own
            field names and raw values.
        """
        with self.feed_path.open() as handle:
            payload = json.load(handle)

        listings: list[dict[str, Any]] = payload.get("imoveis", [])
        return listings

    def _import_listing(self, listing: dict[str, Any], import_run: ImportRun) -> None:
        """Normalise one listing and store it, updating the run counters.

        A listing missing a required field, priced with a value we cannot read,
        or offered under a transaction type we do not support is skipped and
        logged instead of interrupting the import.

        Args:
            listing: The listing as published by the portal.
            import_run: The run in progress, whose counters are updated in place.
        """
        external_id = str(listing.get("referencia", "")).strip()

        if not self._is_complete(listing):
            logger.warning("Listing %s skipped: required fields are missing", external_id)
            import_run.skipped_count += 1
            return

        price = self._parse_price(listing["preco"])
        if price is None:
            logger.warning("Listing %s skipped: unreadable price %r", external_id, listing["preco"])
            import_run.skipped_count += 1
            return

        transaction = TRANSACTION_BY_PORTAL_VALUE.get(str(listing["negocio"]).lower())
        if transaction is None:
            logger.warning(
                "Listing %s skipped: unknown transaction type %r",
                external_id,
                listing["negocio"],
            )
            import_run.skipped_count += 1
            return

        location = listing["localizacao"]
        fields = {
            "title": listing["nome"],
            "description": listing.get("detalhes", ""),
            "transaction": transaction,
            "price": price,
            "bedrooms": self._parse_int(listing.get("quartos")) or 0,
            "bathrooms": self._parse_int(listing.get("banheiros")) or 0,
            "parking_spaces": self._parse_int(listing.get("garagem")) or 0,
            "area_m2": self._parse_int(listing.get("metragem")),
            "address": self._build_address(location),
            "neighborhood": location.get("bairro", ""),
            "city": location.get("municipio", ""),
            "state": location.get("estado", ""),
            "is_active": self._is_available(listing),
        }

        photo_urls = listing.get("fotos", [])
        existing = Property.objects.filter(source=self.source, external_id=external_id).first()

        if existing is None:
            created = Property.objects.create(source=self.source, external_id=external_id, **fields)
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
        property_.photos.all().delete()
        PropertyPhoto.objects.bulk_create(
            PropertyPhoto(property=property_, url=url, position=position)
            for position, url in enumerate(urls)
        )

    def _is_complete(self, listing: dict[str, Any]) -> bool:
        """Tell whether the listing carries every field we need to store it."""
        return all(listing.get(field) for field in REQUIRED_FIELDS)

    def _is_available(self, listing: dict[str, Any]) -> bool:
        """Tell whether the listing is still being offered by the portal."""
        return str(listing.get("status", "")).lower() == "ativo"

    def _parse_price(self, raw: Any) -> Decimal | None:
        """Convert the portal price into a Decimal.

        Vitrine sends the price as text ("845000,00"), so it has to be cleaned
        up before it reaches the model.

        Args:
            raw: The price exactly as published by the portal.

        Returns:
            The parsed amount, or None when the text is not a number.
        """
        normalized = str(raw).strip().replace(",", "")
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

    def _build_address(self, location: dict[str, Any]) -> str:
        """Join the address parts the portal sends separately into one line.

        Args:
            location: The location node of the listing.

        Returns:
            Street, number and complement joined by commas, skipping whichever
            of them the portal left empty.
        """
        street = str(location.get("rua", "")).strip()
        number = str(location.get("num", "")).strip()
        complement = str(location.get("compl", "")).strip()

        parts = [part for part in (street, number, complement) if part]
        return ", ".join(parts)
