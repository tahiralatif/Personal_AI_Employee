"""Base watcher class for Gold Tier AI Employee system.

Enhanced with:
- Error recovery with exponential backoff
- Circuit breaker pattern
- Health status reporting
- Correlation IDs
- Audit logging
"""
import time
import logging
import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from .vault import vault
from .error_recovery import (
    retry_with_backoff,
    CircuitBreaker,
    HealthMonitor,
    HealthStatus,
    classify_error,
    ErrorType,
    health_monitor
)
from .audit_logger import audit_logger


class BaseWatcher(ABC):
    """Base class for all watchers in the AI Employee system.
    
    Features:
    - Exponential backoff with jitter for retries
    - Circuit breaker pattern for fault tolerance
    - Health status monitoring
    - Correlation ID tracking
    - Comprehensive audit logging
    """

    def __init__(
        self,
        check_interval: int = 60,
        enabled: bool = True,
        max_retries: int = 5,
        base_delay: float = 1.0,
        circuit_breaker_threshold: int = 5,
        domain: str = "business",
        subdomain: Optional[str] = None
    ):
        """Initialize base watcher.
        
        Args:
            check_interval: Seconds between checks
            enabled: Whether watcher is enabled
            max_retries: Maximum retry attempts
            base_delay: Base delay for exponential backoff
            circuit_breaker_threshold: Failures before circuit opens
            domain: Domain (business, personal, system)
            subdomain: Subdomain (accounting, social, etc.)
        """
        self.check_interval = check_interval
        self.enabled = enabled
        self.last_check: Optional[datetime] = None
        self.processed_ids: set = set()
        self.domain = domain
        self.subdomain = subdomain
        
        # Error recovery
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=300  # 5 minutes
        )
        
        # Health monitoring
        self.health_status = HealthStatus.HEALTHY
        self.consecutive_failures = 0
        self.total_processed = 0
        self.total_errors = 0
        self.start_time = datetime.now()
        
        # Correlation tracking
        self.correlation_id = self._generate_correlation_id()
        
        # Logger
        self.logger = self._setup_logger()
        
        # Register with health monitor
        health_monitor.register_component(
            self.__class__.__name__.lower(),
            check_interval=check_interval * 2
        )
        
        self.logger.info(
            f"Watcher initialized: {self.__class__.__name__}, "
            f"domain={domain}, check_interval={check_interval}s"
        )

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"corr_{timestamp}_{os.getpid()}_{self.__class__.__name__.lower()}"

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the watcher."""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)

        # Create formatter with correlation ID
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
            defaults={'correlation_id': self.correlation_id[:8]}
        )

        # Create file handler
        log_dir = Path(vault.paths.logs)
        log_file = log_dir / f"{self.__class__.__name__.lower()}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Return list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """Create .md file in Needs_Action folder."""
        pass

    @retry_with_backoff(max_retries=5, base_delay=1.0, jitter=True)
    def _execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic."""
        return func(*args, **kwargs)

    def _record_success(self, item_id: str, execution_time_ms: int):
        """Record successful processing."""
        self.circuit_breaker.record_success()
        self.total_processed += 1
        self.consecutive_failures = 0
        self.health_status = HealthStatus.HEALTHY
        
        # Update health monitor
        health_monitor.record_health(
            self.__class__.__name__.lower(),
            HealthStatus.HEALTHY
        )
        
        # Audit log
        audit_logger.log(
            action_type=f"{self.__class__.__name__.lower()}.process_item",
            actor=self.__class__.__name__,
            actor_type="agent",
            domain=self.domain,
            subdomain=self.subdomain,
            target=f"Item {item_id}",
            parameters={"item_id": item_id},
            result="success",
            execution_time_ms=execution_time_ms,
            correlation_id=self.correlation_id
        )
        
        self.logger.debug(f"Successfully processed item: {item_id}")

    def _record_failure(self, item_id: str, error: Exception, execution_time_ms: int):
        """Record failed processing."""
        self.circuit_breaker.record_failure()
        self.total_errors += 1
        self.consecutive_failures += 1
        
        # Update health status based on consecutive failures
        if self.consecutive_failures >= 5:
            self.health_status = HealthStatus.UNHEALTHY
        elif self.consecutive_failures >= 2:
            self.health_status = HealthStatus.DEGRADED
        
        # Classify error
        error_type = classify_error(error)
        
        # Update health monitor
        health_monitor.record_health(
            self.__class__.__name__.lower(),
            self.health_status,
            str(error)
        )
        
        # Audit log
        audit_logger.log(
            action_type=f"{self.__class__.__name__.lower()}.process_item",
            actor=self.__class__.__name__,
            actor_type="agent",
            domain=self.domain,
            subdomain=self.subdomain,
            target=f"Item {item_id}",
            parameters={"item_id": item_id},
            result="failed",
            error_message=str(error),
            error_code=error_type.value,
            execution_time_ms=execution_time_ms,
            correlation_id=self.correlation_id
        )
        
        self.logger.error(f"Failed to process item {item_id}: {error} (Type: {error_type.value})")

    def run(self):
        """Run the watcher in continuous loop."""
        if not self.enabled:
            self.logger.info(f"{self.__class__.__name__} is disabled, skipping...")
            return

        self.logger.info(f'Starting {self.__class__.__name__}')
        
        while True:
            try:
                # Check circuit breaker
                if not self.circuit_breaker.can_execute():
                    self.logger.warning(
                        f"Circuit breaker open, skipping check. "
                        f"Status: {self.circuit_breaker.state.value}"
                    )
                    self.health_status = HealthStatus.DEGRADED
                    time.sleep(self.check_interval)
                    continue

                if self.enabled:
                    start_time = time.time()
                    
                    try:
                        items = self.check_for_updates()
                        
                        for item in items:
                            if item['id'] not in self.processed_ids:
                                item_start = time.time()
                                
                                try:
                                    self.create_action_file(item)
                                    self.processed_ids.add(item['id'])
                                    
                                    execution_time = int((time.time() - item_start) * 1000)
                                    self._record_success(item['id'], execution_time)
                                    self.logger.info(f"Processed item: {item['id']}")
                                    
                                except Exception as e:
                                    execution_time = int((time.time() - item_start) * 1000)
                                    self._record_failure(item['id'], e, execution_time)
                                    
                    except Exception as e:
                        self.logger.error(f"Error in check_for_updates: {e}")
                        self._record_failure("check", e, 0)

                self.last_check = datetime.now()
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info(f"{self.__class__.__name__} received shutdown signal")
                break
            except Exception as e:
                self.logger.error(f'Unexpected error in {self.__class__.__name__}: {e}')
                time.sleep(5)  # Backoff on error

    def get_health_status(self) -> Dict[str, Any]:
        """Get watcher health status.
        
        Returns:
            Health status dictionary
        """
        uptime = datetime.now() - self.start_time
        
        return {
            "name": self.__class__.__name__,
            "status": self.health_status.value,
            "enabled": self.enabled,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "uptime_seconds": int(uptime.total_seconds()),
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "circuit_breaker": self.circuit_breaker.get_status(),
            "statistics": {
                "total_processed": self.total_processed,
                "total_errors": self.total_errors,
                "consecutive_failures": self.consecutive_failures,
                "error_rate": self.total_errors / max(1, self.total_processed + self.total_errors),
                "processed_ids_count": len(self.processed_ids)
            },
            "correlation_id": self.correlation_id,
            "check_interval": self.check_interval,
            "start_time": self.start_time.isoformat()
        }

    def reset_correlation_id(self):
        """Generate new correlation ID (e.g., after restart)."""
        old_id = self.correlation_id
        self.correlation_id = self._generate_correlation_id()
        self.logger.info(
            f"Correlation ID reset: {old_id[:8]}... → {self.correlation_id[:8]}..."
        )

    def stop(self):
        """Stop the watcher gracefully."""
        self.logger.info(f"Stopping {self.__class__.__name__}")
        self.enabled = False
        health_monitor.record_health(
            self.__class__.__name__.lower(),
            HealthStatus.UNKNOWN,
            "Watcher stopped"
        )