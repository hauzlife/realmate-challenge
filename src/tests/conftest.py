"""Fixtures shared by the properties tests."""

from pathlib import Path

import pytest
from pytest_django.fixtures import Settings

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def nexo_feed(settings: Settings) -> Path:
    """Point the importer at a small excerpt of the catalog the portal publishes."""
    feed_path = FIXTURES_DIR / "nexo_catalogo.xml"
    settings.NEXO_FEED_PATH = feed_path
    return feed_path
