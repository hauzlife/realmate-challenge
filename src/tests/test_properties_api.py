"""Tests for the public catalog API."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.properties.models import Property


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def sale_property(db: None) -> Property:
    return Property.objects.create(
        source=Property.Source.NEXO,
        external_id="NX-1",
        title="Apartamento 2 quartos",
        transaction=Property.Transaction.SALE,
        price=Decimal("500000.00"),
        bedrooms=2,
        address="Rua A, 100",
        city="Belo Horizonte",
        state="MG",
    )


@pytest.mark.django_db
def test_list_returns_active_properties(api_client: APIClient, sale_property: Property) -> None:
    response = api_client.get("/api/properties/")

    assert response.status_code == 200
    assert response.json()["count"] == 1


@pytest.mark.django_db
def test_list_hides_inactive_properties(api_client: APIClient, sale_property: Property) -> None:
    Property.objects.filter(id=sale_property.id).update(is_active=False)

    response = api_client.get("/api/properties/")

    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_list_filters_by_min_price(api_client: APIClient, sale_property: Property) -> None:
    response = api_client.get("/api/properties/", {"min_price": "600000"})

    assert response.json()["count"] == 0
