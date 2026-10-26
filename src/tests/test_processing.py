"""Tests for the nightly catalog processing."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from apps.properties.models import Property
from apps.properties.tasks.process_properties import process_properties


def create_property(external_id: str, description: str) -> Property:
    return Property.objects.create(
        source=Property.Source.NEXO,
        external_id=external_id,
        title="Apartamento",
        description=description,
        transaction=Property.Transaction.SALE,
        price=Decimal("500000.00"),
        address="Rua A, 100",
        city="Belo Horizonte",
        state="MG",
    )


@pytest.mark.django_db
@patch("apps.properties.services.processing.time.sleep")
def test_process_properties_processes_every_listing(sleep: MagicMock) -> None:
    create_property("NX-1", description="Apartamento na Savassi")
    create_property("NX-2", description="Casa no Sion")

    process_properties()

    descriptions = set(Property.objects.values_list("description", flat=True))
    assert descriptions == {"Processed: Apartamento na Savassi", "Processed: Casa no Sion"}
