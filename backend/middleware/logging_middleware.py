import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from backend.utils.logger import app_logger
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract request details
        method = request.method
        url = str(request.url)
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Log the incoming request
        app_logger.debug(f"Incoming request: {method} {url} from {client_ip}")
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Log the request completion
            app_logger.log_request(
                method=method,
                url=url,
                client_ip=client_ip,
                user_agent=user_agent,
                status_code=response.status_code,
                processing_time=processing_time
            )
            
            # Log response details for debugging (only for non-successful responses)
            if response.status_code >= 400:
                app_logger.warning(
                    f"Request failed: {method} {url} - Status: {response.status_code} - Time: {processing_time:.3f}s"
                )
            
            return response
            
        except Exception as e:
            # Calculate processing time even for failed requests
            processing_time = time.time() - start_time
            
            # Log the exception
            app_logger.error(
                f"Request failed with exception: {method} {url}",
                exception=e,
                extra={
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "processing_time": processing_time
                }
            )
            
            # Re-raise the exception to let FastAPI handle it
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for reverse proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"


class DetailedLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced logging middleware with request/response body logging for debugging."""
    
    def __init__(self, app, log_bodies: bool = False, max_body_length: int = 1000):
        super().__init__(app)
        self.log_bodies = log_bodies
        self.max_body_length = max_body_length
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with detailed logging."""
        start_time = time.time()
        
        # Extract request details
        method = request.method
        url = str(request.url)
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        request_details = {
            "method": method,
            "url": url,
            "client_ip": client_ip,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params)
        }
        
        # Log request body if enabled (be careful with large files)
        if self.log_bodies and method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) <= self.max_body_length:
                    # Only log if it's likely to be JSON/text
                    try:
                        request_details["body"] = body.decode("utf-8")
                    except UnicodeDecodeError:
                        request_details["body"] = f"<binary data, {len(body)} bytes>"
                else:
                    request_details["body"] = f"<large body, {len(body)} bytes>"
            except Exception as e:
                app_logger.warning(f"Could not read request body: {e}")
        
        # Log the incoming request with details
        app_logger.debug(f"Detailed request log", extra=request_details)
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Log the response details
            response_details = {
                "status_code": response.status_code,
                "processing_time": processing_time,
                "response_headers": dict(response.headers)
            }
            
            app_logger.info(f"Request completed: {method} {url}", extra=response_details)
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            app_logger.error(
                f"Request failed: {method} {url}",
                exception=e,
                extra={
                    "processing_time": processing_time,
                    "request_details": request_details
                }
            )
            
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
