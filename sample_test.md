import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO
import tempfile
import os
from PIL import Image

# Assuming your main app structure
from your_app import app  # Replace with your actual app import

# Test client setup
client = TestClient(app)

class TestImageGenerationAPI:
    """Comprehensive test suite for image generation endpoint."""
    
    @pytest.fixture
    def sample_image_file(self):
        """Create a sample image file for testing."""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return ("test_image.png", img_bytes, "image/png")
    
    @pytest.fixture
    def sample_text_file(self):
        """Create a sample text file for testing invalid file types."""
        text_content = BytesIO(b"This is a text file")
        return ("test.txt", text_content, "text/plain")

    # ==================== SUCCESS CASES ====================
    
    def test_generate_image_with_openai_prompt_only(self):
        """Test successful image generation with OpenAI and prompt only."""
        with patch('your_service_module.generate_image_service') as mock_service:
            mock_service.return_value = {"image_url": "http://example.com/image.png", "status": "success"}
            
            response = client.post(
                "/generate",
                data={
                    "prompt": "A beautiful sunset",
                    "model": "openai"
                }
            )
            
            assert response.status_code == 200
            assert "image_url" in response.json()
            mock_service.assert_called_once()

    def test_generate_image_with_gemini_prompt_only(self):
        """Test successful image generation with Gemini and prompt only."""
        with patch('your_service_module.generate_image_service') as mock_service:
            mock_service.return_value = {"image_url": "http://example.com/image.png", "status": "success"}
            
            response = client.post(
                "/generate",
                data={
                    "prompt": "A mountain landscape",
                    "model": "gemini"
                }
            )
            
            assert response.status_code == 200
            assert "image_url" in response.json()

    def test_generate_image_with_file_attachment_openai(self, sample_image_file):
        """Test successful image generation with file attachment and OpenAI."""
        with patch('your_service_module.generate_image_service') as mock_service:
            mock_service.return_value = {"image_url": "http://example.com/image.png", "status": "success"}
            
            filename, file_content, content_type = sample_image_file
            
            response = client.post(
                "/generate",
                data={
                    "prompt": "Modify this image",
                    "model": "openai"
                },
                files={"file": (filename, file_content, content_type)}
            )
            
            assert response.status_code == 200
            assert "image_url" in response.json()

    def test_generate_image_with_file_attachment_gemini(self, sample_image_file):
        """Test successful image generation with file attachment and Gemini."""
        with patch('your_service_module.generate_image_service') as mock_service:
            mock_service.return_value = {"image_url": "http://example.com/image.png", "status": "success"}
            
            filename, file_content, content_type = sample_image_file
            
            response = client.post(
                "/generate",
                data={
                    "prompt": "Enhance this image",
                    "model": "gemini"
                },
                files={"file": (filename, file_content, content_type)}
            )
            
            assert response.status_code == 200
            assert "image_url" in response.json()

    # ==================== VALIDATION FAILURE CASES ====================
    
    def test_missing_prompt_parameter(self):
        """Test failure when prompt parameter is missing."""
        response = client.post(
            "/generate",
            data={"model": "openai"}
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("prompt" in str(error).lower() for error in error_detail)

    def test_missing_model_parameter(self):
        """Test failure when model parameter is missing."""
        response = client.post(
            "/generate",
            data={"prompt": "A beautiful sunset"}
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("model" in str(error).lower() for error in error_detail)

    def test_empty_prompt(self):
        """Test failure when prompt is empty."""
        response = client.post(
            "/generate",
            data={
                "prompt": "",
                "model": "openai"
            }
        )
        
        # Should either fail validation or handle gracefully
        assert response.status_code in [400, 422]

    def test_invalid_model_name(self):
        """Test failure when invalid model name is provided."""
        invalid_models = ["gpt4", "claude", "invalid", "dall-e", "midjourney"]
        
        for model in invalid_models:
            response = client.post(
                "/generate",
                data={
                    "prompt": "A beautiful sunset",
                    "model": model
                }
            )
            
            assert response.status_code in [400, 422], f"Model '{model}' should be rejected"

    def test_model_case_sensitivity(self):
        """Test model name case sensitivity."""
        case_variations = ["OPENAI", "OpenAI", "Openai", "GEMINI", "Gemini", "GeMiNi"]
        
        for model in case_variations:
            response = client.post(
                "/generate",
                data={
                    "prompt": "A beautiful sunset",
                    "model": model
                }
            )
            
            # Depending on your implementation, this might succeed or fail
            # Adjust assertion based on your case-sensitivity requirements
            assert response.status_code in [200, 400, 422]

    # ==================== FILE HANDLING TESTS ====================
    
    def test_invalid_file_type(self, sample_text_file):
        """Test handling of invalid file types."""
        filename, file_content, content_type = sample_text_file
        
        response = client.post(
            "/generate",
            data={
                "prompt": "Process this file",
                "model": "openai"
            },
            files={"file": (filename, file_content, content_type)}
        )
        
        # Should either reject invalid file type or handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_large_file_upload(self):
        """Test handling of large file uploads."""
        # Create a large dummy file (e.g., 10MB)
        large_file_content = BytesIO(b"x" * (10 * 1024 * 1024))
        
        response = client.post(
            "/generate",
            data={
                "prompt": "Process this large image",
                "model": "openai"
            },
            files={"file": ("large_image.png", large_file_content, "image/png")}
        )
        
        # Should handle large files appropriately (reject or process)
        assert response.status_code in [200, 413, 422]

    def test_corrupted_image_file(self):
        """Test handling of corrupted image files."""
        corrupted_content = BytesIO(b"This is not a valid image file content")
        
        response = client.post(
            "/generate",
            data={
                "prompt": "Process this corrupted image",
                "model": "gemini"
            },
            files={"file": ("corrupted.png", corrupted_content, "image/png")}
        )
        
        # Should handle corrupted files gracefully
        assert response.status_code in [200, 400, 422]

    # ==================== SERVICE INTEGRATION TESTS ====================
    
    def test_service_failure_handling(self):
        """Test handling when the underlying service fails."""
        with patch('your_service_module.generate_image_service') as mock_service:
            mock_service.side_effect = Exception("Service unavailable")
            
            response = client.post(
                "/generate",
                data={
                    "prompt": "A beautiful sunset",
                    "model": "openai"
                }
            )
            
            assert response.status_code == 500

    def test_service_timeout_handling(self):
        """Test handling when the service times out."""
        with patch('your_service_module.generate_image_service') as mock_service:
            mock_service.side_effect = asyncio.TimeoutError("Request timeout")
            
            response = client.post(
                "/generate",
                data={
                    "prompt": "A complex scene",
                    "model": "gemini"
                }
            )
            
            assert response.status_code in [500, 504]

    def test_factory_pattern_model_routing(self):
        """Test that different models route to correct factory objects."""
        with patch('your_service_module.get_factory') as mock_factory:
            mock_openai_factory = Mock()
            mock_gemini_factory = Mock()
            
            # Test OpenAI routing
            mock_factory.return_value = mock_openai_factory
            client.post("/generate", data={"prompt": "test", "model": "openai"})
            mock_factory.assert_called_with("openai")
            
            # Test Gemini routing
            mock_factory.return_value = mock_gemini_factory
            client.post("/generate", data={"prompt": "test", "model": "gemini"})
            mock_factory.assert_called_with("gemini")

    # ==================== EDGE CASES ====================
    
    def test_very_long_prompt(self):
        """Test handling of very long prompts."""
        long_prompt = "A" * 10000  # 10k character prompt
        
        response = client.post(
            "/generate",
            data={
                "prompt": long_prompt,
                "model": "openai"
            }
        )
        
        # Should either process or reject based on your limits
        assert response.status_code in [200, 400, 422]

    def test_special_characters_in_prompt(self):
        """Test handling of special characters in prompts."""
        special_prompts = [
            "Hello 世界! 🌍",
            "Prompt with <html>tags</html>",
            "Prompt with 'quotes' and \"double quotes\"",
            "Prompt with newlines\nand\ttabs",
            "Prompt with unicode: ñáéíóú àèìòù",
        ]
        
        for prompt in special_prompts:
            response = client.post(
                "/generate",
                data={
                    "prompt": prompt,
                    "model": "openai"
                }
            )
            
            assert response.status_code in [200, 400, 422]

    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            return client.post(
                "/generate",
                data={
                    "prompt": f"Concurrent test {threading.current_thread().ident}",
                    "model": "openai"
                }
            )
        
        with patch('your_service_module.generate_image_service') as mock_service:
            mock_service.return_value = {"image_url": "http://example.com/image.png"}
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                responses = [future.result() for future in futures]
            
            # All requests should complete successfully
            for response in responses:
                assert response.status_code == 200

    # ==================== LOGGING TESTS ====================
    
    def test_logging_behavior(self, caplog):
        """Test that appropriate logs are generated."""
        with patch('your_service_module.generate_image_service') as mock_service:
            mock_service.return_value = {"image_url": "http://example.com/image.png"}
            
            response = client.post(
                "/generate",
                data={
                    "prompt": "Test logging",
                    "model": "openai"
                }
            )
            
            # Check that logs contain expected information
            assert "GENERATE IMAGE ENDPOINT ACCESSED" in caplog.text
            assert "Test logging" in caplog.text
            assert "openai" in caplog.text


# ==================== PYTEST CONFIGURATION ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== TEST RUNNER COMMANDS ====================
"""
To run these tests, use:

# Run all tests
pytest test_image_generation.py -v

# Run specific test categories
pytest test_image_generation.py::TestImageGenerationAPI::test_generate_image_with_openai_prompt_only -v

# Run with coverage
pytest test_image_generation.py --cov=your_app --cov-report=html

# Run tests in parallel
pytest test_image_generation.py -n auto

# Run only fast tests (exclude slow integration tests)
pytest test_image_generation.py -m "not slow"

# Run tests and generate report
pytest test_image_generation.py --html=report.html --self-contained-html
"""