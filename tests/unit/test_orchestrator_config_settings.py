"""
Orchestrator Configuration Settings Tests

Tests for the Pydantic Settings-based configuration management.
Single Responsibility: Validate application settings and environment variable loading.

Component Under Test:
- orchestrator_fastapi/config/settings.py.j2

Settings Features (deployed on orchestrator at hx-orchestrator-server):
- Pydantic BaseSettings with type validation
- Environment variable loading from .env file
- Case-insensitive environment variables
- Secret value protection (SecretStr)
- Database URL construction with password encoding
- Redis URL construction
- Default values for all settings
- CORS origins configuration

Test Coverage:
- Settings initialization with defaults
- Environment variable override
- Database URL property with password encoding
- Redis URL property construction
- SecretStr handling and get_secret_value()
- Field type validation (str, int, bool, List[str])
- CORS origins parsing
- Case insensitive environment variables
"""

import pytest
import os
from urllib.parse import quote
from pydantic import SecretStr

# Import real Settings implementation
from tests.fixtures.orchestrator_fastapi.config.settings import Settings


@pytest.mark.unit
@pytest.mark.fast
class TestSettingsInitialization:
    """Test Settings model initialization"""

    def test_settings_initializes_with_defaults(self, monkeypatch):
        """Test that Settings initializes with default values"""
        # Clear any existing environment variables that might interfere
        monkeypatch.delenv("ORCHESTRATOR_ENV", raising=False)
        monkeypatch.delenv("ORCHESTRATOR_HOST", raising=False)
        monkeypatch.delenv("ORCHESTRATOR_PORT", raising=False)
        monkeypatch.delenv("ORCHESTRATOR_WORKERS", raising=False)
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        
        settings = Settings()

        assert settings.orchestrator_env == "production"
        assert settings.orchestrator_host == "0.0.0.0"
        assert settings.orchestrator_port == 8000
        assert settings.orchestrator_workers == 4
        assert settings.log_level == "INFO"

    def test_settings_accepts_custom_values(self, monkeypatch):
        """Test that Settings accepts custom values via environment variables"""
        monkeypatch.setenv("ORCHESTRATOR_ENV", "development")
        monkeypatch.setenv("ORCHESTRATOR_PORT", "9000")
        monkeypatch.setenv("ORCHESTRATOR_WORKERS", "8")

        settings = Settings()

        assert settings.orchestrator_env == "development"
        assert settings.orchestrator_port == 9000
        assert settings.orchestrator_workers == 8

    def test_settings_has_database_defaults(self, monkeypatch):
        """Test that database settings have correct defaults"""
        # Clear any existing database environment variables
        monkeypatch.delenv("POSTGRES_HOST", raising=False)
        monkeypatch.delenv("POSTGRES_PORT", raising=False)
        monkeypatch.delenv("POSTGRES_DB", raising=False)
        monkeypatch.delenv("POSTGRES_USER", raising=False)
        
        settings = Settings()

        assert settings.postgres_host == "hx-sqldb-server.dev-test.hana-x.ai"
        assert settings.postgres_port == 5432
        assert settings.postgres_db == "shield_orchestrator"
        assert settings.postgres_user == "orchestrator"

    def test_settings_has_redis_defaults(self, monkeypatch):
        """Test that Redis settings have correct defaults"""
        # Clear any existing Redis environment variables
        monkeypatch.delenv("REDIS_HOST", raising=False)
        monkeypatch.delenv("REDIS_PORT", raising=False)
        monkeypatch.delenv("REDIS_DB", raising=False)
        
        settings = Settings()

        assert settings.redis_host == "hx-sqldb-server.dev-test.hana-x.ai"
        assert settings.redis_port == 6379
        assert settings.redis_db == 0


@pytest.mark.unit
@pytest.mark.fast
class TestDatabaseURLProperty:
    """Test database_url property construction"""

    def test_database_url_constructs_correctly(self, monkeypatch):
        """Test that database_url property constructs valid asyncpg URL"""
        monkeypatch.setenv("POSTGRES_PASSWORD", "test_password")
        
        settings = Settings()
        url = settings.database_url

        assert url.startswith("postgresql+asyncpg://")
        assert "orchestrator:test_password@" in url
        assert "hx-sqldb-server.dev-test.hana-x.ai:5432" in url
        assert "/shield_orchestrator" in url

    def test_database_url_encodes_special_characters_in_password(self, monkeypatch):
        """Test that database_url encodes special characters in password"""
        monkeypatch.setenv("POSTGRES_PASSWORD", "p@ssw0rd!#$")
        
        settings = Settings()
        url = settings.database_url

        # Password should be URL-encoded
        encoded_password = quote("p@ssw0rd!#$", safe="")
        assert f":{encoded_password}@" in url
        
        # Verify the secret value is accessible via get_secret_value()
        assert settings.postgres_password.get_secret_value() == "p@ssw0rd!#$"

    def test_database_url_uses_quote_not_quote_plus(self, monkeypatch):
        """Test that database_url uses quote() not quote_plus() for asyncpg compatibility"""
        monkeypatch.setenv("POSTGRES_PASSWORD", "pass word")  # Space in password
        
        settings = Settings()
        url = settings.database_url

        # quote() encodes space as %20, quote_plus() would encode as +
        assert "pass%20word" in url
        assert "pass+word" not in url


@pytest.mark.unit
@pytest.mark.fast
class TestRedisURLProperty:
    """Test redis_url property construction"""

    def test_redis_url_constructs_correctly(self, monkeypatch):
        """Test that redis_url property constructs valid Redis URL"""
        # Clear any Redis environment variables to use defaults
        monkeypatch.delenv("REDIS_HOST", raising=False)
        monkeypatch.delenv("REDIS_PORT", raising=False)
        monkeypatch.delenv("REDIS_DB", raising=False)
        
        settings = Settings()
        url = settings.redis_url

        assert url == "redis://hx-sqldb-server.dev-test.hana-x.ai:6379/0"

    def test_redis_url_uses_custom_db(self, monkeypatch):
        """Test that redis_url uses custom database number"""
        monkeypatch.setenv("REDIS_DB", "5")
        
        settings = Settings()
        url = settings.redis_url

        assert url.endswith("/5")


@pytest.mark.unit
@pytest.mark.fast
class TestSecretStrHandling:
    """Test SecretStr field handling"""

    def test_secret_str_hides_value_in_repr(self):
        """Test that SecretStr hides value in string representation"""
        secret = SecretStr("sensitive_data")

        # Pydantic SecretStr hides the value in string representation
        assert "sensitive_data" not in repr(secret)
        assert "sensitive_data" not in str(secret)

    def test_secret_str_reveals_value_with_get_secret_value(self):
        """Test that SecretStr reveals value with get_secret_value()"""
        secret = SecretStr("sensitive_data")

        assert secret.get_secret_value() == "sensitive_data"

    def test_settings_uses_secret_str_for_passwords(self, monkeypatch):
        """Test that Settings uses SecretStr for sensitive fields"""
        monkeypatch.setenv("POSTGRES_PASSWORD", "db_password")
        monkeypatch.setenv("QDRANT_API_KEY", "qdrant_key")
        monkeypatch.setenv("LLM_API_KEY", "llm_key")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt_secret")
        
        settings = Settings()

        # All secret fields should be SecretStr instances
        assert isinstance(settings.postgres_password, SecretStr)
        assert isinstance(settings.qdrant_api_key, SecretStr)
        assert isinstance(settings.llm_api_key, SecretStr)
        assert isinstance(settings.jwt_secret_key, SecretStr)
        
        # Verify we can access the secret values
        assert settings.postgres_password.get_secret_value() == "db_password"
        assert settings.qdrant_api_key.get_secret_value() == "qdrant_key"
        assert settings.llm_api_key.get_secret_value() == "llm_key"
        assert settings.jwt_secret_key.get_secret_value() == "jwt_secret"


@pytest.mark.unit
@pytest.mark.fast
class TestSettingsConfiguration:
    """Test Settings configuration and special fields"""

    def test_cors_origins_is_list(self, monkeypatch):
        """Test that cors_origins is a list"""
        # Clear any CORS environment variables to use defaults
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        
        settings = Settings()

        assert isinstance(settings.cors_origins, list)
        assert settings.cors_origins == ["*"]

    def test_cors_origins_accepts_multiple_values(self, monkeypatch):
        """Test that cors_origins accepts multiple origin values"""
        # Pydantic can parse JSON array from environment variable
        import json
        origins = ["http://hx-webui-server.dev-test.hana-x.ai:3000", "https://app.example.com"]
        monkeypatch.setenv("CORS_ORIGINS", json.dumps(origins))
        
        settings = Settings()

        assert len(settings.cors_origins) == 2
        assert "http://hx-webui-server.dev-test.hana-x.ai:3000" in settings.cors_origins
        assert "https://app.example.com" in settings.cors_origins

    def test_qdrant_verify_ssl_is_boolean(self, monkeypatch):
        """Test that qdrant_verify_ssl is boolean"""
        # Clear to use default
        monkeypatch.delenv("QDRANT_VERIFY_SSL", raising=False)
        
        settings = Settings()

        assert isinstance(settings.qdrant_verify_ssl, bool)
        assert settings.qdrant_verify_ssl is False

    def test_jwt_configuration_has_defaults(self, monkeypatch):
        """Test that JWT configuration has correct defaults"""
        # Clear JWT environment variables to use defaults
        monkeypatch.delenv("JWT_ALGORITHM", raising=False)
        monkeypatch.delenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)
        
        settings = Settings()

        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_access_token_expire_minutes == 60
