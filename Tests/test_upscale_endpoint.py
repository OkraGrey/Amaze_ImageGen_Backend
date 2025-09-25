import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
import concurrent.futures
import os, sys, pathlib
from PIL import Image

# Ensure project root is on PYTHONPATH so that `import app` works regardless of where tests are run
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app  # Root-level app.py


# Test client setup
test_client = TestClient(app)


class MockPicsartUpscaleService:
    """A mock Picsart upscale service for testing."""

    def __init__(self, should_fail: bool = False, fail_with_not_found: bool = False, fail_with_api_error: bool = False):
        self.should_fail = should_fail
        self.fail_with_not_found = fail_with_not_found
        self.fail_with_api_error = fail_with_api_error

    def upscale_image(self, image_identifier: str, upscale_factor: int):
        if self.fail_with_not_found:
            raise FileNotFoundError(f"Image with identifier {image_identifier} not found.")
        if self.fail_with_api_error:
            raise Exception("Picsart API error")
        if self.should_fail:
            raise Exception("Service unavailable")
        
        # Simulate successful upscaling with mock resolutions
        if upscale_factor == 2:
            return "mock_upscaled_id_2x", "512x512", "1024x1024"
        elif upscale_factor == 4:
            return "mock_upscaled_id_4x", "512x512", "2048x2048"


class MockStorageService:
    """A mock storage service for testing."""

    def get_results_uri(self, identifier: str):
        return f"https://mock-storage.com/results/{identifier}"


class TestUpscaleEndpoint:
    """Comprehensive tests for the /upscale endpoint."""

    # ------------------------- FIXTURES -------------------------

    @pytest.fixture
    def mock_storage_service(self):
        """Mock storage service fixture."""
        return MockStorageService()

    @pytest.fixture
    def mock_upscale_service(self):
        """Mock upscale service fixture."""
        return MockPicsartUpscaleService()

    @pytest.fixture
    def mock_upscale_service_not_found(self):
        """Mock upscale service that raises FileNotFoundError."""
        return MockPicsartUpscaleService(fail_with_not_found=True)

    @pytest.fixture
    def mock_upscale_service_api_error(self):
        """Mock upscale service that raises API error."""
        return MockPicsartUpscaleService(fail_with_api_error=True)

    # ------------------------- SUCCESS CASES -------------------------

    @pytest.mark.parametrize("upscale_factor", [2, 4])
    def test_upscale_image_success(self, upscale_factor, mock_storage_service):
        """Test successful image upscaling with valid scale factors."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService()
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={
                    "image_identifier": "test_image_123",
                    "upscale_factor": upscale_factor
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Image upscaled successfully"
            assert "result_path" in data
            assert "result_identifier" in data
            assert "input_resolution" in data
            assert "upscaled_resolution" in data
            assert data["input_resolution"] == "512x512"
            
            # Check expected upscaled resolution based on factor
            if upscale_factor == 2:
                assert data["upscaled_resolution"] == "1024x1024"
                assert data["result_identifier"] == "mock_upscaled_id_2x"
            elif upscale_factor == 4:
                assert data["upscaled_resolution"] == "2048x2048"
                assert data["result_identifier"] == "mock_upscaled_id_4x"

    # ------------------------- VALIDATION / PARAMETER ERRORS -------------------------

    def test_missing_image_identifier(self):
        """Test missing image_identifier parameter."""
        response = test_client.post("/upscale", data={"upscale_factor": 2})
        assert response.status_code == 422  # FastAPI validation error

    def test_missing_upscale_factor(self):
        """Test missing upscale_factor parameter."""
        response = test_client.post("/upscale", data={"image_identifier": "test_123"})
        assert response.status_code == 422  # FastAPI validation error

    def test_empty_image_identifier(self, mock_storage_service):
        """Test empty image_identifier."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService(fail_with_not_found=True)
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={"image_identifier": "", "upscale_factor": 2}
            )
            # Should be 404 since empty identifier won't be found
            assert response.status_code == 404

    @pytest.mark.parametrize("invalid_factor", [1, 3, 5, 8, 10, 0, -1, -2])
    def test_invalid_upscale_factor(self, invalid_factor):
        """Test invalid upscale factors (only 2 and 4 are allowed)."""
        response = test_client.post(
            "/upscale",
            data={
                "image_identifier": "test_image_123",
                "upscale_factor": invalid_factor
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "Upscale factor must be 2 or 4" in data["detail"]

    @pytest.mark.parametrize("invalid_factor", ["two", "four", "2.5", "abc", "null", ""])
    def test_non_integer_upscale_factor(self, invalid_factor):
        """Test non-integer upscale factors."""
        response = test_client.post(
            "/upscale",
            data={
                "image_identifier": "test_image_123",
                "upscale_factor": invalid_factor
            }
        )
        assert response.status_code == 422  # FastAPI validation error

    def test_null_image_identifier(self, mock_storage_service):
        """Test null/None image_identifier."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService(fail_with_not_found=True)
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={"image_identifier": None, "upscale_factor": 2}
            )
            # Should be 404 since null identifier won't be found
            assert response.status_code == 404

    def test_null_upscale_factor(self):
        """Test null/None upscale_factor."""
        response = test_client.post(
            "/upscale",
            data={"image_identifier": "test_123", "upscale_factor": None}
        )
        assert response.status_code == 422

    # ------------------------- ERROR HANDLING -------------------------

    def test_image_not_found(self, mock_storage_service):
        """Test handling when image identifier is not found."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService(fail_with_not_found=True)
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={
                    "image_identifier": "nonexistent_image_123",
                    "upscale_factor": 2
                }
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()

    def test_picsart_api_error(self, mock_storage_service):
        """Test handling of Picsart API errors."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService(fail_with_api_error=True)
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={
                    "image_identifier": "test_image_123",
                    "upscale_factor": 2
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Picsart API error" in data["detail"]

    def test_general_service_failure(self, mock_storage_service):
        """Test general service failure handling."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService(should_fail=True)
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={
                    "image_identifier": "test_image_123",
                    "upscale_factor": 4
                }
            )
            
            assert response.status_code == 500

    def test_picsart_api_key_missing(self, mock_storage_service):
        """Test handling when Picsart API key is not configured."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            # Mock the service to raise ValueError for missing API key
            mock_service_class.side_effect = ValueError("Picsart API key is not configured.")
            
            response = test_client.post(
                "/upscale",
                data={
                    "image_identifier": "test_image_123",
                    "upscale_factor": 2
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Picsart API key is not configured" in data["detail"]

    # ------------------------- EDGE CASES -------------------------

    def test_very_long_image_identifier(self, mock_storage_service):
        """Test with extremely long image identifier."""
        long_identifier = "a" * 1000
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService()
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={
                    "image_identifier": long_identifier,
                    "upscale_factor": 2
                }
            )
            
            # Should handle gracefully, either success or proper error
            assert response.status_code in (200, 400, 404, 500)

    @pytest.mark.parametrize(
        "special_identifier",
        [
            "test_123-abc",
            "test.123.abc",
            "test_123_ABC_456",
            "test@123",
            "test#123",
            "test%123",
            "test&123",
            "test 123",  # with space
            "test\t123",  # with tab
            "test\n123",  # with newline
        ],
    )
    def test_special_characters_in_identifier(self, special_identifier, mock_storage_service):
        """Test image identifiers with special characters."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService()
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={
                    "image_identifier": special_identifier,
                    "upscale_factor": 4
                }
            )
            
            # Should handle gracefully
            assert response.status_code in (200, 400, 404, 422, 500)

    def test_concurrent_upscale_requests(self, mock_storage_service):
        """Test concurrent upscale requests."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService()
            mock_service_class.return_value = mock_service_instance
            
            def make_request(idx):
                return test_client.post(
                    "/upscale",
                    data={
                        "image_identifier": f"concurrent_test_{idx}",
                        "upscale_factor": 2 if idx % 2 == 0 else 4
                    }
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(make_request, i) for i in range(6)]
                responses = [f.result() for f in futures]

            for r in responses:
                assert r.status_code == 200

    # ------------------------- RESPONSE FORMAT VALIDATION -------------------------

    def test_response_format_validation(self, mock_storage_service):
        """Test that the response contains all required fields in correct format."""
        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService()
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={
                    "image_identifier": "test_image_123",
                    "upscale_factor": 2
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate response structure
            required_fields = ["success", "message", "result_path", "result_identifier", "input_resolution", "upscaled_resolution"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Validate data types
            assert isinstance(data["success"], bool)
            assert isinstance(data["message"], str)
            assert isinstance(data["result_path"], str)
            assert isinstance(data["result_identifier"], str)
            assert isinstance(data["input_resolution"], str)
            assert isinstance(data["upscaled_resolution"], str)
            
            # Validate resolution format (should be "WIDTHxHEIGHT")
            assert "x" in data["input_resolution"]
            assert "x" in data["upscaled_resolution"]
            
            # Validate resolution values are numeric
            input_parts = data["input_resolution"].split("x")
            upscaled_parts = data["upscaled_resolution"].split("x")
            assert len(input_parts) == 2
            assert len(upscaled_parts) == 2
            assert input_parts[0].isdigit()
            assert input_parts[1].isdigit()
            assert upscaled_parts[0].isdigit()
            assert upscaled_parts[1].isdigit()

    # ------------------------- LOGGING TEST -------------------------

    def test_logging_behavior(self, caplog, mock_storage_service):
        """Test that proper logging occurs during upscale operations."""
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.INFO, logger="image_gen_api")
        logging.getLogger("image_gen_api").propagate = True

        with patch("backend.endpoints.generation.get_storage_service", return_value=mock_storage_service), \
             patch("backend.endpoints.generation.PicsartUpscaleService") as mock_service_class:
            
            mock_service_instance = MockPicsartUpscaleService()
            mock_service_class.return_value = mock_service_instance
            
            response = test_client.post(
                "/upscale",
                data={
                    "image_identifier": "log_test_123",
                    "upscale_factor": 4
                }
            )
            
            assert response.status_code == 200
            assert "UPSCALE IMAGE ENDPOINT ACCESSED" in caplog.text
            assert "log_test_123" in caplog.text
            assert "4" in caplog.text


# ------------------------- PYTEST EVENT LOOP FIXTURE -------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
