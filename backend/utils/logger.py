import logging
from typing import Optional
import traceback
import json
from datetime import datetime

class AppLogger:
    
    def __init__(self, name: str = "image_gen_api"):
        self.logger = logging.getLogger(name)
        self.access_logger = logging.getLogger(f"{name}.access")
    
    def info(self, message: str, extra: Optional[dict] = None):
        """Log info message."""
        if extra:
            message = f"{message} | Extra: {json.dumps(extra)}"
        self.logger.info(message)
    
    def debug(self, message: str, extra: Optional[dict] = None):
        """Log debug message."""
        if extra:
            message = f"{message} | Extra: {json.dumps(extra)}"
        self.logger.debug(message)
    
    def warning(self, message: str, extra: Optional[dict] = None):
        """Log warning message."""
        if extra:
            message = f"{message} | Extra: {json.dumps(extra)}"
        self.logger.warning(message)
    
    def error(self, message: str, exception: Optional[Exception] = None, extra: Optional[dict] = None):
        """Log error message with optional exception details."""
        if exception:
            message = f"{message} | Exception: {str(exception)} | Traceback: {traceback.format_exc()}"
        if extra:
            message = f"{message} | Extra: {json.dumps(extra)}"
        self.logger.error(message)
    
    def critical(self, message: str, exception: Optional[Exception] = None, extra: Optional[dict] = None):
        """Log critical message with optional exception details."""
        if exception:
            message = f"{message} | Exception: {str(exception)} | Traceback: {traceback.format_exc()}"
        if extra:
            message = f"{message} | Extra: {json.dumps(extra)}"
        self.logger.critical(message)
    
    def log_request(self, method: str, url: str, client_ip: str, user_agent: str = "", status_code: int = 0, processing_time: float = 0.0):
        """Log HTTP request details."""
        message = f"{method} {url} - IP: {client_ip} - Status: {status_code} - Time: {processing_time:.3f}s"
        if user_agent:
            message += f" - User-Agent: {user_agent}"
        self.access_logger.info(message)
    
    def log_service_call(self, service_name: str, method_name: str, parameters: dict, success: bool, execution_time: float = 0.0, error: Optional[str] = None):
        """Log service method calls for debugging."""
        status = "SUCCESS" if success else "FAILURE"
        message = f"Service: {service_name}.{method_name} - Status: {status} - Time: {execution_time:.3f}s"
        
        if parameters:
            # Sanitize sensitive data
            safe_params = {k: v if k not in ['password', 'token', 'key'] else '***' for k, v in parameters.items()}
            message += f" - Params: {json.dumps(safe_params)}"
        
        if error:
            message += f" - Error: {error}"
            self.error(message)
        else:
            self.info(message)

# Global logger instance
app_logger = AppLogger()

# Convenience functions for quick logging
def log_info(message: str, extra: Optional[dict] = None):
    app_logger.info(message, extra)

def log_debug(message: str, extra: Optional[dict] = None):
    app_logger.debug(message, extra)

def log_warning(message: str, extra: Optional[dict] = None):
    app_logger.warning(message, extra)

def log_error(message: str, exception: Optional[Exception] = None, extra: Optional[dict] = None):
    app_logger.error(message, exception, extra)

def log_critical(message: str, exception: Optional[Exception] = None, extra: Optional[dict] = None):
    app_logger.critical(message, exception, extra)
