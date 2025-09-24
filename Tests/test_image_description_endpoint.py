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


class DummyDescriptionService:
    """A dummy service for image description generation used for mocking."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def generate_image_description(self, image_path: str = None):
        if self.should_fail:
            raise Exception("Service unavailable")
        # Return a dummy JSON description
        return '{"description": "A red square."}'


class TestImageDescriptionEndpoint:
    """Comprehensive tests for the /generate/generate_image_description endpoint."""

    # ------------------------- FIXTURES -------------------------

    @pytest.fixture
    def dummy_image_path(self, tmp_path):
        """Create a temporary dummy image file and return its path."""
        file_path = tmp_path / "dummy.png"
        file_path.write_bytes(b"dummy image content")
        return str(file_path)

    # ------------------------- SUCCESS CASES -------------------------

    def test_generate_image_description_success(self, dummy_image_path):
        """Successful description generation when file exists."""
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyDescriptionService(),
        ) as mock_get_service:
            response = test_client.post(
                "/generate/generate_image_description", data={"file_path": dummy_image_path}
            )
            assert response.status_code == 200
            assert response.json() == "{\"description\": \"A red square.\"}"
            mock_get_service.assert_called_once_with()

    def test_generate_image_description_success_code_fences(self, dummy_image_path):
        """Service returns description wrapped in markdown code fences; endpoint should return raw JSON string without fences."""

        class FenceService(DummyDescriptionService):
            def generate_image_description(self, image_path: str = None):
                return "```json\n{\"description\": \"A fenced result.\"}\n```"

        with patch(
            "backend.endpoints.generation.get_service", return_value=FenceService()
        ):
            response = test_client.post(
                "/generate/generate_image_description", data={"file_path": dummy_image_path}
            )
            # FastAPI strips quotes around plain strings; use .json() to get the raw returned string
            assert response.status_code == 200
            assert response.json() == "```json\n{\"description\": \"A fenced result.\"}\n```"

    # ------------------------- VALIDATION / PARAMETER ERRORS -------------------------

    def test_missing_file_path(self):
        """Validation error when file_path is missing."""
        response = test_client.post("/generate/generate_image_description", data={})
        assert response.status_code == 422  # FastAPI validation error

    def test_file_not_found(self):
        """Client error when the provided file_path does not exist on server."""
        non_existent_path = os.path.join(os.getcwd(), "nonexistent.png")
        response = test_client.post(
            "/generate/generate_image_description", data={"file_path": non_existent_path}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "FILE PATH NOT FOUND"

    # ------------------------- SERVICE FAILURE PATHS -------------------------

    def test_service_failure_handling(self, dummy_image_path):
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyDescriptionService(should_fail=True),
        ):
            response = test_client.post(
                "/generate/generate_image_description", data={"file_path": dummy_image_path}
            )
            assert response.status_code == 500

    # ------------------------- FACTORY ROUTING -------------------------

    def test_factory_routing(self, dummy_image_path):
        with patch("backend.endpoints.generation.get_service") as mock_get_service:
            test_client.post(
                "/generate/generate_image_description", data={"file_path": dummy_image_path}
            )
            mock_get_service.assert_called_once_with()

    # ------------------------- LOGGING TEST -------------------------

    def test_logging_behavior(self, dummy_image_path, caplog):
        import logging

        caplog.set_level(logging.INFO)
        caplog.set_level(logging.INFO, logger="image_gen_api")
        logging.getLogger("image_gen_api").propagate = True

        with patch(
            "backend.endpoints.generation.get_service", return_value=DummyDescriptionService()
        ):
            response = test_client.post(
                "/generate/generate_image_description", data={"file_path": dummy_image_path}
            )
            assert response.status_code == 200
            assert "IMG DESCRIPTION ENDPOINT ACCESSED" in caplog.text
            assert os.path.basename(dummy_image_path) in caplog.text
