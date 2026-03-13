"""CEO Briefing Generator for Gold Tier AI Employee.

This module generates the "Monday Morning CEO Briefing" - a comprehensive
business audit report that transforms the AI from reactive to proactive.

The briefing includes:
- Executive Summary
- Revenue Analysis (from Odoo)
- Expense Analysis (from Odoo)
- Social Media Performance (Facebook, Instagram, Twitter)
- Task Completion Statistics
- Proactive Suggestions
- Critical Alerts

Generated every Monday at 7 AM and saved to Briefings/ folder.
"""
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import yaml

from ..integrations.odoo_integration import odoo
from ..agents.facebook_agent import facebook_agent
from ..agents.instagram_agent import instagram_agent
from ..agents.twitter_agent import twitter_agent
from .vault_manager import vault
from .audit_logger import audit_logger
from .error_recovery import health_monitor

logger = logging.getLogger(__name__)


@dataclass
class BriefingSection:
    """Represents a section in the CEO briefing."""
    title: str
    content: str
    priority: str  # "critical", "high", "normal", "low"
    metrics: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None


class CEOBriefingGenerator:
    """Generates comprehensive CEO briefings every Monday morning.

    Usage:
        generator = CEOBriefingGenerator()
        briefing = generator.generate_briefing()
        generator.save_briefing(briefing)
    """

    def __init__(self):
        """Initialize CEO Briefing Generator."""
        self.name = "CEO Briefing Generator"
        self.version = "1.0.0"
        self.vault_path = Path(vault.vault_path)
        self.briefings_dir = self.vault_path / "Briefings"
        self.briefings_dir.mkdir(parents=True, exist_ok=True)

        # Data sources
        self.odoo = odoo
        self.facebook = facebook_agent
        self.instagram = instagram_agent
        self.twitter = twitter_agent
        self.health_monitor = health_monitor
        self.audit_logger = audit_logger

        logger.info(f"CEO Briefing Generator initialized: {self.name} v{self.version}")

    def generate_briefing(
        self,
        period: str = "week",
        include_social: bool = True,
        include_suggestions: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive CEO briefing.

        Args:
            period: Time period for analysis ("week", "month", "quarter")
            include_social: Whether to include social media performance
            include_suggestions: Whether to generate proactive suggestions

        Returns:
            Briefing dictionary with all sections and metadata

        Example:
            >>> generator = CEOBriefingGenerator()
            >>> briefing = generator.generate_briefing(period="week")
            >>> generator.save_briefing(briefing)
        """
        logger.info(f"Generating CEO briefing for period: {period}")
        start_time = datetime.now()

        try:
            # Calculate date range
            end_date = datetime.now()
            if period == "week":
                start_date = end_date - timedelta(days=7)
            elif period == "month":
                start_date = end_date - timedelta(days=30)
            elif period == "quarter":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=7)

            # Generate all sections
            executive_summary = self._generate_executive_summary(period)
            revenue_analysis = self._get_revenue_analysis(start_date, end_date)
            expense_analysis = self._get_expense_analysis(start_date, end_date)
            
            social_performance = None
            if include_social:
                social_performance = self._get_social_performance(period)
            
            task_completion = self._get_task_completion_stats(start_date, end_date)
            
            proactive_suggestions = None
            if include_suggestions:
                proactive_suggestions = self._generate_suggestions(
                    revenue_analysis,
                    expense_analysis,
                    social_performance,
                    task_completion
                )

            critical_alerts = self._get_critical_alerts()

            # Compile briefing
            briefing = {
                "metadata": {
                    "type": "ceo_briefing",
                    "period": period,
                    "generated_at": datetime.now().isoformat(),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "version": self.version
                },
                "executive_summary": executive_summary,
                "revenue_analysis": revenue_analysis,
                "expense_analysis": expense_analysis,
                "social_media_performance": social_performance,
                "task_completion_stats": task_completion,
                "proactive_suggestions": proactive_suggestions,
                "critical_alerts": critical_alerts
            }

            # Log action
            self.audit_logger.log(
                action_type="briefing.generate",
                actor="CEOBriefingGenerator",
                actor_type="system",
                domain="business",
                subdomain="reporting",
                target=f"CEO Briefing {period}",
                parameters={
                    "period": period,
                    "include_social": include_social,
                    "include_suggestions": include_suggestions
                },
                result="success",
                result_data={"briefing_sections": len(briefing)},
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

            logger.info(f"CEO briefing generated successfully in {(datetime.now() - start_time).total_seconds():.2f}s")
            return briefing

        except Exception as e:
            logger.error(f"Error generating CEO briefing: {e}")
            self.audit_logger.log(
                action_type="briefing.generate",
                actor="CEOBriefingGenerator",
                actor_type="system",
                domain="business",
                subdomain="reporting",
                target=f"CEO Briefing {period}",
                parameters={"period": period},
                result="failed",
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            raise

    def _generate_executive_summary(self, period: str) -> BriefingSection:
        """Generate executive summary section."""
        logger.info("Generating executive summary")

        # Get key metrics
        try:
            # Revenue summary
            revenue_data = self._get_revenue_summary(period)
            total_revenue = revenue_data.get("total_revenue", 0)
            revenue_growth = revenue_data.get("growth_rate", 0)

            # Expense summary
            expense_data = self._get_expense_summary(period)
            total_expenses = expense_data.get("total_expenses", 0)
            expense_change = expense_data.get("change_rate", 0)

            # Profit calculation
            profit = total_revenue - total_expenses
            profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

            # Social media summary
            social_reach = self._get_social_reach_summary(period)

            # Generate summary text
            summary_text = f"""## Business Performance Overview

**Period**: Last {period}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M")}

### Key Highlights

- **Total Revenue**: ${total_revenue:,.2f} ({'+' if revenue_growth >= 0 else ''}{revenue_growth:.1f}% vs previous period)
- **Total Expenses**: ${total_expenses:,.2f} ({'+' if expense_change >= 0 else ''}{expense_change:.1f}% vs previous period)
- **Net Profit**: ${profit:,.2f} ({profit_margin:.1f}% margin)
- **Social Media Reach**: {social_reach:,} impressions

### Overall Assessment

{self._get_assessment(profit, profit_margin, revenue_growth)}
"""

            # Determine priority based on performance
            if profit < 0 or revenue_growth < -10:
                priority = "critical"
            elif profit_margin < 10 or revenue_growth < 0:
                priority = "high"
            elif profit_margin >= 20 and revenue_growth >= 10:
                priority = "low"
            else:
                priority = "normal"

            return BriefingSection(
                title="Executive Summary",
                content=summary_text,
                priority=priority,
                metrics={
                    "total_revenue": total_revenue,
                    "revenue_growth": revenue_growth,
                    "total_expenses": total_expenses,
                    "expense_change": expense_change,
                    "net_profit": profit,
                    "profit_margin": profit_margin,
                    "social_reach": social_reach
                }
            )

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return BriefingSection(
                title="Executive Summary",
                content="Unable to generate executive summary. Please check data sources.",
                priority="critical",
                metrics={},
                suggestions=["Verify Odoo connection", "Check data availability"]
            )

    def _get_revenue_analysis(self, start_date: datetime, end_date: datetime) -> BriefingSection:
        """Get detailed revenue analysis from Odoo."""
        logger.info("Getting revenue analysis")

        try:
            # Get invoices from Odoo
            invoices = self.odoo.get_invoices_by_date(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )

            # Calculate metrics
            total_revenue = sum(inv.get("amount_total", 0) for inv in invoices)
            paid_revenue = sum(inv.get("amount_total", 0) for inv in invoices if inv.get("state") == "posted")
            outstanding_revenue = total_revenue - paid_revenue

            # Top customers
            customer_revenue = {}
            for inv in invoices:
                customer = inv.get("partner_name", "Unknown")
                customer_revenue[customer] = customer_revenue.get(customer, 0) + inv.get("amount_total", 0)

            top_customers = sorted(customer_revenue.items(), key=lambda x: x[1], reverse=True)[:5]

            # Revenue by day
            daily_revenue = {}
            for inv in invoices:
                date = inv.get("date", "")[:10]
                daily_revenue[date] = daily_revenue.get(date, 0) + inv.get("amount_total", 0)

            content = f"""## Revenue Analysis

### Overview
- **Total Revenue**: ${total_revenue:,.2f}
- **Paid**: ${paid_revenue:,.2f}
- **Outstanding**: ${outstanding_revenue:,.2f}
- **Collection Rate**: {(paid_revenue/total_revenue*100) if total_revenue > 0 else 0:.1f}%

### Top Customers
{chr(10).join(f"- {customer}: ${revenue:,.2f}" for customer, revenue in top_customers)}

### Revenue Trend
Daily revenue tracked across {len(daily_revenue)} days
"""

            return BriefingSection(
                title="Revenue Analysis",
                content=content,
                priority="normal",
                metrics={
                    "total_revenue": total_revenue,
                    "paid_revenue": paid_revenue,
                    "outstanding_revenue": outstanding_revenue,
                    "collection_rate": (paid_revenue/total_revenue*100) if total_revenue > 0 else 0,
                    "top_customers": top_customers,
                    "daily_revenue": daily_revenue
                }
            )

        except Exception as e:
            logger.error(f"Error getting revenue analysis: {e}")
            return BriefingSection(
                title="Revenue Analysis",
                content="Unable to retrieve revenue data from Odoo.",
                priority="high",
                metrics={},
                suggestions=["Check Odoo connection", "Verify invoice data"]
            )

    def _get_expense_analysis(self, start_date: datetime, end_date: datetime) -> BriefingSection:
        """Get detailed expense analysis from Odoo."""
        logger.info("Getting expense analysis")

        try:
            # Get vendor bills from Odoo
            bills = self.odoo.get_vendor_bills_by_date(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )

            # Calculate metrics
            total_expenses = sum(bill.get("amount_total", 0) for bill in bills)

            # Expenses by category
            category_expenses = {}
            for bill in bills:
                category = bill.get("category", "General")
                category_expenses[category] = category_expenses.get(category, 0) + bill.get("amount_total", 0)

            # Top vendors
            vendor_expenses = {}
            for bill in bills:
                vendor = bill.get("vendor_name", "Unknown")
                vendor_expenses[vendor] = vendor_expenses.get(vendor, 0) + bill.get("amount_total", 0)

            top_vendors = sorted(vendor_expenses.items(), key=lambda x: x[1], reverse=True)[:5]

            # Identify unusual expenses (flag for review)
            unusual_expenses = []
            avg_expense = total_expenses / len(bills) if bills else 0
            for bill in bills:
                if bill.get("amount_total", 0) > avg_expense * 2:
                    unusual_expenses.append({
                        "vendor": bill.get("vendor_name"),
                        "amount": bill.get("amount_total"),
                        "category": bill.get("category"),
                        "date": bill.get("date")
                    })

            content = f"""## Expense Analysis

### Overview
- **Total Expenses**: ${total_expenses:,.2f}
- **Number of Bills**: {len(bills)}
- **Average Bill**: ${avg_expense:,.2f}

### Expenses by Category
{chr(10).join(f"- {category}: ${amount:,.2f}" for category, amount in sorted(category_expenses.items(), key=lambda x: x[1], reverse=True))}

### Top Vendors
{chr(10).join(f"- {vendor}: ${amount:,.2f}" for vendor, amount in top_vendors)}

### Unusual Expenses (Flagged for Review)
{chr(10).join(f"- {exp['vendor']}: ${exp['amount']:,.2f} ({exp['category']}, {exp['date']})" for exp in unusual_expenses) if unusual_expenses else "None detected"}
"""

            priority = "high" if unusual_expenses else "normal"
            suggestions = []
            if unusual_expenses:
                suggestions.append(f"Review {len(unusual_expenses)} unusual expenses flagged above")

            return BriefingSection(
                title="Expense Analysis",
                content=content,
                priority=priority,
                metrics={
                    "total_expenses": total_expenses,
                    "avg_expense": avg_expense,
                    "category_expenses": category_expenses,
                    "top_vendors": top_vendors,
                    "unusual_expenses": unusual_expenses
                },
                suggestions=suggestions if suggestions else None
            )

        except Exception as e:
            logger.error(f"Error getting expense analysis: {e}")
            return BriefingSection(
                title="Expense Analysis",
                content="Unable to retrieve expense data from Odoo.",
                priority="high",
                metrics={},
                suggestions=["Check Odoo connection", "Verify vendor bill data"]
            )

    def _get_social_performance(self, period: str) -> BriefingSection:
        """Get social media performance across all platforms."""
        logger.info("Getting social media performance")

        try:
            # Get Facebook metrics
            fb_metrics = self.facebook.get_unified_analytics(period=period)
            
            # Get Instagram metrics
            ig_metrics = self.instagram.get_unified_analytics(period=period)
            
            # Get Twitter metrics
            tw_metrics = self.twitter.get_unified_analytics(period=period)

            # Aggregate metrics
            total_posts = (
                fb_metrics.get("posts", 0) +
                ig_metrics.get("posts", 0) +
                tw_metrics.get("posts", 0)
            )
            total_reach = (
                fb_metrics.get("reach", 0) +
                ig_metrics.get("reach", 0) +
                tw_metrics.get("reach", 0)
            )
            total_engagement = (
                fb_metrics.get("engagement", 0) +
                ig_metrics.get("engagement", 0) +
                tw_metrics.get("engagement", 0)
            )

            content = f"""## Social Media Performance

### Overview (Last {period})
- **Total Posts**: {total_posts}
- **Total Reach**: {total_reach:,} impressions
- **Total Engagement**: {total_engagement:,} interactions
- **Engagement Rate**: {(total_engagement/total_reach*100) if total_reach > 0 else 0:.2f}%

### Platform Breakdown

#### Facebook
- Posts: {fb_metrics.get("posts", 0)}
- Reach: {fb_metrics.get("reach", 0):,}
- Engagement: {fb_metrics.get("engagement", 0):,}

#### Instagram
- Posts: {ig_metrics.get("posts", 0)}
- Reach: {ig_metrics.get("reach", 0):,}
- Engagement: {ig_metrics.get("engagement", 0):,}

#### Twitter
- Posts: {tw_metrics.get("posts", 0)}
- Reach: {tw_metrics.get("reach", 0):,}
- Engagement: {tw_metrics.get("engagement", 0):,}
"""

            return BriefingSection(
                title="Social Media Performance",
                content=content,
                priority="normal",
                metrics={
                    "facebook": fb_metrics,
                    "instagram": ig_metrics,
                    "twitter": tw_metrics,
                    "total_posts": total_posts,
                    "total_reach": total_reach,
                    "total_engagement": total_engagement
                }
            )

        except Exception as e:
            logger.error(f"Error getting social performance: {e}")
            return BriefingSection(
                title="Social Media Performance",
                content="Unable to retrieve social media metrics.",
                priority="low",
                metrics={}
            )

    def _get_task_completion_stats(self, start_date: datetime, end_date: datetime) -> BriefingSection:
        """Get task completion statistics from vault."""
        logger.info("Getting task completion statistics")

        try:
            # Count files in Done folder
            done_dir = self.vault_path / "Done"
            done_files = list(done_dir.glob("*.md")) if done_dir.exists() else []
            
            # Count files in Needs_Action folder
            action_dir = self.vault_path / "Needs_Action"
            action_files = list(action_dir.glob("*.md")) if action_dir.exists() else []

            # Count by domain
            domain_stats = {}
            for f in done_files:
                content = f.read_text()
                # Extract domain from frontmatter if present
                if "domain:" in content:
                    for line in content.split("\n")[:20]:
                        if line.startswith("domain:"):
                            domain = line.split(":")[1].strip()
                            domain_stats[domain] = domain_stats.get(domain, 0) + 1
                            break

            content = f"""## Task Completion Statistics

### Overview (Last {period})
- **Completed Tasks**: {len(done_files)}
- **Pending Tasks**: {len(action_files)}
- **Completion Rate**: {(len(done_files)/(len(done_files)+len(action_files))*100) if (len(done_files)+len(action_files)) > 0 else 0:.1f}%

### By Domain
{chr(10).join(f"- {domain}: {count} tasks" for domain, count in sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)) if domain_stats else "No domain data available"}
"""

            return BriefingSection(
                title="Task Completion Statistics",
                content=content,
                priority="normal",
                metrics={
                    "completed_tasks": len(done_files),
                    "pending_tasks": len(action_files),
                    "domain_stats": domain_stats
                }
            )

        except Exception as e:
            logger.error(f"Error getting task completion stats: {e}")
            return BriefingSection(
                title="Task Completion Statistics",
                content="Unable to retrieve task completion statistics.",
                priority="low",
                metrics={}
            )

    def _generate_suggestions(
        self,
        revenue: BriefingSection,
        expenses: BriefingSection,
        social: Optional[BriefingSection],
        tasks: BriefingSection
    ) -> BriefingSection:
        """Generate proactive suggestions based on analysis."""
        logger.info("Generating proactive suggestions")

        suggestions = []

        # Revenue-based suggestions
        if revenue.metrics:
            collection_rate = revenue.metrics.get("collection_rate", 100)
            if collection_rate < 80:
                suggestions.append(f"⚠️ **Improve Collections**: Collection rate is {collection_rate:.1f}%. Consider following up on outstanding invoices.")

            outstanding = revenue.metrics.get("outstanding_revenue", 0)
            if outstanding > 10000:
                suggestions.append(f"💰 **High Outstanding Revenue**: ${outstanding:,.2f} pending. Prioritize collection efforts.")

        # Expense-based suggestions
        if expenses.metrics:
            unusual = expenses.metrics.get("unusual_expenses", [])
            if unusual:
                suggestions.append(f"🔍 **Review Unusual Expenses**: {len(unusual)} expenses flagged for review (>{2*100:.0f}% of average).")

            category_expenses = expenses.metrics.get("category_expenses", {})
            if category_expenses:
                top_category = max(category_expenses.items(), key=lambda x: x[1])
                suggestions.append(f"📊 **Top Expense Category**: {top_category[0]} (${top_category[1]:,.2f}). Look for optimization opportunities.")

        # Social media suggestions
        if social and social.metrics:
            engagement_rate = (social.metrics.get("total_engagement", 0) / social.metrics.get("total_reach", 1) * 100) if social.metrics.get("total_reach", 0) > 0 else 0
            if engagement_rate < 1:
                suggestions.append(f"📱 **Improve Social Engagement**: Engagement rate is {engagement_rate:.2f}%. Consider more interactive content.")

        # Task completion suggestions
        if tasks.metrics:
            pending = tasks.metrics.get("pending_tasks", 0)
            if pending > 20:
                suggestions.append(f"📋 **High Pending Tasks**: {pending} tasks pending. Consider prioritizing or delegating.")

        # Default suggestions if none generated
        if not suggestions:
            suggestions.append("✅ **Business Running Smoothly**: No critical issues detected. Continue current operations.")
            suggestions.append("📈 **Growth Opportunity**: Consider expanding marketing efforts to increase revenue.")

        content = f"""## Proactive Suggestions

{chr(10).join(f"{s}" for s in suggestions)}
"""

        return BriefingSection(
            title="Proactive Suggestions",
            content=content,
            priority="normal" if not any("⚠️" in s or "💰" in s for s in suggestions) else "high",
            suggestions=suggestions
        )

    def _get_critical_alerts(self) -> BriefingSection:
        """Get critical alerts from health monitor."""
        logger.info("Getting critical alerts")

        try:
            health_status = self.health_monitor.get_system_health()
            
            alerts = []
            for component, status in health_status.items():
                if status == "unhealthy":
                    alerts.append(f"🚨 **{component}**: Unhealthy - Requires immediate attention")
                elif status == "degraded":
                    alerts.append(f"⚠️ **{component}**: Degraded - Performance may be impacted")

            if not alerts:
                alerts.append("✅ All systems operational")

            content = f"""## Critical Alerts

{chr(10).join(f"{alert}" for alert in alerts)}
"""

            priority = "critical" if any("🚨" in alert for alert in alerts) else "normal"

            return BriefingSection(
                title="Critical Alerts",
                content=content,
                priority=priority,
                metrics={"health_status": health_status}
            )

        except Exception as e:
            logger.error(f"Error getting critical alerts: {e}")
            return BriefingSection(
                title="Critical Alerts",
                content="Unable to retrieve system health status.",
                priority="high",
                metrics={}
            )

    def save_briefing(self, briefing: Dict[str, Any]) -> str:
        """Save briefing to markdown file in Briefings folder.

        Args:
            briefing: Briefing dictionary from generate_briefing()

        Returns:
            Path to saved briefing file
        """
        logger.info("Saving briefing to file")

        try:
            # Generate filename
            date_str = datetime.now().strftime("%Y-%m-%d")
            day_name = datetime.now().strftime("%A")
            filename = f"{date_str}_{day_name}_Briefing.md"
            filepath = self.briefings_dir / filename

            # Generate markdown content
            markdown = self._briefing_to_markdown(briefing)

            # Write to file
            filepath.write_text(markdown)

            logger.info(f"Briefing saved to: {filepath}")

            # Log action
            self.audit_logger.log(
                action_type="briefing.save",
                actor="CEOBriefingGenerator",
                actor_type="system",
                domain="business",
                subdomain="reporting",
                target=str(filepath),
                parameters={"filename": filename},
                result="success",
                result_data={"filepath": str(filepath)}
            )

            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving briefing: {e}")
            self.audit_logger.log(
                action_type="briefing.save",
                actor="CEOBriefingGenerator",
                actor_type="system",
                domain="business",
                subdomain="reporting",
                target="Briefing file",
                parameters={},
                result="failed",
                error_message=str(e)
            )
            raise

    def _briefing_to_markdown(self, briefing: Dict[str, Any]) -> str:
        """Convert briefing dictionary to markdown format."""
        metadata = briefing["metadata"]
        
        md = f"""---
type: ceo_briefing
period: {metadata['period']}
generated: {metadata['generated_at']}
start_date: {metadata['start_date']}
end_date: {metadata['end_date']}
version: {metadata['version']}
tags: [briefing, ceo, business, {metadata['period']}]
---

# 📊 CEO Business Briefing

**Period**: {metadata['period'].capitalize()}
**Generated**: {datetime.fromisoformat(metadata['generated_at']).strftime("%Y-%m-%d %H:%M")}
**Report Type**: Monday Morning Executive Briefing

---

## {briefing['executive_summary'].content}

---

## {briefing['revenue_analysis'].content}

---

## {briefing['expense_analysis'].content}

---

{f"## {briefing['social_media_performance'].content}" if briefing.get('social_media_performance') else ""}

---

## {briefing['task_completion_stats'].content}

---

{f"## {briefing['proactive_suggestions'].content}" if briefing.get('proactive_suggestions') else ""}

---

## {briefing['critical_alerts'].content}

---

*Generated by AI Employee CEO Briefing Generator v{metadata['version']}*
*Next briefing scheduled for next Monday at 7:00 AM*
"""
        return md

    def _get_revenue_summary(self, period: str) -> Dict[str, Any]:
        """Get revenue summary for executive summary."""
        # Implementation would query Odoo for revenue data
        # Placeholder for now
        return {"total_revenue": 0, "growth_rate": 0}

    def _get_expense_summary(self, period: str) -> Dict[str, Any]:
        """Get expense summary for executive summary."""
        # Implementation would query Odoo for expense data
        # Placeholder for now
        return {"total_expenses": 0, "change_rate": 0}

    def _get_social_reach_summary(self, period: str) -> int:
        """Get social media reach summary."""
        # Implementation would aggregate social metrics
        # Placeholder for now
        return 0

    def _get_assessment(self, profit: float, margin: float, growth: float) -> str:
        """Generate overall business assessment text."""
        if profit < 0:
            return "⚠️ **Business is operating at a loss.** Immediate attention required to reduce expenses or increase revenue."
        elif margin < 10:
            return "⚠️ **Profit margins are thin.** Consider cost optimization or pricing review."
        elif growth < 0:
            return "⚠️ **Revenue is declining.** Review sales and marketing strategies."
        elif margin >= 20 and growth >= 10:
            return "✅ **Business is performing excellently.** Strong margins and growth. Continue current strategies."
        else:
            return "✅ **Business is performing adequately.** Steady performance with room for improvement."


# Global briefing generator instance
ceo_briefing = CEOBriefingGenerator()
