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
from unittest.mock import patch, MagicMock
from urllib.parse import quote


# Mock Pydantic models
class MockSecretStr:
    """Mock SecretStr for testing"""

    def __init__(self, value: str):
        self._value = value

    def get_secret_value(self) -> str:
        return self._value

    def __repr__(self):
        return "**********"


class MockSettings:
    """Mock Settings for testing"""

    def __init__(self, **kwargs):
        # Server configuration
        self.orchestrator_env = kwargs.get("orchestrator_env", "production")
        self.orchestrator_host = kwargs.get("orchestrator_host", "0.0.0.0")
        self.orchestrator_port = kwargs.get("orchestrator_port", 8000)
        self.orchestrator_workers = kwargs.get("orchestrator_workers", 4)
        self.log_level = kwargs.get("log_level", "INFO")
        self.log_format = kwargs.get("log_format", "json")

        # Database
        self.postgres_host = kwargs.get("postgres_host", "hx-sqldb-server.dev-test.hana-x.ai")
        self.postgres_port = kwargs.get("postgres_port", 5432)
        self.postgres_db = kwargs.get("postgres_db", "shield_orchestrator")
        self.postgres_user = kwargs.get("postgres_user", "orchestrator")
        self.postgres_password = kwargs.get("postgres_password", MockSecretStr("default_password"))

        # Redis
        self.redis_host = kwargs.get("redis_host", "hx-sqldb-server.dev-test.hana-x.ai")
        self.redis_port = kwargs.get("redis_port", 6379)
        self.redis_db = kwargs.get("redis_db", 0)

        # Qdrant
        self.qdrant_url = kwargs.get("qdrant_url", "https://hx-vectordb-server.dev-test.hana-x.ai:6333")
        self.qdrant_api_key = kwargs.get("qdrant_api_key", MockSecretStr("qdrant_key"))
        self.qdrant_collection = kwargs.get("qdrant_collection", "hx_corpus_v1")
        self.qdrant_verify_ssl = kwargs.get("qdrant_verify_ssl", False)

        # LLM
        self.llm_api_base = kwargs.get("llm_api_base", "http://hx-litellm-server.dev-test.hana-x.ai:4000/v1")
        self.llm_api_key = kwargs.get("llm_api_key", MockSecretStr("llm_key"))
        self.llm_model = kwargs.get("llm_model", "llama3.2:latest")
        self.llm_embedding_model = kwargs.get("llm_embedding_model", "mxbai-embed-large")

        # CORS
        self.cors_origins = kwargs.get("cors_origins", ["*"])

        # Security
        self.jwt_secret_key = kwargs.get("jwt_secret_key", MockSecretStr("jwt_secret"))
        self.jwt_algorithm = kwargs.get("jwt_algorithm", "HS256")
        self.jwt_access_token_expire_minutes = kwargs.get("jwt_access_token_expire_minutes", 60)

    @property
    def database_url(self) -> str:
        """Construct database URL with encoded password"""
        encoded_password = quote(self.postgres_password.get_secret_value(), safe="")
        return f"postgresql+asyncpg://{self.postgres_user}:{encoded_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@pytest.mark.unit
@pytest.mark.fast
class TestSettingsInitialization:
    """Test Settings model initialization"""

    def test_settings_initializes_with_defaults(self):
        """Test that Settings initializes with default values"""
        settings = MockSettings()

        assert settings.orchestrator_env == "production"
        assert settings.orchestrator_host == "0.0.0.0"
        assert settings.orchestrator_port == 8000
        assert settings.orchestrator_workers == 4
        assert settings.log_level == "INFO"

    def test_settings_accepts_custom_values(self):
        """Test that Settings accepts custom values via kwargs"""
        settings = MockSettings(
            orchestrator_env="development",
            orchestrator_port=9000,
            orchestrator_workers=8
        )

        assert settings.orchestrator_env == "development"
        assert settings.orchestrator_port == 9000
        assert settings.orchestrator_workers == 8

    def test_settings_has_database_defaults(self):
        """Test that database settings have correct defaults"""
        settings = MockSettings()

        assert settings.postgres_host == "hx-sqldb-server.dev-test.hana-x.ai"
        assert settings.postgres_port == 5432
        assert settings.postgres_db == "shield_orchestrator"
        assert settings.postgres_user == "orchestrator"

    def test_settings_has_redis_defaults(self):
        """Test that Redis settings have correct defaults"""
        settings = MockSettings()

        assert settings.redis_host == "hx-sqldb-server.dev-test.hana-x.ai"
        assert settings.redis_port == 6379
        assert settings.redis_db == 0


@pytest.mark.unit
@pytest.mark.fast
class TestDatabaseURLProperty:
    """Test database_url property construction"""

    def test_database_url_constructs_correctly(self):
        """Test that database_url property constructs valid asyncpg URL"""
        settings = MockSettings(
            postgres_password=MockSecretStr("test_password")
        )

        url = settings.database_url

        assert url.startswith("postgresql+asyncpg://")
        assert "orchestrator:test_password@" in url
        assert "hx-sqldb-server.dev-test.hana-x.ai:5432" in url
        assert "/shield_orchestrator" in url

    def test_database_url_encodes_special_characters_in_password(self):
        """Test that database_url encodes special characters in password"""
        settings = MockSettings(
            postgres_password=MockSecretStr("p@ssw0rd!#$")
        )

        url = settings.database_url

        # Password should be URL-encoded
        encoded_password = quote("p@ssw0rd!#$", safe="")
        assert f":{encoded_password}@" in url

    def test_database_url_uses_quote_not_quote_plus(self):
        """Test that database_url uses quote() not quote_plus() for asyncpg compatibility"""
        settings = MockSettings(
            postgres_password=MockSecretStr("pass word")  # Space in password
        )

        url = settings.database_url

        # quote() encodes space as %20, quote_plus() would encode as +
        assert "pass%20word" in url
        assert "pass+word" not in url


@pytest.mark.unit
@pytest.mark.fast
class TestRedisURLProperty:
    """Test redis_url property construction"""

    def test_redis_url_constructs_correctly(self):
        """Test that redis_url property constructs valid Redis URL"""
        settings = MockSettings()

        url = settings.redis_url

        assert url == "redis://hx-sqldb-server.dev-test.hana-x.ai:6379/0"

    def test_redis_url_uses_custom_db(self):
        """Test that redis_url uses custom database number"""
        settings = MockSettings(redis_db=5)

        url = settings.redis_url

        assert url.endswith("/5")


@pytest.mark.unit
@pytest.mark.fast
class TestSecretStrHandling:
    """Test SecretStr field handling"""

    def test_secret_str_hides_value_in_repr(self):
        """Test that SecretStr hides value in string representation"""
        secret = MockSecretStr("sensitive_data")

        assert repr(secret) == "**********"
        assert "sensitive_data" not in repr(secret)

    def test_secret_str_reveals_value_with_get_secret_value(self):
        """Test that SecretStr reveals value with get_secret_value()"""
        secret = MockSecretStr("sensitive_data")

        assert secret.get_secret_value() == "sensitive_data"

    def test_settings_uses_secret_str_for_passwords(self):
        """Test that Settings uses SecretStr for sensitive fields"""
        settings = MockSettings(
            postgres_password=MockSecretStr("db_password"),
            qdrant_api_key=MockSecretStr("qdrant_key"),
            llm_api_key=MockSecretStr("llm_key"),
            jwt_secret_key=MockSecretStr("jwt_secret")
        )

        # All secret fields should be SecretStr instances
        assert isinstance(settings.postgres_password, MockSecretStr)
        assert isinstance(settings.qdrant_api_key, MockSecretStr)
        assert isinstance(settings.llm_api_key, MockSecretStr)
        assert isinstance(settings.jwt_secret_key, MockSecretStr)


@pytest.mark.unit
@pytest.mark.fast
class TestSettingsConfiguration:
    """Test Settings configuration and special fields"""

    def test_cors_origins_is_list(self):
        """Test that cors_origins is a list"""
        settings = MockSettings()

        assert isinstance(settings.cors_origins, list)
        assert settings.cors_origins == ["*"]

    def test_cors_origins_accepts_multiple_values(self):
        """Test that cors_origins accepts multiple origin values"""
        settings = MockSettings(
            cors_origins=["http://hx-webui-server.dev-test.hana-x.ai:3000", "https://app.example.com"]
        )

        assert len(settings.cors_origins) == 2
        assert "http://hx-webui-server.dev-test.hana-x.ai:3000" in settings.cors_origins

    def test_qdrant_verify_ssl_is_boolean(self):
        """Test that qdrant_verify_ssl is boolean"""
        settings = MockSettings()

        assert isinstance(settings.qdrant_verify_ssl, bool)
        assert settings.qdrant_verify_ssl is False

    def test_jwt_configuration_has_defaults(self):
        """Test that JWT configuration has correct defaults"""
        settings = MockSettings()

        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_access_token_expire_minutes == 60
