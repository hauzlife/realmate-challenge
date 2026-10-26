"""Tests for the Vitrine Imoveis importer."""

from pathlib import Path

import pytest

from apps.properties.models import ImportRun, Property
from apps.properties.services.importers import VitrineImporter


@pytest.mark.django_db
def test_run_creates_properties_from_portal_catalog(vitrine_feed: Path) -> None:
    import_run = VitrineImporter().run()

    assert import_run.status == ImportRun.Status.SUCCESS
    assert import_run.created_count == 3
    assert Property.objects.count() == 3


@pytest.mark.django_db
def test_run_skips_listing_without_price(vitrine_feed: Path) -> None:
    import_run = VitrineImporter().run()

    assert import_run.skipped_count == 1
    assert not Property.objects.filter(external_id="VT-4802").exists()


@pytest.mark.django_db
def test_run_updates_property_already_imported(vitrine_feed: Path) -> None:
    VitrineImporter().run()
    Property.objects.filter(external_id="VT-4471").update(title="titulo antigo")

    VitrineImporter().run()

    property_ = Property.objects.get(external_id="VT-4471")
    assert property_.title == "Apartamento 3 quartos no Buritis"
    assert Property.objects.count() == 3


@pytest.mark.django_db
def test_run_marks_unavailable_listing_as_inactive(vitrine_feed: Path) -> None:
    VitrineImporter().run()

    assert Property.objects.get(external_id="VT-4519").is_active is False


@pytest.mark.django_db
def test_run_saves_listing_photos_in_portal_order(vitrine_feed: Path) -> None:
    VitrineImporter().run()

    property_ = Property.objects.get(external_id="VT-4471")
    assert list(property_.photos.values_list("url", flat=True)) == [
        "https://fotos.vitrineimoveis.com.br/VT-4471/01.jpg",
        "https://fotos.vitrineimoveis.com.br/VT-4471/02.jpg",
        "https://fotos.vitrineimoveis.com.br/VT-4471/03.jpg",
    ]


@pytest.mark.django_db
def test_run_replaces_photos_of_property_already_imported(vitrine_feed: Path) -> None:
    VitrineImporter().run()

    VitrineImporter().run()

    assert Property.objects.get(external_id="VT-4471").photos.count() == 3


@pytest.mark.django_db
def test_run_fails_when_feed_is_missing(tmp_path: Path) -> None:
    import_run = VitrineImporter(feed_path=tmp_path / "inexistente.json").run()

    assert import_run.status == ImportRun.Status.FAILED
    assert import_run.error_message


def test_build_address_joins_available_parts() -> None:
    address = VitrineImporter()._build_address(
        {"rua": "Rua Fernandes Tourinho", "num": "88", "compl": ""}
    )

    assert address == "Rua Fernandes Tourinho, 88"
