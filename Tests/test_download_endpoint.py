import pytest
import pathlib
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, ANY

# Ensure project root is on PYTHONPATH so that `import app` works regardless of where tests are run
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app  # Root-level FastAPI app

test_client = TestClient(app)


class TestDownloadEndpoint:
    """Comprehensive tests for the /download endpoint."""

    # ------------------------- FIXTURES -------------------------

    @pytest.fixture
    def dummy_file_path(self, tmp_path):
        """Create a temporary dummy file path for testing."""
        file_path = tmp_path / "dummy.png"
        file_path.write_bytes(b"dummy image content")
        return str(file_path)

    # ------------------------- SUCCESS CASES -------------------------

    def test_download_success(self, dummy_file_path, monkeypatch):
        """Successful background removal when API key is set and service succeeds."""
        # Patch settings constant used by endpoint
        monkeypatch.setattr("backend.endpoints.generation.PHOTOTOOM_API_KEY", "dummy_api_key", raising=False)

        with patch(
            "backend.endpoints.generation.process_download_image",
            return_value="/results/dummy_NO_BG.png",
        ) as mock_process:
            response = test_client.post("/download", data={"file_path": dummy_file_path})
            assert response.status_code == 200
            # FastAPI wraps plain string responses in JSON quotes, so .json() returns the string
            assert response.json() == "/results/dummy_NO_BG.png"
            mock_process.assert_called_once_with(input_path=dummy_file_path, api_key=ANY)

    # ------------------------- VALIDATION / PARAMETER ERRORS -------------------------

    def test_missing_file_path(self):
        """Validation error when file_path is missing."""
        response = test_client.post("/download", data={})
        assert response.status_code == 422  # FastAPI validation error

    def test_missing_api_key(self, dummy_file_path, monkeypatch):
        """Server error when API key environment variable is not set."""
        # Ensure constant is unset/empty for failure case
        monkeypatch.setattr("backend.endpoints.generation.PHOTOTOOM_API_KEY", "", raising=False)
        response = test_client.post("/download", data={"file_path": dummy_file_path})
        assert response.status_code == 500

    # ------------------------- SERVICE FAILURE PATHS -------------------------

    def test_service_failure_handling(self, dummy_file_path, monkeypatch):
        """Server error when the underlying background removal service raises an exception."""
        monkeypatch.setattr("backend.endpoints.generation.PHOTOTOOM_API_KEY", "dummy_api_key", raising=False)

        with patch(
            "backend.endpoints.generation.process_download_image",
            side_effect=Exception("Service failure"),
        ):
            response = test_client.post("/download", data={"file_path": dummy_file_path})
            assert response.status_code == 500
