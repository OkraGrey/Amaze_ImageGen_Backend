import logging
import logging.config
from pathlib import Path
import os
from datetime import datetime

# Check if running on Vercel
IS_VERCEL = os.getenv("VERCEL") == "1"

# Create logs directory only if not on Vercel
if not IS_VERCEL:
    LOGS_DIR = Path("logs")
    LOGS_DIR.mkdir(exist_ok=True)
else:
    LOGS_DIR = None  # Not used on Vercel

# Logging configuration dictionary
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOGS_DIR / "app.log" if LOGS_DIR else None,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": LOGS_DIR / "error.log" if LOGS_DIR else None,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
        "access_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "default",
            "filename": LOGS_DIR / "access.log" if LOGS_DIR else "/tmp/access.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "": {  # root logger
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["access_file"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console", "error_file"],
            "propagate": False,
        },
        "fastapi": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "image_gen_api": {  # Our application logger
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "image_gen_api.access": {  # Access logger for our middleware
            "level": "INFO",
            "handlers": ["access_file", "console"],
            "propagate": False,
        },
    },
}

def setup_logging():
    """Setup logging configuration."""
    # On Vercel, only use the console handler
    if IS_VERCEL:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        for handler_name in ['file', 'error_file', 'access_file']:
            if handler_name in LOGGING_CONFIG['handlers']:
                del LOGGING_CONFIG['handlers'][handler_name]

        for logger_name in LOGGING_CONFIG['loggers']:
            if 'handlers' in LOGGING_CONFIG['loggers'][logger_name]:
                LOGGING_CONFIG['loggers'][logger_name]['handlers'] = [
                    h for h in LOGGING_CONFIG['loggers'][logger_name]['handlers'] if 'file' not in h
                ]
        
        # Configure root logger for Vercel
        LOGGING_CONFIG['loggers']['']['handlers'] = ['console']
        
        # Configure uvicorn loggers for Vercel
        LOGGING_CONFIG['loggers']['uvicorn.access']['handlers'] = ['console']
        LOGGING_CONFIG['loggers']['uvicorn.error']['handlers'] = ['console']
        LOGGING_CONFIG['loggers']['fastapi']['handlers'] = ['console']
        LOGGING_CONFIG['loggers']['image_gen_api']['handlers'] = ['console']
        LOGGING_CONFIG['loggers']['image_gen_api.access']['handlers'] = ['console']

    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Create a custom logger for the application
    logger = logging.getLogger("image_gen_api")
    logger.info("Logging configuration setup completed")
    
    return logger

def get_logger(name: str = "image_gen_api"):
    """Get a logger instance."""
    return logging.getLogger(name)
