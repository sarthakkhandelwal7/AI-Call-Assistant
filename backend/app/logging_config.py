import logging
from logging.config import dictConfig
import sys

def configure_logging():
    """Configure logging for the application."""
    
    # Define the logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "detailed",
                "level": "DEBUG",
                "filename": "app.log",
            },
            "database_file": {
                "class": "logging.FileHandler",
                "formatter": "detailed",
                "level": "DEBUG",
                "filename": "database.log",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": True,
            },
            "database": {
                "handlers": ["console", "database_file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["database_file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "handlers": ["database_file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }
    
    # Apply the configuration
    dictConfig(logging_config)
    
    # Log that logging has been configured
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully") 