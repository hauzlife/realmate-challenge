"""BDD step definitions and scenarios for nightly catalog processing."""

import json
from collections.abc import Iterator
from decimal import Decimal
from unittest.mock import MagicMock, patch

import allure
import pytest
from pytest_bdd import given, parsers, scenario, then, when

from apps.properties.models import Property
from apps.properties.tasks.process_properties import process_properties

FEATURE_FILE = "catalog_processing.feature"


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


@pytest.fixture
def mocked_processing_sleep() -> Iterator[MagicMock]:
    with patch("apps.properties.services.processing.time.sleep") as sleep_mock:
        yield sleep_mock


@allure.epic("Catálogo de Imóveis")
@allure.feature("Processamento Noturno do Catálogo")
@allure.story("Enriquecimento de Descrições em Lote")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("celery", "processing", "nightly-job", "bdd")
@allure.title("Job noturno process_properties enriquece a descrição de todos os anúncios da base")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Job noturno process_properties enriquece a descrição de todos os anúncios da base",
)
def test_process_properties_processes_every_listing() -> None:
    """Scenario: Job noturno process_properties enriquece a descrição dos anúncios."""


@given("que existem os seguintes imóveis cadastrando descrições para processamento noturno:")
@allure.title("🎬 DADO QUE existem imóveis cadastrados aguardando processamento noturno")
def given_properties_awaiting_nightly_processing(datatable: list[list[str]]) -> None:
    for external_id, description in datatable[1:]:
        create_property(external_id, description=description)


@when("a task assíncrona process_properties é executada")
@allure.title("⚡ QUANDO a task assíncrona process_properties é executada")
def when_process_properties_task_runs(mocked_processing_sleep: MagicMock) -> None:
    process_properties()


@then("todas as descrições recebem o prefixo de processamento:")
@allure.title("🎯 ENTÃO todas as descrições recebem o prefixo de processamento")
def then_all_descriptions_are_enriched(datatable: list[list[str]]) -> None:
    descriptions = set(Property.objects.values_list("description", flat=True))
    expected_descriptions = {row[0] for row in datatable[1:]}
    allure.attach(
        json.dumps(sorted(descriptions), indent=2, ensure_ascii=False),
        name="processed_descriptions.json",
        attachment_type=allure.attachment_type.JSON,
    )
    assert descriptions == expected_descriptions


@then(parsers.parse("o worker invoca a rotina de processamento {expected_calls:d} vezes"))
@allure.title("🛡️ E o worker invoca a rotina de processamento {expected_calls} vezes")
def then_worker_invokes_processing_for_every_listing(
    mocked_processing_sleep: MagicMock, expected_calls: int
) -> None:
    assert mocked_processing_sleep.call_count == expected_calls
