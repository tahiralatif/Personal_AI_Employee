"""Error recovery system for Gold Tier AI Employee.

This module provides:
- Exponential backoff with jitter
- Circuit breaker pattern
- Health status tracking
- Error classification
"""
import asyncio
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types."""
    TRANSIENT = "transient"  # Temporary, retry will likely succeed
    PERMANENT = "permanent"  # Retry won't help (e.g., auth failure)
    RATE_LIMIT = "rate_limit"  # Rate limited, wait and retry
    TIMEOUT = "timeout"  # Operation timed out
    NETWORK = "network"  # Network connectivity issue
    SERVER_ERROR = "server_error"  # 5xx server error
    CLIENT_ERROR = "client_error"  # 4xx client error
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, stop calling
    HALF_OPEN = "half_open"  # Testing if recovered


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"  # All systems operational
    DEGRADED = "degraded"  # Some issues but functional
    UNHEALTHY = "unhealthy"  # Critical failures
    UNKNOWN = "unknown"  # Not yet checked


class CircuitBreaker:
    """Circuit breaker pattern implementation.
    
    Prevents cascading failures by stopping calls to failing services.
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)
        
        @breaker
        def api_call():
            return requests.get(url)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,
        half_open_max_calls: int = 3
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again (half-open)
            half_open_max_calls: Successful calls needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change = datetime.now()
        
    def record_success(self):
        """Record a successful call."""
        self.success_count += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.half_open_max_calls:
                self._set_state(CircuitState.CLOSED)
        elif self.state == CircuitState.CLOSED:
            # Reset success count in closed state to avoid overflow
            self.success_count = 0
    
    def record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Immediately open on failure in half-open state
            self._set_state(CircuitState.OPEN)
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._set_state(CircuitState.OPEN)
    
    def _set_state(self, new_state: CircuitState):
        """Change circuit state."""
        old_state = self.state
        self.state = new_state
        self.last_state_change = datetime.now()
        
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0
        
        logger.info(f"Circuit breaker state changed: {old_state.value} → {new_state.value}")
    
    def can_execute(self) -> bool:
        """Check if call can be executed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time is None:
                return False
            
            # Check if recovery timeout has passed
            time_since_failure = datetime.now() - self.last_failure_time
            if time_since_failure.total_seconds() >= self.recovery_timeout:
                self._set_state(CircuitState.HALF_OPEN)
                return True
            return False
        
        # HALF_OPEN: allow limited calls
        return self.success_count < self.half_open_max_calls
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "can_execute": self.can_execute()
        }
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is {self.state.value}"
                )
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise
        
        return wrapper


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


def retry_with_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[tuple] = None
):
    """Decorator for retry with exponential backoff and jitter.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter
        retryable_exceptions: Tuple of exception types to retry on
        
    Usage:
        @retry_with_backoff(max_retries=5, base_delay=1.0)
        def api_call():
            return requests.get(url)
    """
    if retryable_exceptions is None:
        retryable_exceptions = (Exception,)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}",
                            exc_info=True
                        )
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # Add jitter (±10% of delay)
                    if jitter:
                        jitter_value = delay * 0.1 * random.random()
                        delay = delay + jitter_value
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f}s. Error: {str(e)}"
                    )
                    time.sleep(delay)
                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator


async def retry_with_backoff_async(
    func: Callable,
    *args,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[tuple] = None,
    **kwargs
) -> Any:
    """Async version of retry with exponential backoff.
    
    Args:
        func: Async function to retry
        *args: Positional arguments for func
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter
        retryable_exceptions: Tuple of exception types to retry on
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from successful func call
        
    Usage:
        result = await retry_with_backoff_async(
            api_call,
            url,
            max_retries=5,
            base_delay=1.0
        )
    """
    if retryable_exceptions is None:
        retryable_exceptions = (Exception,)
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(
                    f"Max retries ({max_retries}) exceeded for {func.__name__}",
                    exc_info=True
                )
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                base_delay * (exponential_base ** attempt),
                max_delay
            )
            
            # Add jitter
            if jitter:
                jitter_value = delay * 0.1 * random.random()
                delay = delay + jitter_value
            
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                f"Retrying in {delay:.2f}s. Error: {str(e)}"
            )
            await asyncio.sleep(delay)
        except Exception as e:
            # Non-retryable exception
            logger.error(f"Non-retryable error in {func.__name__}: {e}")
            raise
    
    if last_exception:
        raise last_exception


def classify_error(exception: Exception, status_code: Optional[int] = None) -> ErrorType:
    """Classify an exception into an error type.
    
    Args:
        exception: The exception to classify
        status_code: HTTP status code if applicable
        
    Returns:
        ErrorType classification
    """
    import requests
    
    # Check for requests exceptions
    if isinstance(exception, requests.exceptions.Timeout):
        return ErrorType.TIMEOUT
    elif isinstance(exception, requests.exceptions.ConnectionError):
        return ErrorType.NETWORK
    elif isinstance(exception, requests.exceptions.HTTPError):
        if status_code:
            if 400 <= status_code < 500:
                if status_code == 429:
                    return ErrorType.RATE_LIMIT
                return ErrorType.CLIENT_ERROR
            elif 500 <= status_code < 600:
                return ErrorType.SERVER_ERROR
    elif isinstance(exception, CircuitBreakerOpenError):
        return ErrorType.PERMANENT
    
    # Check exception message for common patterns
    error_msg = str(exception).lower()
    if "timeout" in error_msg:
        return ErrorType.TIMEOUT
    elif "connection" in error_msg or "network" in error_msg:
        return ErrorType.NETWORK
    elif "rate limit" in error_msg or "too many requests" in error_msg:
        return ErrorType.RATE_LIMIT
    elif "authentication" in error_msg or "unauthorized" in error_msg:
        return ErrorType.PERMANENT
    elif "not found" in error_msg:
        return ErrorType.PERMANENT
    
    return ErrorType.UNKNOWN


class HealthMonitor:
    """Monitor health status of components.
    
    Usage:
        monitor = HealthMonitor()
        monitor.register_component("odoo")
        monitor.record_health("odoo", HealthStatus.HEALTHY)
        status = monitor.get_overall_health()
    """
    
    def __init__(self):
        self.components: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_component(
        self,
        name: str,
        check_function: Optional[Callable] = None,
        check_interval: int = 300
    ):
        """Register a component for health monitoring.
        
        Args:
            name: Component name
            check_function: Optional async function to check health
            check_interval: Seconds between automatic checks
        """
        self.components[name] = {
            "status": HealthStatus.UNKNOWN,
            "last_check": None,
            "last_error": None,
            "error_count": 0,
            "check_function": check_function,
            "check_interval": check_interval,
            "consecutive_failures": 0
        }
        self.logger.info(f"Registered health monitor component: {name}")
    
    def record_health(
        self,
        component_name: str,
        status: HealthStatus,
        error: Optional[str] = None
    ):
        """Record health status for a component.
        
        Args:
            component_name: Name of component
            status: Health status
            error: Optional error message
        """
        if component_name not in self.components:
            self.logger.warning(f"Unknown component: {component_name}")
            return
        
        component = self.components[component_name]
        component["status"] = status
        component["last_check"] = datetime.now()
        component["last_error"] = error
        
        if status == HealthStatus.UNHEALTHY:
            component["error_count"] += 1
            component["consecutive_failures"] += 1
        elif status == HealthStatus.HEALTHY:
            component["consecutive_failures"] = 0
        
        self.logger.debug(
            f"Health status for {component_name}: {status.value}"
            + (f" - {error}" if error else "")
        )
    
    def get_component_health(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get health status for a specific component."""
        if component_name not in self.components:
            return None
        
        component = self.components[component_name]
        return {
            "name": component_name,
            "status": component["status"].value,
            "last_check": component["last_check"].isoformat() if component["last_check"] else None,
            "last_error": component["last_error"],
            "error_count": component["error_count"],
            "consecutive_failures": component["consecutive_failures"]
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        if not self.components:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "components": {},
                "timestamp": datetime.now().isoformat()
            }
        
        statuses = [c["status"] for c in self.components.values()]
        
        # Determine overall status
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall = HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        else:
            overall = HealthStatus.UNKNOWN
        
        return {
            "status": overall.value,
            "components": {
                name: self.get_component_health(name)
                for name in self.components
            },
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "healthy": sum(1 for s in statuses if s == HealthStatus.HEALTHY),
                "degraded": sum(1 for s in statuses if s == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for s in statuses if s == HealthStatus.UNHEALTHY),
                "unknown": sum(1 for s in statuses if s == HealthStatus.UNKNOWN)
            }
        }
    
    def is_healthy(self) -> bool:
        """Check if overall system is healthy."""
        health = self.get_overall_health()
        return health["status"] == HealthStatus.HEALTHY.value
    
    async def check_all_components(self):
        """Run health checks on all registered components."""
        for name, component in self.components.items():
            if component["check_function"]:
                try:
                    result = await component["check_function"]()
                    if result:
                        self.record_health(name, HealthStatus.HEALTHY)
                    else:
                        self.record_health(name, HealthStatus.DEGRADED, "Check returned false")
                except Exception as e:
                    self.record_health(name, HealthStatus.UNHEALTHY, str(e))


class FallbackChain:
    """Fallback chain pattern for graceful degradation.
    
    Usage:
        fallback = FallbackChain()
        fallback.add_fallback(primary_api_call)
        fallback.add_fallback(backup_api_call)
        fallback.add_fallback(queue_for_later)
        
        result = await fallback.execute()
    """
    
    def __init__(self):
        self.fallbacks: List[Callable] = []
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def add_fallback(self, func: Callable):
        """Add a fallback function."""
        self.fallbacks.append(func)
        self.logger.info(f"Added fallback: {func.__name__}")
    
    async def execute(self, *args, **kwargs) -> Optional[Any]:
        """Execute fallback chain until one succeeds.
        
        Returns:
            Result from first successful fallback, or None if all fail
        """
        last_error = None
        
        for i, fallback in enumerate(self.fallbacks):
            try:
                self.logger.info(f"Executing fallback {i + 1}/{len(self.fallbacks)}: {fallback.__name__}")
                
                if asyncio.iscoroutinefunction(fallback):
                    result = await fallback(*args, **kwargs)
                else:
                    result = fallback(*args, **kwargs)
                
                self.logger.info(f"Fallback succeeded: {fallback.__name__}")
                return result
            
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Fallback {i + 1} failed ({fallback.__name__}): {e}"
                )
                continue
        
        self.logger.error(f"All {len(self.fallbacks)} fallbacks failed")
        if last_error:
            raise last_error
        return None


# Global health monitor instance
health_monitor = HealthMonitor()


# Convenience functions for decorator usage
def with_error_recovery(
    max_retries: int = 5,
    base_delay: float = 1.0,
    circuit_breaker: Optional[CircuitBreaker] = None,
    fallback: Optional[Callable] = None
):
    """Combined decorator for error recovery.
    
    Usage:
        @with_error_recovery(
            max_retries=5,
            base_delay=1.0,
            circuit_breaker=odoo_breaker
        )
        def odoo_call():
            return odoo.create_invoice(...)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check circuit breaker first
            if circuit_breaker and not circuit_breaker.can_execute():
                logger.warning(f"Circuit breaker open for {func.__name__}")
                if fallback:
                    return fallback(*args, **kwargs)
                raise CircuitBreakerOpenError(f"Circuit breaker open for {func.__name__}")
            
            # Execute with retry
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result
                
                except Exception as e:
                    last_exception = e
                    if circuit_breaker:
                        circuit_breaker.record_failure()
                    
                    if attempt == max_retries:
                        break
                    
                    # Calculate delay
                    delay = min(base_delay * (2 ** attempt), 60.0)
                    jitter_value = delay * 0.1 * random.random()
                    time.sleep(delay + jitter_value)
            
            # All retries failed, try fallback
            if fallback:
                try:
                    logger.info(f"Trying fallback for {func.__name__}")
                    return fallback(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator
