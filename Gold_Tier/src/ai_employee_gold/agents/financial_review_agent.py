"""Financial Review Agent for Gold Tier AI Employee.

This agent performs weekly financial reviews and generates proactive suggestions:
- Weekly financial review
- Identify bottlenecks
- Generate proactive suggestions
- Subscription audit
- Unusual expense detection

Part of the CEO Briefing generation system.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..integrations.odoo_integration import odoo
from .ceo_briefing import ceo_briefing
from .vault_manager import vault
from .audit_logger import audit_logger
from ..config.settings import settings

logger = logging.getLogger(__name__)


class FinancialReviewAgent:
    """Autonomous Financial Review Agent.

    This agent specializes in financial analysis and provides:
    - Weekly financial performance reviews
    - Bottleneck identification
    - Proactive cost optimization suggestions
    - Subscription audits
    - Unusual expense detection

    All analysis is logged and may require approval for actions.
    """

    def __init__(self):
        """Initialize Financial Review Agent."""
        self.name = "FinancialReviewAgent"
        self.version = "1.0.0"
        self.domain = "finance"
        self.subdomain = "analysis"

        # Odoo integration
        self.odoo = odoo
        self.briefing_generator = ceo_briefing
        self.vault = vault
        self.audit_logger = audit_logger

        # Analysis thresholds
        self.subscription_inactivity_days = 30
        self.unusual_expense_multiplier = 2.0
        self.low_margin_threshold = 10.0
        self.high_outstanding_threshold = 10000

        # Statistics
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.start_time = datetime.now()

        logger.info(f"Financial Review Agent initialized: {self.name} v{self.version}")

    # ==================== AGENT SKILLS ====================

    def weekly_financial_review(self) -> Dict[str, Any]:
        """Agent Skill: Perform comprehensive weekly financial review.

        Returns:
            Review results with metrics and insights

        Example:
            >>> agent.weekly_financial_review()
            {
                "revenue": {...},
                "expenses": {...},
                "profit": {...},
                "bottlenecks": [...],
                "suggestions": [...]
            }
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info("Performing weekly financial review")

            # Calculate date range (last 7 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            # Get revenue data
            revenue_data = self._analyze_revenue(start_date, end_date)

            # Get expense data
            expense_data = self._analyze_expenses(start_date, end_date)

            # Calculate profit
            total_revenue = revenue_data.get("total", 0)
            total_expenses = expense_data.get("total", 0)
            profit = total_revenue - total_expenses
            profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

            # Identify bottlenecks
            bottlenecks = self._identify_bottlenecks(
                revenue_data,
                expense_data,
                profit,
                profit_margin
            )

            # Generate suggestions
            suggestions = self._generate_suggestions(
                revenue_data,
                expense_data,
                bottlenecks
            )

            result = {
                "period": "week",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "revenue": revenue_data,
                "expenses": expense_data,
                "profit": {
                    "amount": profit,
                    "margin": profit_margin,
                    "status": "profitable" if profit > 0 else "loss"
                },
                "bottlenecks": bottlenecks,
                "suggestions": suggestions,
                "generated_at": datetime.now().isoformat()
            }

            # Log success
            self.successful_actions += 1
            self.audit_logger.log(
                action_type="financial.weekly_review",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Weekly Financial Review",
                parameters={"period": "week"},
                result="success",
                result_data={"profit": profit, "margin": profit_margin},
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"Weekly financial review completed. Profit: ${profit:,.2f}, Margin: {profit_margin:.1f}%")
            return result

        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error in weekly financial review: {e}")
            self.audit_logger.log(
                action_type="financial.weekly_review",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Weekly Financial Review",
                parameters={"period": "week"},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            raise

    def identify_bottlenecks(
        self,
        revenue_data: Dict[str, Any],
        expense_data: Dict[str, Any],
        profit: float,
        profit_margin: float
    ) -> List[Dict[str, Any]]:
        """Agent Skill: Identify business bottlenecks from financial data.

        Args:
            revenue_data: Revenue analysis data
            expense_data: Expense analysis data
            profit: Net profit amount
            profit_margin: Profit margin percentage

        Returns:
            List of identified bottlenecks with severity and recommendations

        Example:
            >>> agent.identify_bottlenecks(revenue_data, expense_data, profit, margin)
            [
                {
                    "type": "collection",
                    "severity": "high",
                    "description": "Low collection rate",
                    "impact": 5000,
                    "recommendation": "Follow up on outstanding invoices"
                }
            ]
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            bottlenecks = []

            # Check collection rate
            collection_rate = revenue_data.get("collection_rate", 100)
            if collection_rate < 80:
                outstanding = revenue_data.get("outstanding", 0)
                bottlenecks.append({
                    "type": "cash_flow",
                    "severity": "high" if collection_rate < 60 else "medium",
                    "description": f"Low collection rate ({collection_rate:.1f}%)",
                    "impact": outstanding,
                    "recommendation": "Implement stricter payment terms and follow-up process",
                    "action_required": True
                })

            # Check profit margin
            if profit_margin < self.low_margin_threshold:
                bottlenecks.append({
                    "type": "profitability",
                    "severity": "high" if profit_margin < 5 else "medium",
                    "description": f"Thin profit margin ({profit_margin:.1f}%)",
                    "impact": abs(profit) if profit < 0 else 0,
                    "recommendation": "Review pricing strategy and reduce costs",
                    "action_required": True
                })

            # Check expense trends
            expense_trend = expense_data.get("trend", 0)
            revenue_trend = revenue_data.get("trend", 0)
            if expense_trend > revenue_trend and expense_trend > 10:
                bottlenecks.append({
                    "type": "cost_control",
                    "severity": "medium",
                    "description": f"Expenses growing faster than revenue (+{expense_trend:.1f}%)",
                    "impact": expense_data.get("total", 0) * (expense_trend - revenue_trend) / 100,
                    "recommendation": "Audit expenses and identify cost reduction opportunities",
                    "action_required": True
                })

            # Check for unusual expenses
            unusual_expenses = expense_data.get("unusual_expenses", [])
            if unusual_expenses:
                total_unusual = sum(exp.get("amount", 0) for exp in unusual_expenses)
                bottlenecks.append({
                    "type": "expense_anomaly",
                    "severity": "medium",
                    "description": f"{len(unusual_expenses)} unusual expenses detected",
                    "impact": total_unusual,
                    "recommendation": "Review and validate unusual expenses",
                    "action_required": True
                })

            # Check outstanding receivables
            outstanding_receivables = revenue_data.get("outstanding", 0)
            if outstanding_receivables > self.high_outstanding_threshold:
                bottlenecks.append({
                    "type": "receivables",
                    "severity": "high",
                    "description": f"High outstanding receivables (${outstanding_receivables:,.2f})",
                    "impact": outstanding_receivables,
                    "recommendation": "Prioritize collection efforts on large accounts",
                    "action_required": True
                })

            # Log success
            self.successful_actions += 1
            self.audit_logger.log(
                action_type="financial.identify_bottlenecks",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Bottleneck Analysis",
                parameters={
                    "profit": profit,
                    "margin": profit_margin
                },
                result="success",
                result_data={"bottlenecks_found": len(bottlenecks)},
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"Identified {len(bottlenecks)} bottlenecks")
            return bottlenecks

        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error identifying bottlenecks: {e}")
            self.audit_logger.log(
                action_type="financial.identify_bottlenecks",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Bottleneck Analysis",
                parameters={},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            return []

    def generate_proactive_suggestions(
        self,
        revenue_data: Dict[str, Any],
        expense_data: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Agent Skill: Generate proactive suggestions for business optimization.

        Args:
            revenue_data: Revenue analysis data
            expense_data: Expense analysis data
            bottlenecks: List of identified bottlenecks

        Returns:
            List of actionable suggestions with priority and estimated impact

        Example:
            >>> agent.generate_proactive_suggestions(revenue, expense, bottlenecks)
            [
                {
                    "category": "cost_reduction",
                    "priority": "high",
                    "suggestion": "Cancel unused subscriptions",
                    "estimated_savings": 500,
                    "effort": "low"
                }
            ]
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            suggestions = []

            # Generate suggestions based on bottlenecks
            for bottleneck in bottlenecks:
                if bottleneck["type"] == "cash_flow":
                    suggestions.append({
                        "category": "receivables",
                        "priority": "high",
                        "suggestion": "Implement automated payment reminders",
                        "estimated_impact": bottleneck.get("impact", 0) * 0.3,
                        "effort": "medium",
                        "timeframe": "1-2 weeks"
                    })
                    suggestions.append({
                        "category": "receivables",
                        "priority": "medium",
                        "suggestion": "Offer early payment discounts (2/10 net 30)",
                        "estimated_impact": bottleneck.get("impact", 0) * 0.2,
                        "effort": "low",
                        "timeframe": "immediate"
                    })

                elif bottleneck["type"] == "profitability":
                    suggestions.append({
                        "category": "pricing",
                        "priority": "high",
                        "suggestion": "Review and adjust pricing strategy",
                        "estimated_impact": revenue_data.get("total", 0) * 0.05,
                        "effort": "high",
                        "timeframe": "2-4 weeks"
                    })
                    suggestions.append({
                        "category": "cost_reduction",
                        "priority": "high",
                        "suggestion": "Audit all recurring expenses",
                        "estimated_impact": expense_data.get("total", 0) * 0.1,
                        "effort": "medium",
                        "timeframe": "1 week"
                    })

                elif bottleneck["type"] == "expense_anomaly":
                    suggestions.append({
                        "category": "expense_control",
                        "priority": "high",
                        "suggestion": "Implement expense approval workflow",
                        "estimated_impact": sum(exp.get("amount", 0) for exp in expense_data.get("unusual_expenses", [])),
                        "effort": "medium",
                        "timeframe": "1 week"
                    })

            # Subscription audit suggestions
            subscription_suggestions = self._audit_subscriptions()
            suggestions.extend(subscription_suggestions)

            # Always add growth suggestions if no critical issues
            if not bottlenecks:
                suggestions.append({
                    "category": "growth",
                    "priority": "medium",
                    "suggestion": "Business performing well. Consider expanding marketing efforts",
                    "estimated_impact": revenue_data.get("total", 0) * 0.15,
                    "effort": "medium",
                    "timeframe": "1-3 months"
                })

            # Sort by priority and estimated impact
            priority_order = {"high": 0, "medium": 1, "low": 2}
            suggestions.sort(key=lambda x: (
                priority_order.get(x["priority"], 3),
                -x.get("estimated_impact", 0)
            ))

            # Log success
            self.successful_actions += 1
            self.audit_logger.log(
                action_type="financial.generate_suggestions",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Proactive Suggestions",
                parameters={"bottlenecks_count": len(bottlenecks)},
                result="success",
                result_data={"suggestions_count": len(suggestions)},
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"Generated {len(suggestions)} proactive suggestions")
            return suggestions

        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error generating suggestions: {e}")
            self.audit_logger.log(
                action_type="financial.generate_suggestions",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Proactive Suggestions",
                parameters={},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            return []

    def audit_subscriptions(self) -> List[Dict[str, Any]]:
        """Agent Skill: Audit subscriptions for unused or redundant services.

        Returns:
            List of subscription issues and recommendations

        Example:
            >>> agent.audit_subscriptions()
            [
                {
                    "subscription": "Software License",
                    "status": "unused",
                    "monthly_cost": 99,
                    "recommendation": "Cancel - No activity in 45 days"
                }
            ]
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            logger.info("Auditing subscriptions")
            suggestions = []

            # Get recurring expenses from Odoo
            try:
                recurring_expenses = self.odoo.get_recurring_expenses()
            except Exception:
                # If Odoo not available, return empty
                logger.warning("Could not retrieve recurring expenses from Odoo")
                return []

            # Analyze each subscription
            for expense in recurring_expenses:
                vendor = expense.get("vendor_name", "Unknown")
                amount = expense.get("amount", 0)
                last_activity = expense.get("last_activity_date")

                # Check for inactivity
                if last_activity:
                    try:
                        last_date = datetime.fromisoformat(last_activity)
                        days_inactive = (datetime.now() - last_date).days

                        if days_inactive > self.subscription_inactivity_days:
                            suggestions.append({
                                "category": "subscription_optimization",
                                "priority": "high" if days_inactive > 60 else "medium",
                                "subscription": vendor,
                                "monthly_cost": amount,
                                "days_inactive": days_inactive,
                                "suggestion": f"Cancel subscription - No activity in {days_inactive} days",
                                "estimated_savings": amount * 12,  # Annual savings
                                "effort": "low",
                                "timeframe": "immediate"
                            })
                    except Exception:
                        pass

            # Add summary suggestion if issues found
            if suggestions:
                total_savings = sum(s.get("estimated_savings", 0) for s in suggestions)
                suggestions.append({
                    "category": "subscription_summary",
                    "priority": "high",
                    "suggestion": f"Review {len(suggestions)} unused subscriptions",
                    "estimated_savings": total_savings,
                    "effort": "low",
                    "timeframe": "this week"
                })

            # Log success
            self.successful_actions += 1
            self.audit_logger.log(
                action_type="financial.audit_subscriptions",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Subscription Audit",
                parameters={},
                result="success",
                result_data={
                    "subscriptions_reviewed": len(recurring_expenses),
                    "issues_found": len(suggestions)
                },
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"Subscription audit complete. Found {len(suggestions)} optimization opportunities")
            return suggestions

        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error auditing subscriptions: {e}")
            self.audit_logger.log(
                action_type="financial.audit_subscriptions",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Subscription Audit",
                parameters={},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            return []

    def detect_unusual_expenses(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Agent Skill: Detect unusual expenses based on historical patterns.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            List of unusual expenses with anomaly score and reason

        Example:
            >>> agent.detect_unusual_expenses()
            [
                {
                    "vendor": "ABC Corp",
                    "amount": 5000,
                    "category": "Software",
                    "anomaly_score": 0.95,
                    "reason": "3x higher than average for category"
                }
            ]
        """
        self.total_actions += 1
        start_time = datetime.now()

        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=90)  # Last 90 days
            if not end_date:
                end_date = datetime.now()

            logger.info("Detecting unusual expenses")

            # Get expenses from Odoo
            try:
                expenses = self.odoo.get_expenses_by_date(
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )
            except Exception:
                logger.warning("Could not retrieve expenses from Odoo")
                return []

            # Calculate average by category
            category_stats = {}
            for expense in expenses:
                category = expense.get("category", "General")
                amount = expense.get("amount", 0)
                if category not in category_stats:
                    category_stats[category] = {"total": 0, "count": 0, "amounts": []}
                category_stats[category]["total"] += amount
                category_stats[category]["count"] += 1
                category_stats[category]["amounts"].append(amount)

            # Calculate averages and std devs
            for category, stats in category_stats.items():
                if stats["count"] > 0:
                    stats["average"] = stats["total"] / stats["count"]
                    # Simple std dev approximation
                    mean = stats["average"]
                    variance = sum((x - mean) ** 2 for x in stats["amounts"]) / stats["count"]
                    stats["std_dev"] = variance ** 0.5
                else:
                    stats["average"] = 0
                    stats["std_dev"] = 0

            # Identify unusual expenses
            unusual_expenses = []
            for expense in expenses:
                category = expense.get("category", "General")
                amount = expense.get("amount", 0)
                vendor = expense.get("vendor_name", "Unknown")

                if category in category_stats:
                    avg = category_stats[category]["average"]
                    std_dev = category_stats[category]["std_dev"]

                    # Flag if > 2 standard deviations above mean or > 2x average
                    threshold = max(avg * 2, avg + 2 * std_dev) if std_dev > 0 else avg * 2

                    if amount > threshold and amount > 100:  # Minimum $100 threshold
                        anomaly_score = (amount - avg) / std_dev if std_dev > 0 else amount / avg
                        unusual_expenses.append({
                            "vendor": vendor,
                            "amount": amount,
                            "category": category,
                            "date": expense.get("date"),
                            "anomaly_score": min(anomaly_score, 1.0),  # Cap at 1.0
                            "reason": f"{amount/avg:.1f}x higher than category average (${avg:.2f})",
                            "threshold": threshold
                        })

            # Sort by anomaly score
            unusual_expenses.sort(key=lambda x: x["anomaly_score"], reverse=True)

            # Log success
            self.successful_actions += 1
            self.audit_logger.log(
                action_type="financial.detect_unusual_expenses",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Unusual Expense Detection",
                parameters={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                result="success",
                result_data={"unusual_expenses_found": len(unusual_expenses)},
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"Detected {len(unusual_expenses)} unusual expenses")
            return unusual_expenses

        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error detecting unusual expenses: {e}")
            self.audit_logger.log(
                action_type="financial.detect_unusual_expenses",
                actor=self.name,
                actor_type="agent",
                domain=self.domain,
                subdomain=self.subdomain,
                target="Unusual Expense Detection",
                parameters={},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            return []

    # ==================== HELPER METHODS ====================

    def _analyze_revenue(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze revenue for period."""
        try:
            invoices = self.odoo.get_invoices_by_date(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )

            total = sum(inv.get("amount_total", 0) for inv in invoices)
            paid = sum(inv.get("amount_total", 0) for inv in invoices if inv.get("state") == "posted")
            outstanding = total - paid

            return {
                "total": total,
                "paid": paid,
                "outstanding": outstanding,
                "collection_rate": (paid / total * 100) if total > 0 else 100,
                "invoice_count": len(invoices),
                "trend": 0  # Would calculate from previous period
            }
        except Exception as e:
            logger.error(f"Error analyzing revenue: {e}")
            return {"total": 0, "paid": 0, "outstanding": 0, "collection_rate": 0}

    def _analyze_expenses(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze expenses for period."""
        try:
            bills = self.odoo.get_vendor_bills_by_date(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )

            total = sum(bill.get("amount_total", 0) for bill in bills)
            avg = total / len(bills) if bills else 0

            # Find unusual expenses
            unusual = []
            for bill in bills:
                if bill.get("amount_total", 0) > avg * self.unusual_expense_multiplier:
                    unusual.append({
                        "vendor": bill.get("vendor_name"),
                        "amount": bill.get("amount_total"),
                        "category": bill.get("category")
                    })

            return {
                "total": total,
                "count": len(bills),
                "average": avg,
                "unusual_expenses": unusual,
                "trend": 0  # Would calculate from previous period
            }
        except Exception as e:
            logger.error(f"Error analyzing expenses: {e}")
            return {"total": 0, "count": 0, "average": 0, "unusual_expenses": []}


# Global financial review agent instance
financial_review_agent = FinancialReviewAgent()
