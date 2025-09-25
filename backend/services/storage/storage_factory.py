import threading
from backend.services.storage.base import FileStorage
from backend.services.storage.local_storage import LocalStorage
from backend.services.storage.google_drive import GoogleDriveStorage
from backend.config.settings import STORAGE_TYPE
from backend.utils.logger import app_logger

# Thread-local storage for service instances
_thread_local = threading.local()

def get_storage_service():
    """
    Factory function to get the appropriate storage service.
    Ensures that each thread gets its own service instance.
    """
    app_logger.info(f"GETTING STORAGE SERVICE FOR TYPE: {STORAGE_TYPE}")
    
    # Check if a service instance already exists for this thread
    storage_service = getattr(_thread_local, 'storage_service', None)
    
    if storage_service is None:
        app_logger.info(f"CREATING NEW STORAGE SERVICE INSTANCE FOR THREAD: {threading.current_thread().name}")
        if STORAGE_TYPE == "local":
            storage_service = LocalStorage()
        elif STORAGE_TYPE == "gcp":
            storage_service = GoogleDriveStorage()
        else:
            raise ValueError(f"Unknown storage type: {STORAGE_TYPE}")
        
        # Save the instance in thread-local storage
        _thread_local.storage_service = storage_service
    else:
        app_logger.info(f"REUSING STORAGE SERVICE INSTANCE FOR THREAD: {threading.current_thread().name}")
        
    app_logger.info(f"RETURNING STORAGE SERVICE OBJECT")
    return storage_service
