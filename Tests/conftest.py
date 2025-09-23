import os
import shutil
import pytest
import sys
import pathlib

# Ensure project root is on PYTHONPATH
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import UPLOAD_DIR
from backend.utils.logger import app_logger

@pytest.fixture(autouse=True, scope="session")
def clean_uploads_dir():

    # Create tmp directory for test files
    tmp_dir = os.path.join(UPLOAD_DIR, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    
    app_logger.info(f"\n[TEST SETUP] Created tmp directory: {tmp_dir}")
    
    yield   # run the tests
    
    # Clean up tmp directory after all tests
    if os.path.exists(tmp_dir):
        app_logger.info(f"\n[TEST CLEANUP] Removing tmp directory: {tmp_dir}")
        try:
            shutil.rmtree(tmp_dir)
            app_logger.info(f"[TEST CLEANUP] Successfully removed tmp directory")
        except OSError as e:
            app_logger.error(f"[TEST CLEANUP] Error removing tmp directory: {e}")
    else:
        app_logger.info(f"\n[TEST CLEANUP] Tmp directory {tmp_dir} does not exist")
