"""Importer for the catalog published by the Vitrine Imoveis portal."""

import json
import logging
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.properties.models import ImportRun, Property
from apps.properties.services.importers.base import BasePortalImporter

logger = logging.getLogger(__name__)

TRANSACTION_BY_PORTAL_VALUE = {
    "venda": Property.Transaction.SALE,
    "locacao": Property.Transaction.RENT,
}

REQUIRED_FIELDS = ("referencia", "nome", "negocio", "preco", "localizacao")


class VitrineImporter(BasePortalImporter):
    """Imports the property catalog published by Vitrine Imoveis.

    The portal publishes the partner's whole catalog as a JSON file, which it
    regenerates overnight. Listings we already know are updated in place and
    the remaining ones are created. Listings that are no longer offered stay in
    our database, flagged as inactive, so their history is not lost.
    """

    source = Property.Source.VITRINE
    portal_name = "Vitrine"
    external_id_field = "referencia"
    required_fields = REQUIRED_FIELDS
    transaction_by_portal_value = TRANSACTION_BY_PORTAL_VALUE
    read_exceptions = (OSError, json.JSONDecodeError)

    def __init__(self, feed_path: Path | str | None = None) -> None:
        """Build the importer.

        Args:
            feed_path: Location of the JSON catalog. Defaults to the path
                configured in `settings.VITRINE_FEED_PATH`.
        """
        super().__init__(Path(feed_path or settings.VITRINE_FEED_PATH))

    def _read_listings(self) -> list[dict[str, Any]]:
        """Read the feed and return one dictionary per listing.

        Returns:
            The listings found in the catalog, still using the portal's own
            field names and raw values.
        """
        with self.feed_path.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        listings: list[dict[str, Any]] = payload.get("imoveis") or []
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

        photo_urls = listing.get("fotos") or []
        self._save_property(external_id, fields, photo_urls, import_run)

    def _is_available(self, listing: dict[str, Any]) -> bool:
        """Tell whether the listing is still being offered by the portal."""
        return str(listing.get("status", "")).lower() == "ativo"

    def _build_address(self, location: dict[str, Any]) -> str:
        """Join the address parts the portal sends separately into one line.

        Args:
            location: The location node of the listing.

        Returns:
            Street, number and complement joined by commas, skipping whichever
            of them the portal left empty.
        """
        return self._join_address_parts(
            location.get("rua", ""),
            location.get("num", ""),
            location.get("compl", ""),
        )
