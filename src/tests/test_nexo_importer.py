"""Tests for the Nexo Portal importer."""

from decimal import Decimal
from pathlib import Path

import pytest

from apps.properties.models import ImportRun, Property
from apps.properties.services.importers import NexoImporter


@pytest.mark.django_db
def test_run_creates_properties_from_portal_catalog(nexo_feed: Path) -> None:
    import_run = NexoImporter().run()

    assert import_run.status == ImportRun.Status.SUCCESS
    assert import_run.created_count == 3
    assert Property.objects.count() == 3


@pytest.mark.django_db
def test_run_skips_listing_without_price(nexo_feed: Path) -> None:
    import_run = NexoImporter().run()

    assert import_run.skipped_count == 1
    assert not Property.objects.filter(external_id="NX-11288").exists()


@pytest.mark.django_db
def test_run_updates_property_already_imported(nexo_feed: Path) -> None:
    NexoImporter().run()
    Property.objects.filter(external_id="NX-10233").update(price=Decimal("1.00"))

    NexoImporter().run()

    property_ = Property.objects.get(external_id="NX-10233")
    assert property_.price == Decimal("1250000.00")
    assert Property.objects.count() == 3


@pytest.mark.django_db
def test_run_marks_unavailable_listing_as_inactive(nexo_feed: Path) -> None:
    NexoImporter().run()

    assert Property.objects.get(external_id="NX-10488").is_active is False


@pytest.mark.django_db
def test_run_saves_listing_photos_in_portal_order(nexo_feed: Path) -> None:
    NexoImporter().run()

    property_ = Property.objects.get(external_id="NX-10233")
    assert list(property_.photos.values_list("url", flat=True)) == [
        "https://fotos.portalnexo.com.br/NX-10233/01.jpg",
        "https://fotos.portalnexo.com.br/NX-10233/02.jpg",
        "https://fotos.portalnexo.com.br/NX-10233/03.jpg",
    ]


@pytest.mark.django_db
def test_run_replaces_photos_of_property_already_imported(nexo_feed: Path) -> None:
    NexoImporter().run()

    NexoImporter().run()

    assert Property.objects.get(external_id="NX-10233").photos.count() == 3


@pytest.mark.django_db
def test_run_fails_when_feed_is_missing(tmp_path: Path) -> None:
    import_run = NexoImporter(feed_path=tmp_path / "inexistente.xml").run()

    assert import_run.status == ImportRun.Status.FAILED
    assert import_run.error_message


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.250.000,00", Decimal("1250000.00")),
        ("3.400,00", Decimal("3400.00")),
        ("890,50", Decimal("890.50")),
        ("450000", Decimal("450000")),
    ],
)
def test_parse_price_accepts_portal_format(raw: str, expected: Decimal) -> None:
    assert NexoImporter()._parse_price(raw) == expected


def test_parse_price_returns_none_for_invalid_value() -> None:
    assert NexoImporter()._parse_price("sob consulta") is None


def test_build_address_joins_available_parts() -> None:
    address = NexoImporter()._build_address(
        {"logradouro": "Rua Pernambuco", "numero": "1255", "complemento": ""}
    )

    assert address == "Rua Pernambuco, 1255"
