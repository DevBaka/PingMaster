"""Logging configuration for the Network Monitor."""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union

from rich.console import Console
from rich.logging import RichHandler

def setup_logging(
    level: Union[str, int] = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    console: bool = True,
) -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        level: Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        log_file: Path to the log file. If None, no file logging will be configured.
        console: Whether to log to console.
        
    Returns:
        Configured logger instance.
    """
    # Convert string level to logging level
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    logger = logging.getLogger('network_monitor')
    logger.setLevel(level)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler
    if console:
        console_handler = RichHandler(
            console=Console(stderr=True),
            show_time=False,
            show_level=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Capture warnings
    logging.captureWarnings(True)
    
    return logger

class HostLogger:
    """Logger for host-specific events."""
    
    def __init__(self, logger: logging.Logger, host: str):
        """Initialize host logger.
        
        Args:
            logger: Base logger instance.
            host: Hostname or IP address.
        """
        self.logger = logger
        self.host = host
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(f"[{self.host}] {msg}", *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(f"[{self.host}] {msg}", *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(f"[{self.host}] {msg}", *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(f"[{self.host}] {msg}", *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(f"[{self.host}] {msg}", *args, **kwargs)
    
    def status_change(self, old_status: str, new_status: str, details: str = ""):
        """Log host status change.
        
        Args:
            old_status: Previous status.
            new_status: New status.
            details: Additional details about the status change.
        """
        msg = f"Status changed: {old_status} -> {new_status}"
        if details:
            msg += f" ({details})"
        
        if new_status.lower() == 'up':
            self.info(msg)
        elif new_status.lower() == 'down':
            self.warning(msg)
        else:
            self.info(msg)
