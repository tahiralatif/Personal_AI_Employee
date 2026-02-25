"""
Custom exceptions for the AI Employee system.

This module defines custom exception classes that follow the error handling
patterns required by the system.
"""


class AIEmployeeException(Exception):
    """
    Base exception class for the AI Employee system.
    All custom exceptions should inherit from this class.
    """
    def __init__(self, message: str, error_code: str = None, original_exception: Exception = None):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            original_exception: Original exception that caused this one (if applicable)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.original_exception = original_exception

    def __str__(self):
        """String representation of the exception."""
        if self.original_exception:
            return f"{self.error_code}: {self.message} (caused by: {type(self.original_exception).__name__}: {self.original_exception})"
        return f"{self.error_code}: {self.message}"

    def __repr__(self):
        """Detailed string representation of the exception."""
        return f"{self.__class__.__name__}(message='{self.message}', error_code='{self.error_code}')"


class ConfigurationError(AIEmployeeException):
    """
    Raised when there's an issue with the system configuration.
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, "CONFIG_ERROR", original_exception)


class VaultError(AIEmployeeException):
    """
    Raised when there's an issue with the vault operations.
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, "VAULT_ERROR", original_exception)


class FileOperationError(AIEmployeeException):
    """
    Raised when there's an issue with file operations.
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, "FILE_OP_ERROR", original_exception)


class FileSizeError(FileOperationError):
    """
    Raised when a file exceeds the maximum allowed size.
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, "FILE_SIZE_ERROR", original_exception)


class SecurityError(AIEmployeeException):
    """
    Raised when a security violation is detected.
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, "SECURITY_ERROR", original_exception)


class ValidationError(AIEmployeeException):
    """
    Raised when data validation fails.
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, "VALIDATION_ERROR", original_exception)


class ProcessingError(AIEmployeeException):
    """
    Raised when there's an error during file processing.
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, "PROCESSING_ERROR", original_exception)


class HandlerError(AIEmployeeException):
    """
    Raised when there's an issue with event handlers.
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, "HANDLER_ERROR", original_exception)


def handle_exception(exception: Exception, logger=None, reraise: bool = True, default_return=None):
    """
    Generic exception handler that follows the system's error handling patterns.

    Args:
        exception: The exception to handle
        logger: Optional logger to log the exception
        reraise: Whether to reraise the exception after handling (default: True)
        default_return: Default value to return if reraise is False

    Returns:
        Default value if reraise is False, otherwise None
    """
    # Log the exception if a logger is provided
    if logger:
        if isinstance(exception, AIEmployeeException):
            logger.error(f"{exception.error_code}: {exception.message}")
        else:
            logger.error(f"UNHANDLED_EXCEPTION: {str(exception)}")

        # Log the full traceback
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

    # Reraise if requested
    if reraise:
        raise exception
    else:
        return default_return


def safe_execute(func, *args, logger=None, exception_map=None, default_return=None, **kwargs):
    """
    Safely execute a function with exception handling.

    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        logger: Optional logger to log exceptions
        exception_map: Dictionary mapping exception types to custom exception types
        default_return: Default value to return if an exception occurs
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Result of the function call or default_return if an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Map the exception if needed
        if exception_map and type(e) in exception_map:
            mapped_exception = exception_map[type(e)](str(e), original_exception=e)
            return handle_exception(mapped_exception, logger, reraise=False, default_return=default_return)

        # Handle the original exception
        return handle_exception(e, logger, reraise=False, default_return=default_return)


class ExceptionHandlerContext:
    """
    Context manager for handling exceptions in a consistent way.
    """
    def __init__(self, logger=None, reraise: bool = True, default_return=None, exception_map=None):
        """
        Initialize the context manager.

        Args:
            logger: Optional logger to log exceptions
            reraise: Whether to reraise exceptions (default: True)
            default_return: Default value to return if an exception occurs
            exception_map: Dictionary mapping exception types to custom exception types
        """
        self.logger = logger
        self.reraise = reraise
        self.default_return = default_return
        self.exception_map = exception_map or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An exception occurred
            if exc_type in self.exception_map:
                # Map to a custom exception
                mapped_exception = self.exception_map[exc_type](str(exc_val), original_exception=exc_val)
                if self.logger:
                    self.logger.error(f"{mapped_exception.error_code}: {mapped_exception.message}")
                if self.reraise:
                    return False  # Don't suppress the exception
                else:
                    return True  # Suppress the exception

            # Log the exception if a logger is provided
            if self.logger:
                self.logger.error(f"EXCEPTION: {exc_type.__name__}: {exc_val}")

            # Decide whether to suppress the exception based on reraise flag
            return not self.reraise

        # No exception occurred
        return True


# Decorator for consistent exception handling
def handle_exceptions(logger=None, exception_map=None, default_return=None):
    """
    Decorator for adding consistent exception handling to functions.

    Args:
        logger: Optional logger to log exceptions
        exception_map: Dictionary mapping exception types to custom exception types
        default_return: Default value to return if an exception occurs
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return safe_execute(
                func,
                *args,
                logger=logger,
                exception_map=exception_map,
                default_return=default_return,
                **kwargs
            )
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage
    from .logger import get_logger

    logger = get_logger()

    # Example 1: Basic exception handling
    try:
        raise ConfigurationError("Invalid configuration value")
    except AIEmployeeException as e:
        print(f"Caught custom exception: {e}")

    # Example 2: Safe execution
    def risky_function(x, y):
        if y == 0:
            raise ValueError("Division by zero")
        return x / y

    result = safe_execute(risky_function, 10, 0, logger=logger, default_return=float('inf'))
    print(f"Result: {result}")

    # Example 3: Context manager
    with ExceptionHandlerContext(logger=logger, default_return=0):
        result = 10 / 0  # This will be caught and return 0
    print(f"Result from context: {result}")

    # Example 4: Decorator
    @handle_exceptions(logger=logger, default_return=0)
    def safe_divide(x, y):
        return x / y

    result = safe_divide(10, 0)
    print(f"Result from decorated function: {result}")