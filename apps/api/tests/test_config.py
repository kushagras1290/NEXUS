import pytest

from nexus_api.config import Settings


def test_cors_string_is_split() -> None:
    settings = Settings(cors_origins="https://a.example,https://b.example")
    assert settings.cors_origins == ["https://a.example", "https://b.example"]


def test_production_rejects_dev_auth() -> None:
    settings = Settings(env="production", auth_mode="dev_headers")
    with pytest.raises(ValueError):
        settings.validate_production()
