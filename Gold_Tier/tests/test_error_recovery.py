"""
Tests for Error Recovery System.

Covers:
- Exponential backoff with jitter
- Circuit breaker pattern
- Health monitor
- Error classification
- Fallback chain
"""
import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_employee_gold.core.error_recovery import (
    retry_with_backoff,
    retry_with_backoff_async,
    CircuitBreaker,
    CircuitBreakerOpenError,
    HealthMonitor,
    HealthStatus,
    ErrorType,
    classify_error,
    FallbackChain
)


class TestRetryWithBackoff:
    """Test exponential backoff decorator."""
    
    def test_successful_function_no_retry(self):
        """Test that successful function doesn't retry."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = success_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure(self):
        """Test that function retries on failure."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01, jitter=False)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Simulated failure")
            return "success"
        
        result = fail_then_succeed()
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test that max retries raises exception."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            always_fail()
        
        assert call_count == 3  # Initial + 2 retries
    
    def test_exponential_backoff_timing(self):
        """Test that backoff timing is exponential."""
        timestamps = []
        
        @retry_with_backoff(max_retries=3, base_delay=0.1, jitter=False)
        def slow_fail():
            timestamps.append(time.time())
            raise ValueError("Fail")
        
        with pytest.raises(ValueError):
            slow_fail()
        
        # Check delays are exponential (approximately)
        assert len(timestamps) == 4
        delay1 = timestamps[1] - timestamps[0]
        delay2 = timestamps[2] - timestamps[1]
        delay3 = timestamps[3] - timestamps[2]
        
        assert delay1 < delay2 < delay3  # Exponential increase


class TestCircuitBreaker:
    """Test circuit breaker pattern."""
    
    def test_initial_state_closed(self):
        """Test circuit breaker starts closed."""
        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.state == CircuitBreaker.CLOSED
        assert breaker.can_execute()
    
    def test_opens_after_threshold_failures(self):
        """Test circuit opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        # Record failures
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker.state == CircuitBreaker.OPEN
        assert not breaker.can_execute()
    
    def test_half_open_after_timeout(self):
        """Test circuit goes half-open after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Open the circuit
        for _ in range(2):
            breaker.record_failure()
        
        assert breaker.state == CircuitBreaker.OPEN
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should transition to half-open
        assert breaker.can_execute()
        assert breaker.state == CircuitBreaker.HALF_OPEN
    
    def test_closes_after_successful_half_open(self):
        """Test circuit closes after successful calls in half-open."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1, half_open_max_calls=2)
        
        # Open the circuit
        for _ in range(2):
            breaker.record_failure()
        
        # Wait for recovery
        time.sleep(1.1)
        
        # Trigger half-open
        breaker.can_execute()
        
        # Record successful calls
        for _ in range(2):
            breaker.record_success()
        
        assert breaker.state == CircuitBreaker.CLOSED
    
    def test_decorator_usage(self):
        """Test circuit breaker as decorator."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        @breaker
        def failing_func():
            raise ValueError("Fail")
        
        with pytest.raises(ValueError):
            failing_func()
        
        with pytest.raises(ValueError):
            failing_func()
        
        # Should be open now
        with pytest.raises(CircuitBreakerOpenError):
            failing_func()
    
    def test_get_status(self):
        """Test status reporting."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        breaker.record_failure()
        breaker.record_success()
        
        status = breaker.get_status()
        
        assert 'state' in status
        assert 'failure_count' in status
        assert 'success_count' in status
        assert 'can_execute' in status


class TestHealthMonitor:
    """Test health monitoring system."""
    
    def test_register_component(self):
        """Test component registration."""
        monitor = HealthMonitor()
        monitor.register_component("test_component")
        
        assert "test_component" in monitor.components
        assert monitor.components["test_component"]["status"] == HealthStatus.UNKNOWN
    
    def test_record_health(self):
        """Test health status recording."""
        monitor = HealthMonitor()
        monitor.register_component("test")
        
        monitor.record_health("test", HealthStatus.HEALTHY)
        
        status = monitor.get_component_health("test")
        assert status["status"] == "healthy"
    
    def test_overall_health_aggregation(self):
        """Test overall health calculation."""
        monitor = HealthMonitor()
        monitor.register_component("healthy_comp")
        monitor.register_component("unhealthy_comp")
        
        monitor.record_health("healthy_comp", HealthStatus.HEALTHY)
        monitor.record_health("unhealthy_comp", HealthStatus.UNHEALTHY)
        
        overall = monitor.get_overall_health()
        
        assert overall["status"] == "unhealthy"
        assert overall["summary"]["healthy"] == 1
        assert overall["summary"]["unhealthy"] == 1
    
    def test_is_healthy(self):
        """Test healthy check."""
        monitor = HealthMonitor()
        monitor.register_component("test")
        
        assert not monitor.is_healthy()  # Unknown is not healthy
        
        monitor.record_health("test", HealthStatus.HEALTHY)
        assert monitor.is_healthy()


class TestErrorClassification:
    """Test error type classification."""
    
    def test_classify_timeout(self):
        """Test timeout error classification."""
        error = TimeoutError("Connection timed out")
        assert classify_error(error) == ErrorType.TIMEOUT
    
    def test_classify_network(self):
        """Test network error classification."""
        error = ConnectionError("Network unreachable")
        assert classify_error(error) == ErrorType.NETWORK
    
    def test_classify_rate_limit(self):
        """Test rate limit classification."""
        error = Exception("Too many requests")
        assert classify_error(error, status_code=429) == ErrorType.RATE_LIMIT
    
    def test_classify_permanent(self):
        """Test permanent error classification."""
        error = Exception("Authentication failed")
        assert classify_error(error) == ErrorType.PERMANENT
    
    def test_classify_unknown(self):
        """Test unknown error classification."""
        error = Exception("Random error")
        assert classify_error(error) == ErrorType.UNKNOWN


class TestFallbackChain:
    """Test fallback chain pattern."""
    
    @pytest.mark.asyncio
    async def test_fallback_success_on_first(self):
        """Test success on first fallback."""
        chain = FallbackChain()
        
        async def first():
            return "first_success"
        
        chain.add_fallback(first)
        
        result = await chain.execute()
        assert result == "first_success"
    
    @pytest.mark.asyncio
    async def test_fallback_chains_to_next(self):
        """Test fallback chains to next on failure."""
        chain = FallbackChain()
        call_order = []
        
        async def first():
            call_order.append(1)
            raise ValueError("First fails")
        
        async def second():
            call_order.append(2)
            return "second_success"
        
        chain.add_fallback(first)
        chain.add_fallback(second)
        
        result = await chain.execute()
        assert result == "second_success"
        assert call_order == [1, 2]
    
    @pytest.mark.asyncio
    async def test_all_fallbacks_fail(self):
        """Test when all fallbacks fail."""
        chain = FallbackChain()
        
        async def fail():
            raise ValueError("Always fails")
        
        chain.add_fallback(fail)
        chain.add_fallback(fail)
        
        with pytest.raises(ValueError):
            await chain.execute()


class TestAsyncRetry:
    """Test async retry functionality."""
    
    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """Test async retry with eventual success."""
        call_count = 0
        
        async def async_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Fail")
            return "success"
        
        result = await retry_with_backoff_async(
            async_func,
            max_retries=3,
            base_delay=0.01,
            jitter=False
        )
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_retry_max_exceeded(self):
        """Test async retry with max exceeded."""
        async def always_fail():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            await retry_with_backoff_async(
                always_fail,
                max_retries=2,
                base_delay=0.01
            )


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ai_employee_gold.core.error_recovery", "--cov-report=html"])
