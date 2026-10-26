"""Importer for the catalog published by the Nexo Portal."""

import logging
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from django.conf import settings

from apps.properties.models import ImportRun, Property
from apps.properties.services.importers.base import BasePortalImporter

logger = logging.getLogger(__name__)

TRANSACTION_BY_PORTAL_VALUE = {
    "venda": Property.Transaction.SALE,
    "aluguel": Property.Transaction.RENT,
}

REQUIRED_FIELDS = ("codigo", "titulo", "tipo_negocio", "valor", "endereco")


class NexoImporter(BasePortalImporter):
    """Imports the property catalog published by the Nexo Portal.

    The portal publishes the partner's whole catalog as an XML file, which it
    regenerates overnight. Listings we already know are updated in place and
    the remaining ones are created. Listings that are no longer offered stay in
    our database, flagged as inactive, so their history is not lost.
    """

    source = Property.Source.NEXO
    portal_name = "Nexo Portal"
    external_id_field = "codigo"
    required_fields = REQUIRED_FIELDS
    transaction_by_portal_value = TRANSACTION_BY_PORTAL_VALUE
    read_exceptions = (OSError, ElementTree.ParseError)

    def __init__(self, feed_path: Path | str | None = None) -> None:
        """Build the importer.

        Args:
            feed_path: Location of the XML catalog. Defaults to the path
                configured in `settings.NEXO_FEED_PATH`.
        """
        super().__init__(Path(feed_path or settings.NEXO_FEED_PATH))

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

        photo_urls = listing.get("fotos") or []
        self._save_property(external_id, fields, photo_urls, import_run)

    def _is_available(self, listing: dict[str, Any]) -> bool:
        """Tell whether the listing is still being offered by the portal."""
        return str(listing.get("situacao", "")).lower() == "disponivel"

    def _build_address(self, address: dict[str, Any]) -> str:
        """Join the address parts the portal sends separately into one line.

        Args:
            address: The address node of the listing.

        Returns:
            Street, number and complement joined by commas, skipping whichever
            of them the portal left empty.
        """
        return self._join_address_parts(
            address.get("logradouro", ""),
            address.get("numero", ""),
            address.get("complemento", ""),
        )
