"""BDD step definitions and scenarios for the Nexo Portal importer (specs/nexo_importer.feature)."""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import allure
import pytest
from pytest_bdd import given, parsers, scenario, then, when

from apps.properties.models import ImportRun, Property, PropertyPhoto
from apps.properties.services.importers import NexoImporter
from apps.properties.tasks.import_properties import import_nexo_properties

FEATURE_FILE = "nexo_importer.feature"


def _attach_import_run_summary(import_run: ImportRun) -> None:
    allure.attach(
        json.dumps(
            {
                "import_run_id": import_run.id,
                "status": import_run.status,
                "created_count": import_run.created_count,
                "updated_count": import_run.updated_count,
                "skipped_count": import_run.skipped_count,
            },
            indent=2,
        ),
        name="import_run_summary.json",
        attachment_type=allure.attachment_type.JSON,
    )


# ============================================================================
# Scenarios bound to specs/nexo_importer.feature
# ============================================================================


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Importação Completa de Catálogo XML")
@allure.severity(allure.severity_level.BLOCKER)
@allure.tag("importer", "nexo", "xml", "bdd")
@allure.title("Importação inicial cria imóveis válidos a partir do catálogo XML do Portal Nexo")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Importação inicial cria imóveis válidos a partir do catálogo XML do Portal Nexo",
)
def test_run_creates_properties_from_portal_catalog() -> None:
    """Scenario: Importação inicial cria imóveis válidos a partir do catálogo XML do Portal Nexo."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Validação e Descarte de Anúncios Inválidos")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "validation", "price", "bdd")
@allure.title("Importador ignora anúncio com preço inválido ('sob consulta') sem abortar o lote")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Importador ignora anúncio com preço inválido sem abortar o lote",
)
def test_run_skips_listing_without_price() -> None:
    """Scenario: Importador ignora anúncio com preço inválido sem abortar o lote."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Atualização Idempotente de Anúncios Existentes")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "upsert", "idempotency", "bdd")
@allure.title("Reimportação atualiza dados de imóvel já existente in-place sem duplicar registro")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Reimportação atualiza dados de imóvel já existente in-place sem duplicar registro",
)
def test_run_updates_property_already_imported() -> None:
    """Scenario: Reimportação atualiza dados de imóvel já existente in-place."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Controle de Disponibilidade de Anúncios")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "availability", "inactive", "bdd")
@allure.title("Anúncio marcado como 'vendido' no XML é salvo como inativo (is_active=False)")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Anúncio marcado como vendido no XML é salvo como inativo",
)
def test_run_marks_unavailable_listing_as_inactive() -> None:
    """Scenario: Anúncio marcado como vendido no XML é salvo como inativo."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Controle de Disponibilidade de Anúncios")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "availability", "inactive", "bdd")
@allure.title(
    "Anúncio removido do XML em carga subsequente é marcado como inativo (is_active=False)"
)
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Anúncio removido do XML em carga subsequente é marcado como inativo",
)
def test_run_deactivates_missing_listing_from_previous_import() -> None:
    """Scenario: Anúncio removido do XML em carga subsequente é marcado como inativo."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Sincronização de Fotos do Imóvel")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("importer", "photos", "ordering", "bdd")
@allure.title("Fotos do anúncio são gravadas respeitando a ordem exata publicada pelo portal")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Fotos do anúncio são gravadas respeitando a ordem exata publicada pelo portal",
)
def test_run_saves_listing_photos_in_portal_order() -> None:
    """Scenario: Fotos do anúncio são gravadas respeitando a ordem exata publicada pelo portal."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Sincronização de Fotos do Imóvel")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("importer", "photos", "idempotency", "bdd")
@allure.title("Reimportação substitui as fotos do imóvel sem acumular registros duplicados")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Reimportação substitui as fotos do imóvel sem acumular registros duplicados",
)
def test_run_replaces_photos_of_property_already_imported() -> None:
    """Scenario: Reimportação substitui as fotos do imóvel sem acumular registros duplicados."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Resiliência e Tratamento de Falhas de I/O")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("importer", "resilience", "error-handling", "bdd")
@allure.title("Ausência do arquivo XML registra ImportRun com status FAILED e mensagem de erro")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Ausência do arquivo XML registra ImportRun com status FAILED e mensagem de erro",
)
def test_run_fails_when_feed_is_missing() -> None:
    """Scenario: Ausência do arquivo XML registra ImportRun com status FAILED e mensagem de erro."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Execução via Task Assíncrona Celery")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("celery", "task", "importer", "bdd")
@allure.title("Task Celery import_nexo_properties aciona o importador e persiste o ImportRun")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Task Celery import_nexo_properties aciona o importador e persiste o ImportRun",
)
def test_celery_task_import_nexo_properties_executes_importer() -> None:
    """Scenario: Task Celery import_nexo_properties aciona o importador e persiste o ImportRun."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Normalização de Preços e Endereços")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("parser", "price", "pt-br", "bdd")
@allure.title("Conversão de preço em formato pt-BR ('{raw}') retorna Decimal('{expected}')")
@scenario(
    FEATURE_FILE,
    "Conversão de preço em formato pt-BR retorna Decimal normalizado",
)
def test_parse_price_accepts_portal_format() -> None:
    """Scenario Outline: Conversão de preço em formato pt-BR retorna Decimal normalizado."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Normalização de Preços e Endereços")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("parser", "price", "negative-test", "bdd")
@allure.title("Conversão de preço não numérico ('sob consulta') retorna None com segurança")
@scenario(
    FEATURE_FILE,
    "Conversão de preço não numérico retorna None com segurança",
)
def test_parse_price_returns_none_for_invalid_value() -> None:
    """Scenario: Conversão de preço não numérico retorna None com segurança."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Normalização de Preços e Endereços")
@allure.severity(allure.severity_level.MINOR)
@allure.tag("parser", "address", "bdd")
@allure.title("Formatação de endereço concatena logradouro, número e complemento não vazios")
@scenario(
    FEATURE_FILE,
    "Formatação de endereço concatena logradouro, número e complemento não vazios",
)
def test_build_address_joins_available_parts() -> None:
    """Scenario: Formatação de endereço concatena logradouro, número e complemento não vazios."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Validação e Descarte de Anúncios Inválidos")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("validation", "negative-test", "bdd")
@allure.title("Importador descarta anúncios incompletos ou com tipo de negócio desconhecido")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Importador descarta anúncios incompletos ou com tipo de negócio desconhecido",
)
def test_import_listing_skips_incomplete_and_unknown_transaction() -> None:
    """Scenario: Importador descarta anúncios incompletos ou com tipo de negócio desconhecido."""


@allure.epic("Catálogo de Imóveis")
@allure.feature("Importador Portal Nexo")
@allure.story("Representação de Modelos de Domínio")
@allure.severity(allure.severity_level.MINOR)
@allure.tag("models", "bdd")
@allure.title("Representação textual de Property, PropertyPhoto e ImportRun")
@pytest.mark.django_db
@scenario(
    FEATURE_FILE,
    "Representação textual de Property, PropertyPhoto e ImportRun reflete "
    "identificadores de domínio",
)
def test_domain_models_string_representation() -> None:
    """Scenario: Representação textual de Property, PropertyPhoto e ImportRun."""


# ============================================================================
# Step Definitions (Given / When / Then)
# ============================================================================


@given(
    parsers.parse(
        'que o catálogo foi importado e o imóvel "{external_id}" '
        'teve o preço alterado para "{temp_price}"'
    )
)
@allure.title(
    "🎬 DADO QUE o catálogo foi importado e o imóvel {external_id} "
    "teve o preço alterado para {temp_price}"
)
def given_catalog_imported_and_price_changed(
    nexo_feed: Path, external_id: str, temp_price: str
) -> None:
    NexoImporter().run()
    Property.objects.filter(external_id=external_id).update(price=Decimal(temp_price))


@given(
    parsers.parse('que o anúncio "{external_id}" estava ativo na base após uma carga anterior')
)
@allure.title("🎬 DADO QUE o anúncio {external_id} estava ativo na base após uma carga anterior")
def given_active_property_from_previous_import(external_id: str) -> None:
    Property.objects.create(
        source=Property.Source.NEXO,
        external_id=external_id,
        title="Apartamento 2 quartos no Sion",
        transaction=Property.Transaction.SALE,
        price=Decimal("640000.00"),
        city="Belo Horizonte",
        state="MG",
        is_active=True,
    )


@given(
    parsers.parse('que o imóvel "{external_id}" já possui {photo_count:d} fotos importadas')
)
@allure.title("🎬 DADO QUE o imóvel {external_id} já possui {photo_count} fotos importadas")
def given_property_already_has_imported_photos(
    nexo_feed: Path, external_id: str, photo_count: int
) -> None:
    NexoImporter().run()
    assert Property.objects.get(external_id=external_id).photos.count() == photo_count


@given(
    "que o caminho do feed aponta para um arquivo XML inexistente",
    target_fixture="missing_feed_path",
)
@allure.title("🎬 DADO QUE o caminho do feed aponta para um arquivo XML inexistente")
def given_missing_feed_path(tmp_path: Path) -> Path:
    return tmp_path / "inexistente.xml"


@given(
    parsers.parse(
        'que o endereço bruto possui logradouro "{logradouro}", '
        'número "{numero}" e complemento vazio'
    ),
    target_fixture="raw_address",
)
@allure.title(
    "🎬 DADO QUE o endereço bruto possui logradouro '{logradouro}', "
    "número '{numero}' e complemento vazio"
)
def given_raw_address(logradouro: str, numero: str) -> dict[str, str]:
    return {"logradouro": logradouro, "numero": numero, "complemento": ""}


@when("o NexoImporter executa a importação do catálogo XML", target_fixture="import_run")
@when(
    "o NexoImporter processa o feed contendo item sem preço numérico",
    target_fixture="import_run",
)
@when(
    "o NexoImporter roda novamente sobre o catálogo atualizado",
    target_fixture="import_run",
)
@when("o NexoImporter executa uma segunda carga do mesmo feed", target_fixture="import_run")
@allure.title("⚡ QUANDO o NexoImporter executa a importação do catálogo XML")
def when_importer_runs(nexo_feed: Path) -> ImportRun:
    import_run = NexoImporter().run()
    _attach_import_run_summary(import_run)
    return import_run


@when(
    parsers.parse('o NexoImporter importa o feed com o imóvel "{external_id}" vendido'),
    target_fixture="import_run",
)
@when(
    parsers.parse('o NexoImporter importa o catálogo com as fotos do imóvel "{external_id}"'),
    target_fixture="import_run",
)
@allure.title("⚡ QUANDO o NexoImporter importa o catálogo para o imóvel {external_id}")
def when_importer_runs_for_property(nexo_feed: Path, external_id: str) -> ImportRun:
    import_run = NexoImporter().run()
    _attach_import_run_summary(import_run)
    return import_run


@when(
    "o NexoImporter tenta executar a importação do arquivo ausente",
    target_fixture="import_run",
)
@allure.title("⚡ QUANDO o NexoImporter tenta executar a importação do arquivo ausente")
def when_importer_runs_with_missing_feed(missing_feed_path: Path) -> ImportRun:
    import_run = NexoImporter(feed_path=missing_feed_path).run()
    allure.attach(
        import_run.error_message,
        name="error_message.txt",
        attachment_type=allure.attachment_type.TEXT,
    )
    return import_run


@when("a task Celery import_nexo_properties é disparada")
@allure.title("⚡ QUANDO a task Celery import_nexo_properties é disparada")
def when_celery_import_task_runs(nexo_feed: Path) -> None:
    import_nexo_properties()


@when(
    parsers.parse('_parse_price recebe o texto "{raw}"'),
    target_fixture="parsed_price",
)
@allure.title("⚡ QUANDO _parse_price recebe o texto '{raw}'")
def when_parse_price_receives_text(raw: str) -> Decimal | None:
    return NexoImporter()._parse_price(raw)


@when(
    "_build_address monta a linha de endereço",
    target_fixture="formatted_address",
)
@allure.title("⚡ QUANDO _build_address monta a linha de endereço")
def when_build_address_runs(raw_address: dict[str, str]) -> str:
    return NexoImporter()._build_address(raw_address)


@then(
    parsers.parse(
        'a execução fecha com status "{expected_status}" e {expected_created:d} imóveis criados'
    )
)
@allure.title(
    "🎯 ENTÃO a execução fecha com status {expected_status} e {expected_created} imóveis criados"
)
def then_import_run_succeeds_with_created_count(
    import_run: ImportRun, expected_status: str, expected_created: int
) -> None:
    assert import_run.status == expected_status
    assert import_run.created_count == expected_created


@then(parsers.parse("a base de dados persiste exatamente {expected_count:d} anúncios válidos"))
@then(parsers.parse("os {expected_count:d} imóveis do catálogo ficam disponíveis na base"))
@allure.title("🛡️ E a base de dados persiste exatamente {expected_count} imóveis")
def then_database_has_expected_property_count(expected_count: int) -> None:
    assert Property.objects.count() == expected_count


@then(
    parsers.parse("o contador skipped_count registra {expected_skipped:d} anúncio descartado")
)
@allure.title("🎯 ENTÃO o contador skipped_count registra {expected_skipped} anúncio descartado")
def then_skipped_count_matches(import_run: ImportRun, expected_skipped: int) -> None:
    assert import_run.skipped_count == expected_skipped


@then(parsers.parse('o anúncio inválido "{external_id}" não é gravado na tabela Property'))
@allure.title("🛡️ E o anúncio inválido {external_id} não é gravado na tabela Property")
def then_invalid_property_is_not_persisted(external_id: str) -> None:
    assert not Property.objects.filter(external_id=external_id).exists()


@then(parsers.parse('o preço do imóvel "{external_id}" volta para "{expected_price}"'))
@allure.title("🎯 ENTÃO o preço do imóvel {external_id} volta para R$ {expected_price}")
def then_property_price_is_updated(external_id: str, expected_price: str) -> None:
    property_ = Property.objects.get(external_id=external_id)
    assert property_.price == Decimal(expected_price)


@then(
    parsers.parse(
        "o total de imóveis permanece {expected_total:d} "
        "com updated_count igual a {expected_updated:d}"
    )
)
@allure.title(
    "🛡️ E o total de imóveis permanece {expected_total} com updated_count igual a {expected_updated}"
)
def then_total_and_updated_count_match(
    import_run: ImportRun, expected_total: int, expected_updated: int
) -> None:
    assert Property.objects.count() == expected_total
    assert import_run.updated_count == expected_updated


@then(parsers.parse('o imóvel "{external_id}" fica persistido com is_active falso'))
@allure.title("🎯 ENTÃO o imóvel {external_id} fica persistido com is_active=False")
def then_property_is_inactive(external_id: str) -> None:
    property_ = Property.objects.get(external_id=external_id)
    assert property_.is_active is False


@then(
    parsers.parse('o imóvel disponível "{external_id}" permanece com is_active verdadeiro')
)
@allure.title("🛡️ E o imóvel disponível {external_id} permanece com is_active=True")
def then_property_is_active(external_id: str) -> None:
    assert Property.objects.get(external_id=external_id).is_active is True


@then(
    parsers.parse(
        'as URLs das fotos do imóvel "{external_id}" seguem a sequência publicada pelo portal:'
    )
)
@allure.title(
    "🎯 ENTÃO as URLs das fotos do imóvel {external_id} seguem a sequência publicada pelo portal"
)
def then_property_photos_match_portal_order(
    external_id: str, datatable: list[list[str]]
) -> None:
    property_ = Property.objects.get(external_id=external_id)
    urls = list(property_.photos.values_list("url", flat=True))
    expected_urls = [row[1] for row in datatable[1:]]
    allure.attach(
        json.dumps(urls, indent=2),
        name="ordered_photo_urls.json",
        attachment_type=allure.attachment_type.JSON,
    )
    assert urls == expected_urls


@then(
    parsers.parse(
        'a contagem de fotos do imóvel "{external_id}" continua sendo exatamente {expected_count:d}'
    )
)
@allure.title(
    "🎯 ENTÃO a contagem de fotos do imóvel {external_id} "
    "continua sendo exatamente {expected_count}"
)
def then_property_photo_count_remains(external_id: str, expected_count: int) -> None:
    assert Property.objects.get(external_id=external_id).photos.count() == expected_count


@then(
    parsers.parse(
        'o ImportRun termina com status "{expected_status}" sem lançar exceção não tratada'
    )
)
@allure.title(
    "🎯 ENTÃO o ImportRun termina com status {expected_status} sem lançar exceção não tratada"
)
def then_import_run_fails_gracefully(import_run: ImportRun, expected_status: str) -> None:
    assert import_run.status == expected_status


@then("a mensagem do erro e o timestamp finished_at ficam preenchidos")
@allure.title("🛡️ E a mensagem do erro e o timestamp finished_at ficam preenchidos")
def then_error_message_and_finished_at_are_populated(import_run: ImportRun) -> None:
    assert import_run.error_message
    assert import_run.finished_at is not None


@then(parsers.parse('um ImportRun com status "{expected_status}" é registrado no banco'))
@allure.title("🎯 ENTÃO um ImportRun com status {expected_status} é registrado no banco")
def then_latest_import_run_has_status(expected_status: str) -> None:
    latest_run = ImportRun.objects.first()
    assert latest_run is not None
    assert latest_run.status == expected_status


@then(parsers.parse('o valor decimal retornado é "{expected}"'))
@allure.title("🎯 ENTÃO o valor decimal retornado é Decimal('{expected}')")
def then_parsed_price_matches_decimal(parsed_price: Decimal | None, expected: str) -> None:
    assert parsed_price == Decimal(expected)


@then("o retorno de _parse_price é None sem lançar InvalidOperation")
@allure.title("🎯 ENTÃO o retorno de _parse_price é None sem lançar InvalidOperation")
def then_parsed_price_is_none(parsed_price: Decimal | None) -> None:
    assert parsed_price is None


@then(parsers.parse('o endereço formatado final é "{expected_address}"'))
@allure.title("🎯 ENTÃO o endereço formatado final é '{expected_address}'")
def then_formatted_address_matches(formatted_address: str, expected_address: str) -> None:
    assert formatted_address == expected_address


@given(
    "que existe um ImportRun em andamento e dois payloads inválidos",
    target_fixture="invalid_payloads_ctx",
)
@allure.title("🎬 DADO QUE existe um ImportRun em andamento e dois payloads inválidos")
def given_import_run_and_invalid_payloads() -> dict[str, Any]:
    run = ImportRun.objects.create(source=Property.Source.NEXO)
    incomplete_listing = {"codigo": "NX-INC", "titulo": "Incompleto"}
    unknown_tx_listing = {
        "codigo": "NX-UNK",
        "titulo": "Permuta",
        "tipo_negocio": "permuta",
        "valor": "500.000,00",
        "endereco": {"logradouro": "Rua X", "cidade": "BH", "uf": "MG"},
    }
    return {
        "run": run,
        "listings": [incomplete_listing, unknown_tx_listing],
    }


@when(
    "_import_listing processa ambos os anúncios inválidos e _parse_int recebe texto inválido",
    target_fixture="invalid_processing_result",
)
@allure.title(
    "⚡ QUANDO _import_listing processa os anúncios inválidos e _parse_int recebe texto inválido"
)
def when_import_listing_processes_invalid_payloads(
    invalid_payloads_ctx: dict[str, Any],
) -> dict[str, Any]:
    importer = NexoImporter()
    run: ImportRun = invalid_payloads_ctx["run"]
    for item in invalid_payloads_ctx["listings"]:
        importer._import_listing(item, run)
    unreadable_price_run = ImportRun.objects.create(source=Property.Source.NEXO)
    importer._import_listing(
        {
            "codigo": "NX-BADPRICE",
            "titulo": "Preço Sob Consulta",
            "tipo_negocio": "venda",
            "valor": "sob consulta",
            "endereco": {"logradouro": "Rua Y", "cidade": "BH", "uf": "MG"},
        },
        unreadable_price_run,
    )
    assert unreadable_price_run.skipped_count == 1
    return {
        "run": run,
        "empty_int": importer._parse_int(""),
        "bad_int": importer._parse_int("nao-numerico"),
    }


@then("skipped_count contabiliza 2 descartes e _parse_int inválido retorna None")
@allure.title("🎯 ENTÃO skipped_count contabiliza 2 descartes e _parse_int inválido retorna None")
def then_skipped_count_is_two_and_parse_int_none(
    invalid_processing_result: dict[str, Any],
) -> None:
    run: ImportRun = invalid_processing_result["run"]
    assert run.skipped_count == 2
    assert invalid_processing_result["empty_int"] is None
    assert invalid_processing_result["bad_int"] is None


@then(
    "as representações textuais de Property, PropertyPhoto e ImportRun "
    "exibem fonte, código e posição"
)
@allure.title(
    "🎯 ENTÃO as representações textuais de Property, PropertyPhoto e ImportRun "
    "exibem fonte, código e posição"
)
def then_models_str_representations_are_formatted(import_run: ImportRun) -> None:
    prop = Property.objects.get(external_id="NX-10233")
    photo = PropertyPhoto.objects.filter(property=prop).first()
    assert photo is not None
    assert "Nexo Portal #NX-10233" in str(prop)
    assert str(photo) == "NX-10233 #0"
    assert "NEXO SUCCESS" in str(import_run)
