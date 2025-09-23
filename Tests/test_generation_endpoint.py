import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO
import concurrent.futures
import threading
import os, sys, pathlib
# Ensure project root is on PYTHONPATH so that `import app` works regardless of where tests are run
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app  # Root-level app.py


# Test client setup
test_client = TestClient(app)

class DummyService:
    """A dummy image generation service used for mocking."""

    def __init__(self, should_fail: bool = False, raise_timeout: bool = False):
        self.should_fail = should_fail
        self.raise_timeout = raise_timeout

    def generate_image(self, prompt: str, image_path: str = None):
        if self.raise_timeout:
            raise asyncio.TimeoutError("Request timeout")
        if self.should_fail:
            raise Exception("Service unavailable")
        # Simulate successful generation by returning a dummy path
        return "/dummy/results/generated.png"


class TestImageGenerationEndpoint:
    """Comprehensive tests for the /generate endpoint."""

    # ------------------------- FIXTURES -------------------------

    @pytest.fixture
    def sample_image_file(self):
        """Create a sample in-memory PNG image."""
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return ("test_image.png", img_bytes, "image/png")

    @pytest.fixture
    def sample_text_file(self):
        """Create a sample text file (invalid type)."""
        text_bytes = BytesIO(b"This is a text file")
        return ("test.txt", text_bytes, "text/plain")

    # ------------------------- SUCCESS CASES -------------------------

    @pytest.mark.parametrize("model", ["openai", "gemini"])
    def test_generate_image_prompt_only_success(self, model):
        """Successful generation using only prompt."""
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(),
        ) as mock_get_service:
            response = test_client.post("/generate", data={"prompt": "A sunset", "model": model})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "result_path" in data
            mock_get_service.assert_called_once_with(model)

    @pytest.mark.parametrize("model", ["openai", "gemini"])
    def test_generate_image_with_file_success(self, model, sample_image_file):
        """Successful generation when a file is attached."""
        filename, content, ctype = sample_image_file
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(),
        ):
            response = test_client.post(
                "/generate",
                data={"prompt": "Modify this image", "model": model},
                files={"file": (filename, content, ctype)},
            )
            assert response.status_code == 200
            assert response.json()["success"] is True

    # ------------------------- VALIDATION / PARAMETER ERRORS -------------------------

    def test_missing_prompt(self):
        response = test_client.post("/generate", data={"model": "openai"})
        assert response.status_code == 422  # FastAPI validation error

    def test_missing_model(self):
        response = test_client.post("/generate", data={"prompt": "Hello"})
        assert response.status_code == 422

    def test_empty_prompt(self):
        response = test_client.post("/generate", data={"prompt": "", "model": "openai"})
        assert response.status_code in (400, 422)

    @pytest.mark.parametrize("invalid_model", ["gpt4", "claude", "dall-e", "invalid"])
    def test_invalid_model(self, invalid_model):
        response = test_client.post("/generate", data={"prompt": "Hi", "model": invalid_model})
        assert response.status_code in (400, 422)

    @pytest.mark.parametrize("case_variant", [
        "OPENAI",
        "OpenAI",
        "Openai",
        "GEMINI",
        "Gemini",
        "GeMiNi",
    ])
    def test_model_case_sensitivity(self, case_variant):
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(),
        ):
            response = test_client.post("/generate", data={"prompt": "Case test", "model": case_variant})
            assert response.status_code in (200, 400, 422)

    # ------------------------- FILE HANDLING -------------------------

    def test_invalid_file_type(self, sample_text_file):
        filename, content, ctype = sample_text_file
        response = test_client.post(
            "/generate",
            data={"prompt": "Process file", "model": "openai"},
            files={"file": (filename, content, ctype)},
        )
        assert response.status_code in (400, 422)

    def test_large_file_upload(self):
        large_bytes = BytesIO(b"x" * (10 * 1024 * 1024 + 1))  # 10MB + 1 byte
        response = test_client.post(
            "/generate",
            data={"prompt": "Large file", "model": "openai"},
            files={"file": ("large.png", large_bytes, "image/png")},
        )
        assert response.status_code in (400, 413, 422)

    def test_corrupted_image_file(self):
        corrupted_bytes = BytesIO(b"not an image")
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(),
        ):
            response = test_client.post(
                "/generate",
                data={"prompt": "Corrupted", "model": "gemini"},
                files={"file": ("broken.png", corrupted_bytes, "image/png")},
            )
            assert response.status_code in (200, 400, 422)

    # ------------------------- SERVICE FAILURE PATHS -------------------------

    def test_service_failure_handling(self):
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(should_fail=True),
        ):
            response = test_client.post("/generate", data={"prompt": "fail", "model": "openai"})
            assert response.status_code == 500

    def test_service_timeout_handling(self):
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(raise_timeout=True),
        ):
            response = test_client.post("/generate", data={"prompt": "timeout", "model": "gemini"})
            assert response.status_code in (500, 504)

    # ------------------------- FACTORY ROUTING -------------------------

    def test_factory_routing(self):
        with patch("backend.endpoints.generation.get_service") as mock_get_service:
            # OpenAI call
            test_client.post("/generate", data={"prompt": "x", "model": "openai"})
            mock_get_service.assert_called_with("openai")

            # Gemini call
            test_client.post("/generate", data={"prompt": "y", "model": "gemini"})
            mock_get_service.assert_called_with("gemini")

    # ------------------------- EDGE CASES -------------------------

    def test_very_long_prompt(self):
        long_prompt = "A" * 10000
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(),
        ):
            response = test_client.post("/generate", data={"prompt": long_prompt, "model": "openai"})
            assert response.status_code in (200, 400, 422)

    @pytest.mark.parametrize(
        "prompt",
        [
            "Hello 世界! 🌍",
            "Prompt with <html>tags</html>",
            "Prompt with 'quotes' and \"double quotes\"",
            "Prompt with newlines\nand\ttabs",
            "Prompt with unicode: ñáéíóú àèìòù",
        ],
    )
    def test_special_characters_prompt(self, prompt):
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(),
        ):
            response = test_client.post("/generate", data={"prompt": prompt, "model": "openai"})
            assert response.status_code in (200, 400, 422)

    def test_concurrent_requests(self):
        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(),
        ):
            def make_request(idx):
                return test_client.post(
                    "/generate",
                    data={"prompt": f"Concurrent {idx}", "model": "openai"},
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request, i) for i in range(10)]
                responses = [f.result() for f in futures]

            for r in responses:
                assert r.status_code == 200

    # ------------------------- LOGGING TEST -------------------------

    def test_logging_behavior(self, caplog):
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.INFO, logger="image_gen_api")
        logging.getLogger("image_gen_api").propagate = True

        with patch(
            "backend.endpoints.generation.get_service",
            return_value=DummyService(),
        ):
            response = test_client.post("/generate", data={"prompt": "log", "model": "openai"})
            assert response.status_code == 200
            assert "GENERATE IMAGE ENDPOINT ACCESSED" in caplog.text
            assert "log" in caplog.text
            assert "openai" in caplog.text


# ------------------------- PYTEST EVENT LOOP FIXTURE -------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
