"""Importer for the catalog published by the Nexo Portal."""

import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from django.conf import settings
from django.utils import timezone

from apps.properties.models import ImportRun, Property, PropertyPhoto

logger = logging.getLogger(__name__)

TRANSACTION_BY_PORTAL_VALUE = {
    "venda": Property.Transaction.SALE,
    "aluguel": Property.Transaction.RENT,
}

REQUIRED_FIELDS = ("codigo", "titulo", "tipo_negocio", "valor", "endereco")


class NexoImporter:
    """Imports the property catalog published by the Nexo Portal.

    The portal publishes the partner's whole catalog as an XML file, which it
    regenerates overnight. Listings we already know are updated in place and
    the remaining ones are created. Listings that are no longer offered stay in
    our database, flagged as inactive, so their history is not lost.
    """

    source = Property.Source.NEXO

    def __init__(self, feed_path: Path | str | None = None) -> None:
        """Build the importer.

        Args:
            feed_path: Location of the XML catalog. Defaults to the path
                configured in `settings.NEXO_FEED_PATH`.
        """
        self.feed_path = Path(feed_path or settings.NEXO_FEED_PATH)

    def run(self) -> ImportRun:
        """Import the whole catalog and record the outcome.

        Returns:
            The `ImportRun` describing this execution, already closed with its
            final status and counters. A feed that cannot be read produces a
            failed run rather than an exception.
        """
        import_run = ImportRun.objects.create(source=self.source)
        logger.info("Starting Nexo Portal import (run %s) from %s", import_run.id, self.feed_path)

        try:
            listings = self._read_listings()
        except (OSError, ElementTree.ParseError) as exc:
            logger.exception("Could not read the Nexo Portal catalog at %s", self.feed_path)
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
            "Nexo Portal import finished: %s created, %s updated, %s skipped",
            import_run.created_count,
            import_run.updated_count,
            import_run.skipped_count,
        )
        return import_run

    def _read_listings(self) -> list[dict[str, Any]]:
        """Read the feed and return one dictionary per listing.

        Returns:
            The listings found in the catalog, still using the portal's own
            field names and raw text values.
        """
        root = ElementTree.parse(self.feed_path).getroot()
        return [self._element_to_listing(element) for element in root.findall("imovel")]

    def _element_to_listing(self, element: ElementTree.Element) -> dict[str, Any]:
        """Flatten a single `<imovel>` node into a dictionary.

        Args:
            element: The listing node taken from the catalog.

        Returns:
            The listing fields keyed by the portal's tag names. The nested
            address node becomes a dictionary under `endereco` and the photo
            URLs become a list under `fotos`.
        """
        listing: dict[str, Any] = {}

        for child in element:
            if child.tag == "endereco":
                listing["endereco"] = {field.tag: (field.text or "").strip() for field in child}
            elif child.tag == "fotos":
                listing["fotos"] = [(photo.text or "").strip() for photo in child]
            else:
                listing[child.tag] = (child.text or "").strip()

        return listing

    def _import_listing(self, listing: dict[str, Any], import_run: ImportRun) -> None:
        """Normalise one listing and store it, updating the run counters.

        A listing missing a required field, priced with a value we cannot read,
        or offered under a transaction type we do not support is skipped and
        logged instead of interrupting the import.

        Args:
            listing: The listing as published by the portal.
            import_run: The run in progress, whose counters are updated in place.
        """
        external_id = str(listing.get("codigo", "")).strip()

        if not self._is_complete(listing):
            logger.warning("Listing %s skipped: required fields are missing", external_id)
            import_run.skipped_count += 1
            return

        price = self._parse_price(listing["valor"])
        if price is None:
            logger.warning("Listing %s skipped: unreadable price %r", external_id, listing["valor"])
            import_run.skipped_count += 1
            return

        transaction = TRANSACTION_BY_PORTAL_VALUE.get(str(listing["tipo_negocio"]).lower())
        if transaction is None:
            logger.warning(
                "Listing %s skipped: unknown transaction type %r",
                external_id,
                listing["tipo_negocio"],
            )
            import_run.skipped_count += 1
            return

        address = listing["endereco"]
        fields = {
            "title": listing["titulo"],
            "description": listing.get("descricao", ""),
            "transaction": transaction,
            "price": price,
            "bedrooms": self._parse_int(listing.get("dormitorios")) or 0,
            "bathrooms": self._parse_int(listing.get("banheiros")) or 0,
            "parking_spaces": self._parse_int(listing.get("vagas")) or 0,
            "area_m2": self._parse_int(listing.get("area_util")),
            "address": self._build_address(address),
            "neighborhood": address.get("bairro", ""),
            "city": address.get("cidade", ""),
            "state": address.get("uf", ""),
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
        return str(listing.get("situacao", "")).lower() == "disponivel"

    def _parse_price(self, raw: Any) -> Decimal | None:
        """Convert the portal price, written in pt-BR notation, into a Decimal.

        Nexo sends the price as text ("1.250.000,00"): dots separate thousands
        and the comma separates the cents.

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

    def _build_address(self, address: dict[str, Any]) -> str:
        """Join the address parts the portal sends separately into one line.

        Args:
            address: The address node of the listing.

        Returns:
            Street, number and complement joined by commas, skipping whichever
            of them the portal left empty.
        """
        street = str(address.get("logradouro", "")).strip()
        number = str(address.get("numero", "")).strip()
        complement = str(address.get("complemento", "")).strip()

        parts = [part for part in (street, number, complement) if part]
        return ", ".join(parts)
