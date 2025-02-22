import pytest
from unittest.mock import patch
import os

@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests"""
    with patch("app.core.config.get_settings") as mock:
        mock.return_value.OPENAI_API_KEY = "test-key"
        mock.return_value.MAX_FILES = 20
        mock.return_value.MODEL_NAME = "gpt-4"
        mock.return_value.MAX_CRITERIA = 10
        yield mock

@pytest.fixture(autouse=True)
def test_env():
    """Set up test environment variables"""
    os.environ["OPENAI_API_KEY"] = "test-key"
    yield
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
