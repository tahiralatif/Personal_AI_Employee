"""
Utils module for the AI Employee system.

This module contains utility functions for file operations, logging, and configuration.
"""

from .logger import get_logger, setup_logging, debug, info, warning, error, critical, log_event
from .file_utils import (
    safe_move_file, safe_copy_file, get_file_size, get_file_type, is_safe_filename,
    sanitize_filename, create_unique_filename, calculate_file_hash, validate_file_size,
    read_file_safely, write_file_safely, ensure_directory_exists, get_files_in_directory,
    get_file_creation_time, get_file_modification_time
)
from .exceptions import (
    AIEmployeeException, ConfigurationError, VaultError, FileOperationError,
    FileSizeError, SecurityError, ValidationError, ProcessingError, HandlerError,
    handle_exception, safe_execute, ExceptionHandlerContext, handle_exceptions
)

__all__ = [
    # Logger functions
    'get_logger', 'setup_logging', 'debug', 'info', 'warning', 'error', 'critical', 'log_event',
    # File utility functions
    'safe_move_file', 'safe_copy_file', 'get_file_size', 'get_file_type', 'is_safe_filename',
    'sanitize_filename', 'create_unique_filename', 'calculate_file_hash', 'validate_file_size',
    'read_file_safely', 'write_file_safely', 'ensure_directory_exists', 'get_files_in_directory',
    'get_file_creation_time', 'get_file_modification_time',
    # Exception classes and functions
    'AIEmployeeException', 'ConfigurationError', 'VaultError', 'FileOperationError',
    'FileSizeError', 'SecurityError', 'ValidationError', 'ProcessingError', 'HandlerError',
    'handle_exception', 'safe_execute', 'ExceptionHandlerContext', 'handle_exceptions'
]