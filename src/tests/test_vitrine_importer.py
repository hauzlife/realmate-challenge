"""BDD step definitions and scenarios for the Vitrine importer (specs/vitrine_importer.feature)."""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import allure
import pytest
from pytest_bdd import given, parsers, scenario, then, when

from apps.properties.models import ImportRun, Property
from apps.properties.services.importers import VitrineImporter
from apps.properties.tasks.import_properties import import_vitrine_properties

FEATURE_FILE = "vitrine_importer.feature"


def _attach_vitrine_run_summary(import_run: ImportRun) -> None:
    allure.attach(
        json.dumps(
            {
                "import_run_id": import_run.id,
                "source": import_run.source,
                "status": import_run.status,
                "created_count": import_run.created_count,
                "updated_count": import_run.updated_count,
                "skipped_count": import_run.skipped_count,
            },
            indent=2,
        ),
        name="vitrine_import_run_summary.json",
        attachment_type=allure.attachment_type.JSON,
    )


# ============================================================================
# Scenarios bound to specs/vitrine_importer.feature
# ============================================================================


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Importação Completa e Precisão Monetária de Catálogo JSON")
@allure.severity(allure.severity_level.BLOCKER)
@allure.tag("importer", "vitrine", "json", "price", "bdd")
@allure.title(
    "Importação inicial cria imóveis válidos com preços precisos "
    "a partir do catálogo JSON do Vitrine Imóveis"
)
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Importação inicial cria imóveis válidos com preços precisos "
    "a partir do catálogo JSON do Vitrine Imóveis",
)
def test_run_creates_properties_from_portal_catalog() -> None:
    """Scenario: Importação inicial cria imóveis válidos com preços precisos."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Validação e Descarte de Anúncios Inválidos")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "vitrine", "validation", "price", "bdd")
@allure.title("Importador do Vitrine ignora anúncio sem preço ('VT-4802') sem abortar o lote")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Importador do Vitrine ignora anúncio sem preço sem abortar o lote",
)
def test_run_skips_listing_without_price() -> None:
    """Scenario: Importador do Vitrine ignora anúncio sem preço sem abortar o lote."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Controle de Disponibilidade de Anúncios")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "vitrine", "availability", "inactive", "bdd")
@allure.title(
    "Anúncio marcado como 'vendido' no JSON do Vitrine é salvo como inativo (is_active=False)"
)
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Anúncio marcado como vendido no JSON do Vitrine é salvo como inativo",
)
def test_run_marks_unavailable_listing_as_inactive() -> None:
    """Scenario: Anúncio marcado como vendido no JSON do Vitrine é salvo como inativo."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Controle de Disponibilidade de Anúncios")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "vitrine", "availability", "inactive", "bdd")
@allure.title(
    "Anúncio do Vitrine removido do JSON em carga subsequente "
    "é marcado como inativo (is_active=False)"
)
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Anúncio do Vitrine removido do JSON em carga subsequente é marcado como inativo",
)
def test_run_deactivates_missing_listing_from_previous_import() -> None:
    """Scenario: Anúncio do Vitrine removido do JSON em carga subsequente é marcado como inativo."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Atualização Idempotente de Anúncios Existentes")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "vitrine", "upsert", "idempotency", "bdd")
@allure.title(
    "Reimportação do Vitrine atualiza dados de imóvel já existente in-place sem duplicar registro"
)
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Reimportação do Vitrine atualiza dados de imóvel já existente in-place sem duplicar registro",
)
def test_run_updates_property_already_imported() -> None:
    """Scenario: Reimportação do Vitrine atualiza dados de imóvel já existente in-place."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Sincronização de Fotos do Imóvel")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("importer", "vitrine", "photos", "ordering", "bdd")
@allure.title(
    "Fotos do anúncio do Vitrine são gravadas respeitando a ordem exata publicada pelo portal"
)
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Fotos do anúncio do Vitrine são gravadas respeitando a ordem exata publicada pelo portal",
)
def test_run_saves_listing_photos_in_portal_order() -> None:
    """Scenario: Fotos do anúncio do Vitrine são gravadas na ordem do portal."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Sincronização de Fotos do Imóvel")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("importer", "vitrine", "photos", "idempotency", "bdd")
@allure.title(
    "Reimportação do Vitrine substitui as fotos do imóvel sem acumular registros duplicados"
)
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Reimportação do Vitrine substitui as fotos do imóvel sem acumular registros duplicados",
)
def test_run_replaces_photos_of_property_already_imported() -> None:
    """Scenario: Reimportação do Vitrine substitui as fotos do imóvel."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Resiliência e Tratamento de Falhas de I/O")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "vitrine", "resilience", "error-handling", "bdd")
@allure.title("Ausência do arquivo JSON registra ImportRun com status FAILED e mensagem de erro")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Ausência do arquivo JSON registra ImportRun com status FAILED e mensagem de erro",
)
def test_run_fails_when_feed_is_missing() -> None:
    """Scenario: Ausência do arquivo JSON registra ImportRun com status FAILED."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Execução via Task Assíncrona Celery")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("celery", "task", "vitrine", "importer", "bdd")
@allure.title("Task Celery import_vitrine_properties aciona o importador e persiste o ImportRun")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Task Celery import_vitrine_properties aciona o importador e persiste o ImportRun",
)
def test_celery_task_import_vitrine_properties_executes_importer() -> None:
    """Scenario: Task Celery import_vitrine_properties aciona o importador."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Normalização de Preços e Endereços")
@allure.severity(allure.severity_level.BLOCKER)
@allure.tag("parser", "vitrine", "price", "pt-br", "bdd")
@allure.title(
    "Conversão de preço no formato do Vitrine ('{raw}') retorna "
    "Decimal('{expected}') sem multiplicar por 100"
)
@scenario(
    FEATURE_FILE,
    "Conversão de preço no formato do Vitrine retorna Decimal normalizado sem multiplicar por 100",
)
def test_parse_price_normalizes_vitrine_format() -> None:
    """Scenario Outline: Conversão de preço no formato do Vitrine retorna Decimal normalizado."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Normalização de Preços e Endereços")
@allure.severity(allure.severity_level.MINOR)
@allure.tag("parser", "vitrine", "address", "bdd")
@allure.title("Formatação de endereço do Vitrine concatena rua, número e complemento disponíveis")
@scenario(
    FEATURE_FILE,
    "Formatação de endereço do Vitrine concatena rua, número e complemento disponíveis",
)
def test_build_address_joins_available_parts() -> None:
    """Scenario: Formatação de endereço do Vitrine concatena partes disponíveis."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Vitrine Imóveis")
@allure.story("Validação e Descarte de Anúncios Inválidos")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("validation", "vitrine", "negative-test", "bdd")
@allure.title(
    "Importador do Vitrine descarta anúncios com preço ilegível ou tipo de negócio desconhecido"
)
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Importador do Vitrine descarta anúncios com preço ilegível ou tipo de negócio desconhecido",
)
def test_vitrine_skips_unreadable_price_and_unknown_transaction() -> None:
    """Scenario: Importador do Vitrine descarta anúncios com preço ilegível ou negócio inválido."""


# ============================================================================
# Step Definitions (Given / When / Then)
# ============================================================================


@given(
    parsers.parse(
        'que o anúncio "{external_id}" do Vitrine estava ativo na base após uma carga anterior'
    )
)
@allure.title(
    "🎬 DADO QUE o anúncio {external_id} do Vitrine estava ativo na base após uma carga anterior"
)
def given_vitrine_property_was_active(external_id: str) -> None:
    Property.objects.create(
        source=Property.Source.VITRINE,
        external_id=external_id,
        title="Cobertura 3 quartos no Anchieta",
        transaction=Property.Transaction.SALE,
        price=Decimal("2340000.00"),
        city="Belo Horizonte",
        state="MG",
        is_active=True,
    )


@given(
    parsers.parse(
        'que o catálogo do Vitrine foi importado e o imóvel "{external_id}" '
        'teve o título alterado para "{old_title}"'
    )
)
@allure.title(
    "🎬 DADO QUE o catálogo do Vitrine foi importado e o imóvel {external_id} "
    "teve o título alterado para '{old_title}'"
)
def given_vitrine_imported_and_title_changed(
    vitrine_feed: Path, external_id: str, old_title: str
) -> None:
    VitrineImporter().run()
    Property.objects.filter(external_id=external_id).update(title=old_title)


@given(
    parsers.parse(
        'que o imóvel "{external_id}" do Vitrine já possui {photo_count:d} fotos importadas'
    )
)
@allure.title(
    "🎬 DADO QUE o imóvel {external_id} do Vitrine já possui {photo_count} fotos importadas"
)
def given_vitrine_property_already_has_photos(
    vitrine_feed: Path, external_id: str, photo_count: int
) -> None:
    VitrineImporter().run()
    assert Property.objects.get(external_id=external_id).photos.count() == photo_count


@given(
    "que o caminho do feed aponta para um arquivo JSON inexistente",
    target_fixture="missing_json_feed_path",
)
@allure.title("🎬 DADO QUE o caminho do feed aponta para um arquivo JSON inexistente")
def given_missing_json_feed_path(tmp_path: Path) -> Path:
    return tmp_path / "inexistente.json"


@given(
    parsers.parse(
        'que a localização do Vitrine possui rua "{rua}", número "{num}" e complemento vazio'
    ),
    target_fixture="raw_vitrine_location",
)
@allure.title(
    "🎬 DADO QUE a localização do Vitrine possui rua '{rua}', número '{num}' e complemento vazio"
)
def given_raw_vitrine_location(rua: str, num: str) -> dict[str, str]:
    return {"rua": rua, "num": num, "compl": ""}


@when("o VitrineImporter executa a importação do catálogo JSON", target_fixture="vitrine_run")
@allure.title("⚡ QUANDO o VitrineImporter executa a importação do catálogo JSON")
def when_vitrine_importer_runs(vitrine_feed: Path) -> ImportRun:
    import_run = VitrineImporter().run()
    _attach_vitrine_run_summary(import_run)
    return import_run


@when(
    "o VitrineImporter tenta executar a importação do arquivo JSON ausente",
    target_fixture="vitrine_run",
)
@allure.title("⚡ QUANDO o VitrineImporter tenta executar a importação do arquivo JSON ausente")
def when_vitrine_importer_runs_missing_file(missing_json_feed_path: Path) -> ImportRun:
    import_run = VitrineImporter(feed_path=missing_json_feed_path).run()
    allure.attach(
        import_run.error_message,
        name="vitrine_error_message.txt",
        attachment_type=allure.attachment_type.TEXT,
    )
    return import_run


@when("a task Celery import_vitrine_properties é disparada")
@allure.title("⚡ QUANDO a task Celery import_vitrine_properties é disparada")
def when_celery_import_vitrine_runs(vitrine_feed: Path) -> None:
    import_vitrine_properties()


@when(
    parsers.parse('VitrineImporter._parse_price recebe o texto "{raw}"'),
    target_fixture="vitrine_parsed_price",
)
@allure.title("⚡ QUANDO VitrineImporter._parse_price recebe o texto '{raw}'")
def when_vitrine_parse_price_runs(raw: str) -> Decimal | None:
    return VitrineImporter()._parse_price(raw)


@when(
    "VitrineImporter._build_address monta a linha de endereço",
    target_fixture="vitrine_formatted_address",
)
@allure.title("⚡ QUANDO VitrineImporter._build_address monta a linha de endereço")
def when_vitrine_build_address_runs(raw_vitrine_location: dict[str, str]) -> str:
    return VitrineImporter()._build_address(raw_vitrine_location)


@then(
    parsers.parse(
        'a execução do Vitrine fecha com status "{expected_status}" '
        "e {expected_created:d} imóveis criados"
    )
)
@allure.title(
    "🎯 ENTÃO a execução do Vitrine fecha com status {expected_status} "
    "e {expected_created} imóveis criados"
)
def then_vitrine_run_succeeds(
    vitrine_run: ImportRun, expected_status: str, expected_created: int
) -> None:
    assert vitrine_run.status == expected_status
    assert vitrine_run.created_count == expected_created


@then(
    parsers.parse(
        'a base de dados persiste {expected_count:d} anúncios da fonte VITRINE '
        'com o imóvel "{external_id}" custando "{expected_price}"'
    )
)
@allure.title(
    "🛡️ E a base persiste {expected_count} anúncios VITRINE com "
    "{external_id} custando R$ {expected_price}"
)
def then_vitrine_properties_persisted_with_exact_price(
    expected_count: int, external_id: str, expected_price: str
) -> None:
    assert Property.objects.filter(source=Property.Source.VITRINE).count() == expected_count
    prop = Property.objects.get(source=Property.Source.VITRINE, external_id=external_id)
    assert prop.price == Decimal(expected_price), (
        f"Preço do imóvel {external_id} corrompido: esperado Decimal('{expected_price}'), "
        f"obtido Decimal('{prop.price}') (multiplicado por 100x em _parse_price)"
    )


@then(
    parsers.parse(
        "o contador skipped_count do Vitrine registra {expected_skipped:d} anúncio descartado"
    )
)
@allure.title(
    "🎯 ENTÃO o contador skipped_count do Vitrine registra {expected_skipped} anúncio descartado"
)
def then_vitrine_skipped_count_matches(vitrine_run: ImportRun, expected_skipped: int) -> None:
    assert vitrine_run.skipped_count == expected_skipped


@then(parsers.parse('o anúncio sem preço "{external_id}" não é gravado na tabela Property'))
@allure.title("🛡️ E o anúncio sem preço {external_id} não é gravado na tabela Property")
def then_vitrine_priceless_listing_not_saved(external_id: str) -> None:
    assert not Property.objects.filter(external_id=external_id).exists()


@then(parsers.parse('o imóvel vendido "{external_id}" fica persistido com is_active falso'))
@then(parsers.parse('o imóvel removido "{external_id}" fica persistido com is_active falso'))
@allure.title("🎯 ENTÃO o imóvel {external_id} fica persistido com is_active=False")
def then_vitrine_property_is_inactive(external_id: str) -> None:
    prop = Property.objects.get(external_id=external_id)
    assert prop.is_active is False, (
        f"Imóvel {external_id} deveria estar inativo (is_active=False), "
        f"mas permaneceu is_active={prop.is_active}"
    )


@then(parsers.parse('o imóvel ativo "{external_id}" permanece com is_active verdadeiro'))
@allure.title("🛡️ E o imóvel ativo {external_id} permanece com is_active=True")
def then_vitrine_property_is_active(external_id: str) -> None:
    assert Property.objects.get(external_id=external_id).is_active is True


@then(
    parsers.parse(
        'o imóvel "{external_id}" recupera o título "{expected_title}" e preço "{expected_price}"'
    )
)
@allure.title(
    "🎯 ENTÃO o imóvel {external_id} recupera o título '{expected_title}' "
    "e preço R$ {expected_price}"
)
def then_vitrine_property_updated_title_and_price(
    external_id: str, expected_title: str, expected_price: str
) -> None:
    prop = Property.objects.get(external_id=external_id)
    assert prop.title == expected_title
    assert prop.price == Decimal(expected_price), (
        f"Preço corrompido após update de {external_id}: esperado Decimal('{expected_price}'), "
        f"obtido Decimal('{prop.price}')"
    )


@then(
    parsers.parse(
        "o total de imóveis do Vitrine permanece {expected_total:d} "
        "com updated_count igual a {expected_updated:d}"
    )
)
@allure.title(
    "🛡️ E o total de imóveis do Vitrine permanece {expected_total} "
    "com updated_count igual a {expected_updated}"
)
def then_vitrine_total_and_updated_count_match(
    vitrine_run: ImportRun, expected_total: int, expected_updated: int
) -> None:
    assert Property.objects.filter(source=Property.Source.VITRINE).count() == expected_total
    assert vitrine_run.updated_count == expected_updated


@then(
    parsers.parse(
        'as URLs das fotos do imóvel "{external_id}" seguem a sequência publicada pelo Vitrine:'
    )
)
@allure.title(
    "🎯 ENTÃO as URLs das fotos do imóvel {external_id} seguem a sequência publicada pelo Vitrine"
)
def then_vitrine_photos_match_order(external_id: str, datatable: list[list[str]]) -> None:
    prop = Property.objects.get(external_id=external_id)
    urls = list(prop.photos.values_list("url", flat=True))
    expected_urls = [row[1] for row in datatable[1:]]
    assert urls == expected_urls


@then(
    parsers.parse(
        'a contagem de fotos do imóvel "{external_id}" continua sendo exatamente {expected_count:d}'
    )
)
@allure.title(
    "🎯 ENTÃO a contagem de fotos do imóvel {external_id} continua sendo {expected_count}"
)
def then_vitrine_photo_count_remains(external_id: str, expected_count: int) -> None:
    assert Property.objects.get(external_id=external_id).photos.count() == expected_count


@then(
    parsers.parse(
        'o ImportRun do Vitrine termina com status "{expected_status}" '
        "e mensagem de erro preenchida"
    )
)
@allure.title(
    "🎯 ENTÃO o ImportRun do Vitrine termina com status {expected_status} e mensagem preenchida"
)
def then_vitrine_run_failed_gracefully(vitrine_run: ImportRun, expected_status: str) -> None:
    assert vitrine_run.status == expected_status
    assert vitrine_run.error_message
    assert vitrine_run.finished_at is not None


@then(
    parsers.parse(
        'um ImportRun da fonte VITRINE com status "{expected_status}" é registrado no banco'
    )
)
@allure.title("🎯 ENTÃO um ImportRun da fonte VITRINE com status {expected_status} é registrado")
def then_vitrine_celery_run_recorded(expected_status: str) -> None:
    latest = ImportRun.objects.filter(source=Property.Source.VITRINE).first()
    assert latest is not None
    assert latest.status == expected_status


@then(parsers.parse('o valor decimal retornado pelo VitrineImporter é "{expected}"'))
@allure.title("🎯 ENTÃO o valor decimal retornado pelo VitrineImporter é Decimal('{expected}')")
def then_vitrine_parsed_price_matches(
    vitrine_parsed_price: Decimal | None, expected: str
) -> None:
    assert vitrine_parsed_price == Decimal(expected), (
        f"_parse_price corrompeu o valor monetário: esperado Decimal('{expected}'), "
        f"obtido Decimal('{vitrine_parsed_price}')"
    )


@then(parsers.parse('o endereço formatado pelo VitrineImporter é "{expected_address}"'))
@allure.title("🎯 ENTÃO o endereço formatado pelo VitrineImporter é '{expected_address}'")
def then_vitrine_formatted_address_matches(
    vitrine_formatted_address: str, expected_address: str
) -> None:
    assert vitrine_formatted_address == expected_address


@given(
    "que existe um ImportRun do Vitrine em andamento com anúncios "
    "de preço ilegível e negócio desconhecido",
    target_fixture="vitrine_invalid_ctx",
)
@allure.title(
    "🎬 DADO QUE existe um ImportRun do Vitrine em andamento com anúncios "
    "de preço ilegível e negócio desconhecido"
)
def given_vitrine_invalid_listings() -> dict[str, Any]:
    run = ImportRun.objects.create(source=Property.Source.VITRINE)
    unreadable_price = {
        "referencia": "VT-BADPRICE",
        "nome": "Imóvel Sob Consulta",
        "negocio": "venda",
        "preco": "sob consulta",
        "localizacao": {"rua": "Rua A", "municipio": "BH", "estado": "MG"},
    }
    unknown_tx = {
        "referencia": "VT-UNK",
        "nome": "Imóvel Permuta",
        "negocio": "permuta",
        "preco": "500000,00",
        "localizacao": {"rua": "Rua B", "municipio": "BH", "estado": "MG"},
    }
    return {"run": run, "listings": [unreadable_price, unknown_tx]}


@when(
    "VitrineImporter._import_listing processa os anúncios inválidos do Vitrine",
    target_fixture="vitrine_invalid_run",
)
@allure.title("⚡ QUANDO VitrineImporter._import_listing processa os anúncios inválidos do Vitrine")
def when_vitrine_processes_invalid_listings(vitrine_invalid_ctx: dict[str, Any]) -> ImportRun:
    importer = VitrineImporter()
    run: ImportRun = vitrine_invalid_ctx["run"]
    for item in vitrine_invalid_ctx["listings"]:
        importer._import_listing(item, run)
    return run


@then(
    parsers.parse(
        "o ImportRun do Vitrine contabiliza {expected_skipped:d} descartes em skipped_count"
    )
)
@allure.title(
    "🎯 ENTÃO o ImportRun do Vitrine contabiliza {expected_skipped} descartes em skipped_count"
)
def then_vitrine_invalid_run_skipped_count(
    vitrine_invalid_run: ImportRun, expected_skipped: int
) -> None:
    assert vitrine_invalid_run.skipped_count == expected_skipped
