"""Autonomous Run System for Gold Tier AI Employee.

This module launches all agents in parallel for 24/7 autonomous operation:
- Odoo Agent (accounting)
- Facebook Agent (social media)
- Instagram Agent (social media)
- Twitter Agent (social media)
- Financial Review Agent (weekly audit)
- Audit Agent (compliance)
- Security Agent (security monitoring)

All agents run autonomously with health monitoring and error recovery.
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from ..config.settings import settings
from ..core.error_recovery import health_monitor, CircuitBreaker
from ..core.audit_logger import audit_logger
from ..agents.odoo_agent import odoo_agent
from ..agents.facebook_agent import facebook_agent
from ..agents.instagram_agent import instagram_agent
from ..agents.twitter_agent import twitter_agent
from ..agents.financial_review_agent import financial_review_agent
from ..agents.audit_agent import audit_agent
from ..agents.security_agent import security_agent

logger = logging.getLogger(__name__)


class GoldTierAutonomousSystem:
    """Autonomous system that runs all Gold Tier agents."""

    def __init__(self):
        """Initialize autonomous system."""
        self.name = "GoldTierAutonomousSystem"
        self.version = "1.0.0"
        
        # Register all agents
        self.agents = {
            "odoo": odoo_agent,
            "facebook": facebook_agent,
            "instagram": instagram_agent,
            "twitter": twitter_agent,
            "financial_review": financial_review_agent,
            "audit": audit_agent,
            "security": security_agent
        }
        
        # Agent configuration
        self.agent_config = {
            "odoo": {"check_interval": 300},  # 5 minutes
            "facebook": {"check_interval": 300},  # 5 minutes
            "instagram": {"check_interval": 300},  # 5 minutes
            "twitter": {"check_interval": 180},  # 3 minutes
            "financial_review": {"check_interval": 3600},  # 1 hour
            "audit": {"check_interval": 600},  # 10 minutes
            "security": {"check_interval": 300}  # 5 minutes
        }
        
        # Running state
        self.running = False
        self.tasks: Dict[str, asyncio.Task] = {}
        
        # Statistics
        self.start_time = None
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        
        logger.info(f"{self.name} v{self.version} initialized")

    async def run_agent(self, agent_name: str, agent: Any, check_interval: int):
        """Run a single agent autonomously.
        
        Args:
            agent_name: Name of the agent
            agent: Agent instance
            check_interval: Seconds between checks
        """
        logger.info(f"Starting {agent_name} agent (interval: {check_interval}s)")
        
        while self.running:
            try:
                # Register component with health monitor
                health_monitor.register_component(f"agent.{agent_name}")
                
                # Run agent check
                start_time = datetime.now()
                
                # Call agent's autonomous method (if exists)
                if hasattr(agent, 'autonomous_check'):
                    result = await agent.autonomous_check()
                    self.total_actions += 1
                    
                    if result.get("success", False):
                        self.successful_actions += 1
                        health_monitor.record_health(f"agent.{agent_name}", "healthy")
                    else:
                        self.failed_actions += 1
                        health_monitor.record_health(f"agent.{agent_name}", "degraded")
                else:
                    # Agent doesn't have autonomous_check, just mark as healthy
                    health_monitor.record_health(f"agent.{agent_name}", "healthy")
                
                # Log execution time
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                logger.debug(f"{agent_name} check completed in {execution_time:.0f}ms")
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                logger.info(f"{agent_name} agent cancelled")
                break
            except Exception as e:
                self.failed_actions += 1
                logger.error(f"Error in {agent_name} agent: {e}")
                health_monitor.record_health(f"agent.{agent_name}", "unhealthy")
                
                # Wait before retry
                await asyncio.sleep(60)

    async def run_health_monitor(self, check_interval: int = 60):
        """Run health monitoring system.
        
        Args:
            check_interval: Seconds between health checks
        """
        logger.info("Starting health monitor")
        
        while self.running:
            try:
                # Get overall health status
                health_status = health_monitor.get_system_health()
                
                # Log health status
                unhealthy = [k for k, v in health_status.items() if v == "unhealthy"]
                degraded = [k for k, v in health_status.items() if v == "degraded"]
                
                if unhealthy:
                    logger.warning(f"Unhealthy components: {', '.join(unhealthy)}")
                elif degraded:
                    logger.info(f"Degraded components: {', '.join(degraded)}")
                else:
                    logger.debug("All components healthy")
                
                # Log system statistics
                if self.start_time:
                    uptime = (datetime.now() - self.start_time).total_seconds()
                    logger.debug(
                        f"System stats - Uptime: {uptime:.0f}s, "
                        f"Actions: {self.total_actions}, "
                        f"Success: {self.successful_actions}, "
                        f"Failed: {self.failed_actions}"
                    )
                
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                logger.info("Health monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)

    async def run_audit_logger(self, flush_interval: int = 300):
        """Run audit logger flush system.
        
        Args:
            flush_interval: Seconds between flushes
        """
        logger.info("Starting audit logger flush")
        
        while self.running:
            try:
                # Flush audit log buffer
                audit_logger.flush_buffer()
                logger.debug("Audit log buffer flushed")
                
                await asyncio.sleep(flush_interval)
                
            except asyncio.CancelledError:
                logger.info("Audit logger flush cancelled")
                break
            except Exception as e:
                logger.error(f"Error flushing audit log: {e}")
                await asyncio.sleep(60)

    async def start(self):
        """Start the autonomous system."""
        logger.info("="*60)
        logger.info("Starting Gold Tier Autonomous System")
        logger.info("="*60)
        
        self.running = True
        self.start_time = datetime.now()
        
        # Create tasks for all agents
        tasks = []
        
        # Start all agents
        for agent_name, agent in self.agents.items():
            interval = self.agent_config.get(agent_name, {}).get("check_interval", 300)
            task = asyncio.create_task(
                self.run_agent(agent_name, agent, interval),
                name=f"agent.{agent_name}"
            )
            self.tasks[agent_name] = task
            tasks.append(task)
        
        # Start health monitor
        health_task = asyncio.create_task(
            self.run_health_monitor(60),
            name="health_monitor"
        )
        tasks.append(health_task)
        
        # Start audit logger flush
        audit_task = asyncio.create_task(
            self.run_audit_logger(300),
            name="audit_logger"
        )
        tasks.append(audit_task)
        
        logger.info(f"Started {len(tasks)} tasks")
        logger.info("="*60)
        
        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("System cancelled")
        
        logger.info("Autonomous system stopped")

    def stop(self):
        """Stop the autonomous system."""
        logger.info("Stopping Gold Tier Autonomous System...")
        
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks.values():
            task.cancel()
        
        logger.info("System stop initiated")


# Global autonomous system instance
autonomous_system = GoldTierAutonomousSystem()


async def main():
    """Main entry point."""
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        autonomous_system.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start system
    try:
        await autonomous_system.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        autonomous_system.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Gold Tier Autonomous System starting...")
    asyncio.run(main())
