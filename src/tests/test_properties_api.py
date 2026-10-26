"""BDD step definitions and scenarios for the public catalog API (specs/properties_api.feature)."""

import json
from decimal import Decimal
from typing import Any

import allure
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from pytest_bdd import given, parsers, scenario, then, when
from rest_framework.test import APIClient

from apps.properties.models import Property, PropertyPhoto

FEATURE_FILE = "properties_api.feature"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


# ============================================================================
# Scenarios bound to specs/properties_api.feature
# ============================================================================


@allure.epic("API Pública de Imóveis")
@allure.feature("Listagem e Consulta de Catálogo (/api/properties/)")
@allure.story("Exibição de Imóveis Ativos")
@allure.severity(allure.severity_level.BLOCKER)
@allure.tag("api", "rest", "catalog", "bdd")
@allure.title("GET /api/properties/ retorna imóveis ativos paginados com rótulos legíveis")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "GET /api/properties/ retorna imóveis ativos paginados com rótulos legíveis",
)
def test_list_returns_active_properties() -> None:
    """Scenario: GET /api/properties/ retorna imóveis ativos paginados com rótulos legíveis."""


@allure.epic("API Pública de Imóveis")
@allure.feature("Listagem e Consulta de Catálogo (/api/properties/)")
@allure.story("Ocultação de Imóveis Inativos")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("api", "security", "inactive", "bdd")
@allure.title("GET /api/properties/ omite imóveis marcados como inativos (is_active=False)")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "GET /api/properties/ omite imóveis marcados como inativos",
)
def test_list_hides_inactive_properties() -> None:
    """Scenario: GET /api/properties/ omite imóveis marcados como inativos."""


@allure.epic("API Pública de Imóveis")
@allure.feature("Filtros de Busca do Catálogo (/api/properties/)")
@allure.story("Filtragem por Faixa de Preço, Quartos, Cidade e Transação")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("api", "filters", "min_price", "bdd")
@allure.title("Filtro min_price exclui imóveis abaixo do valor mínimo solicitado")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Filtro min_price exclui imóveis abaixo do valor mínimo solicitado",
)
def test_list_filters_by_min_price() -> None:
    """Scenario: Filtro min_price exclui imóveis abaixo do valor mínimo solicitado."""


@allure.epic("API Pública de Imóveis")
@allure.feature("Filtros de Busca do Catálogo (/api/properties/)")
@allure.story("Filtragem por Faixa de Preço, Quartos, Cidade e Transação")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("api", "filters", "combined-filters", "bdd")
@allure.title("Filtros combinados (city, transaction, max_price, min_bedrooms) refinam o catálogo")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Filtros combinados refinam o catálogo por cidade, transação, preço máximo e quartos mínimos",
)
def test_list_filters_by_city_transaction_max_price_and_bedrooms() -> None:
    """Scenario: Filtros combinados refinam o catálogo na API."""


@allure.epic("API Pública de Imóveis")
@allure.feature("Listagem e Consulta de Catálogo (/api/properties/)")
@allure.story("Exibição de Fotos do Imóvel e Eficiência SQL")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("api", "photos", "n-plus-one", "bdd")
@allure.title("GET /api/properties/ inclui fotos ordenadas sem introduzir queries N+1 por imóvel")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "GET /api/properties/ inclui fotos ordenadas sem introduzir queries N+1 por imóvel",
)
def test_list_includes_property_photos() -> None:
    """Scenario: GET /api/properties/ inclui fotos ordenadas sem introduzir queries N+1."""


# ============================================================================
# Step Definitions (Given / When / Then)
# ============================================================================


@given(
    parsers.parse(
        'que existe um imóvel ativo "{external_id}" à venda em "{city}" '
        'por "{price}" com {bedrooms:d} quartos'
    ),
    target_fixture="sale_property",
)
@allure.title(
    "🎬 DADO QUE existe um imóvel ativo {external_id} à venda em {city} "
    "por R$ {price} ({bedrooms} quartos)"
)
def given_active_sale_property(
    external_id: str, city: str, price: str, bedrooms: int
) -> Property:
    return Property.objects.create(
        source=Property.Source.NEXO,
        external_id=external_id,
        title=f"Apartamento {bedrooms} quartos",
        transaction=Property.Transaction.SALE,
        price=Decimal(price),
        bedrooms=bedrooms,
        address="Rua A, 100",
        city=city,
        state="MG",
    )


@given(parsers.parse('que o imóvel "{external_id}" foi desativado na base'))
@allure.title("🎬 DADO QUE o imóvel {external_id} foi desativado na base (is_active=False)")
def given_property_is_deactivated(external_id: str) -> None:
    Property.objects.filter(external_id=external_id).update(is_active=False)


@given(
    parsers.parse(
        'que existe também um imóvel ativo "{external_id}" para aluguel em "{city}" '
        'por "{price}" com {bedrooms:d} quarto'
    )
)
@allure.title(
    "🎬 DADO QUE existe também um imóvel ativo {external_id} para aluguel em {city} por R$ {price}"
)
def given_active_rent_property(
    external_id: str, city: str, price: str, bedrooms: int
) -> None:
    Property.objects.create(
        source=Property.Source.NEXO,
        external_id=external_id,
        title="Studio Centro",
        transaction=Property.Transaction.RENT,
        price=Decimal(price),
        bedrooms=bedrooms,
        address="Av Paulista, 1000",
        city=city,
        state="SP",
    )


@when(parsers.parse('o cliente consulta GET "{endpoint}"'), target_fixture="api_result")
@allure.title("⚡ QUANDO o cliente consulta GET {endpoint}")
def when_client_queries_endpoint(
    api_client: APIClient, endpoint: str
) -> dict[str, Any]:
    response = api_client.get(endpoint)
    payload = response.json()
    allure.attach(
        json.dumps(payload, indent=2, ensure_ascii=False),
        name="api_response.json",
        attachment_type=allure.attachment_type.JSON,
    )
    return {"status_code": response.status_code, "payload": payload}


@when(
    parsers.parse('o cliente consulta GET "{endpoint}" com o filtro min_price "{min_price}"'),
    target_fixture="api_result",
)
@allure.title("⚡ QUANDO o cliente consulta GET {endpoint}?min_price={min_price}")
def when_client_queries_with_min_price(
    api_client: APIClient, endpoint: str, min_price: str
) -> dict[str, Any]:
    response = api_client.get(endpoint, {"min_price": min_price})
    payload = response.json()
    allure.attach(
        json.dumps(payload, indent=2, ensure_ascii=False),
        name="api_min_price_response.json",
        attachment_type=allure.attachment_type.JSON,
    )
    return {"status_code": response.status_code, "payload": payload}


@when("o cliente aplica os filtros combinados na API:", target_fixture="api_result")
@allure.title("⚡ QUANDO o cliente aplica os filtros combinados na API")
def when_client_applies_combined_filters(
    api_client: APIClient, datatable: list[list[str]]
) -> dict[str, Any]:
    query_params = {row[0]: row[1] for row in datatable[1:]}
    response = api_client.get("/api/properties/", query_params)
    payload = response.json()
    allure.attach(
        json.dumps(payload, indent=2, ensure_ascii=False),
        name="api_filtered_response.json",
        attachment_type=allure.attachment_type.JSON,
    )
    return {"status_code": response.status_code, "payload": payload}


@then(
    parsers.parse(
        "a API responde HTTP {expected_status:d} com count igual a {expected_count:d}"
    )
)
@allure.title("🎯 ENTÃO a API responde HTTP {expected_status} com count igual a {expected_count}")
def then_api_responds_with_count(
    api_result: dict[str, Any], expected_status: int, expected_count: int
) -> None:
    assert api_result["status_code"] == expected_status
    assert api_result["payload"]["count"] == expected_count


@then(
    parsers.parse(
        "a API responde HTTP {expected_status:d} com count igual a {expected_count:d} e lista vazia"
    )
)
@allure.title(
    "🎯 ENTÃO a API responde HTTP {expected_status} com count igual a "
    "{expected_count} e lista vazia"
)
def then_api_responds_with_empty_list(
    api_result: dict[str, Any], expected_status: int, expected_count: int
) -> None:
    assert api_result["status_code"] == expected_status
    assert api_result["payload"]["count"] == expected_count
    assert api_result["payload"]["results"] == []


@then(
    parsers.parse(
        'o primeiro item retornado possui external_id "{external_id}", '
        'source "{source}" e transaction "{transaction}"'
    )
)
@allure.title(
    "🛡️ E o item serializado exibe external_id '{external_id}', "
    "source '{source}' e transaction '{transaction}'"
)
def then_first_item_has_expected_labels(
    api_result: dict[str, Any], external_id: str, source: str, transaction: str
) -> None:
    item = api_result["payload"]["results"][0]
    assert item["external_id"] == external_id
    assert item["source"] == source
    assert item["transaction"] == transaction


@then(parsers.parse('apenas o imóvel "{external_id}" é retornado na listagem'))
@allure.title("🛡️ E apenas o imóvel {external_id} é retornado na listagem")
def then_only_expected_property_is_returned(
    api_result: dict[str, Any], external_id: str
) -> None:
    results = api_result["payload"]["results"]
    assert len(results) == 1
    assert results[0]["external_id"] == external_id


@given(
    parsers.parse(
        'que o imóvel "{external_id}" possui as fotos "{url_1}" e "{url_2}"'
    )
)
@allure.title("🎬 DADO QUE o imóvel {external_id} possui 2 fotos cadastradas")
def given_property_has_two_photos(external_id: str, url_1: str, url_2: str) -> None:
    prop = Property.objects.get(external_id=external_id)
    PropertyPhoto.objects.create(property=prop, url=url_1, position=0)
    PropertyPhoto.objects.create(property=prop, url=url_2, position=1)


@when(
    parsers.parse('o cliente consulta GET "{endpoint}" monitorando o número de queries SQL'),
    target_fixture="api_result",
)
@allure.title("⚡ QUANDO o cliente consulta GET {endpoint} monitorando queries SQL")
def when_client_queries_endpoint_monitoring_sql(
    api_client: APIClient, endpoint: str
) -> dict[str, Any]:
    with CaptureQueriesContext(connection) as ctx:
        response = api_client.get(endpoint)
    payload = response.json()
    allure.attach(
        json.dumps(
            {
                "sql_count": len(ctx.captured_queries),
                "queries": [q["sql"] for q in ctx.captured_queries],
                "payload": payload,
            },
            indent=2,
            ensure_ascii=False,
        ),
        name="api_photos_sql_trace.json",
        attachment_type=allure.attachment_type.JSON,
    )
    return {
        "status_code": response.status_code,
        "payload": payload,
        "sql_count": len(ctx.captured_queries),
    }


@then(
    parsers.parse(
        'a API devolve as URLs das fotos do imóvel "{external_id}" na ordem cadastrada'
    )
)
@allure.title(
    "🎯 ENTÃO a API devolve as URLs das fotos do imóvel {external_id} na ordem cadastrada"
)
def then_api_returns_ordered_photos(api_result: dict[str, Any], external_id: str) -> None:
    results = api_result["payload"]["results"]
    item = next(r for r in results if r["external_id"] == external_id)
    assert item["photos"] == [
        "https://fotos.vitrineimoveis.com.br/VT-1/01.jpg",
        "https://fotos.vitrineimoveis.com.br/VT-1/02.jpg",
    ]


@then(
    parsers.parse(
        "a listagem executa no máximo {max_queries:d} queries SQL sem N+1 em PropertyPhoto"
    )
)
@allure.title(
    "🛡️ E a listagem executa no máximo {max_queries} queries SQL sem N+1 em PropertyPhoto"
)
def then_api_executes_at_most_queries(api_result: dict[str, Any], max_queries: int) -> None:
    assert api_result["sql_count"] <= max_queries, (
        f"N+1 queries detectadas ao serializar photos: {api_result['sql_count']} queries "
        f"executadas (esperado <= {max_queries} com prefetch_related('photos'))"
    )
