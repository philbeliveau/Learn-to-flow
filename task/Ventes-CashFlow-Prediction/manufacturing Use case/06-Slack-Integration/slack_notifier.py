"""
Slack Integration for Manufacturing Data Simulator
Sends daily summaries, alerts, and notifications to Slack channels
"""

import os
import asyncio
import httpx
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class SlackConfig:
    """Slack integration configuration"""
    webhook_url: str
    channel: str = "#manufacturing-data"
    username: str = "Manufacturing Simulator"
    icon_emoji: str = ":factory:"
    timeout: int = 10

class SlackNotifier:
    """Handles Slack notifications for the manufacturing simulator"""
    
    def __init__(self, webhook_url: str, config: Optional[SlackConfig] = None):
        self.webhook_url = webhook_url
        self.config = config or SlackConfig(webhook_url=webhook_url)
        
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def send_daily_summary(self, simulation_report: Dict[str, Any], excel_file_path: Optional[str] = None) -> bool:
        """Send daily simulation summary to Slack"""
        try:
            # Create rich summary message
            message = self._build_daily_summary_message(simulation_report, excel_file_path)
            
            response = await self._send_message(message)
            
            if response.status_code == 200:
                logger.info("Daily summary sent to Slack successfully")
                return True
            else:
                logger.error(f"Failed to send daily summary: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending daily summary to Slack: {e}")
            return False
    
    async def send_error_notification(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Send error notification to Slack"""
        try:
            message = {
                "channel": self.config.channel,
                "username": self.config.username,
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": "danger",
                        "title": "🚨 Manufacturing Simulator Error",
                        "text": f"```{error_message}```",
                        "fields": [
                            {
                                "title": "Timestamp",
                                "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": True
                            },
                            {
                                "title": "Environment",
                                "value": os.getenv("ENVIRONMENT", "production"),
                                "short": True
                            }
                        ],
                        "footer": "Manufacturing Data Simulator",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            if context:
                message["attachments"][0]["fields"].extend([
                    {
                        "title": "Context",
                        "value": f"```{json.dumps(context, indent=2)}```",
                        "short": False
                    }
                ])
            
            response = await self._send_message(message)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending error notification to Slack: {e}")
            return False
    
    async def send_startup_notification(self) -> bool:
        """Send notification when simulator starts up"""
        try:
            message = {
                "channel": self.config.channel,
                "username": self.config.username,
                "icon_emoji": ":rocket:",
                "text": "🚀 *Manufacturing Data Simulator Started*",
                "attachments": [
                    {
                        "color": "good",
                        "fields": [
                            {
                                "title": "Environment",
                                "value": os.getenv("ENVIRONMENT", "production"),
                                "short": True
                            },
                            {
                                "title": "Schedule",
                                "value": os.getenv("SIMULATION_SCHEDULE", "Daily at 6 AM UTC"),
                                "short": True
                            },
                            {
                                "title": "Database",
                                "value": "Connected ✅",
                                "short": True
                            },
                            {
                                "title": "Status",
                                "value": "Ready for simulation",
                                "short": True
                            }
                        ],
                        "footer": "Manufacturing Data Simulator",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            response = await self._send_message(message)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending startup notification to Slack: {e}")
            return False
    
    async def send_weekly_report(self, weekly_data: Dict[str, Any]) -> bool:
        """Send weekly performance report"""
        try:
            message = self._build_weekly_report_message(weekly_data)
            
            response = await self._send_message(message)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending weekly report to Slack: {e}")
            return False
    
    async def send_cash_flow_alert(self, alert_type: str, current_balance: float, threshold: float) -> bool:
        """Send cash flow alerts"""
        try:
            color = "warning" if alert_type == "low" else "danger"
            emoji = "⚠️" if alert_type == "low" else "🚨"
            
            message = {
                "channel": self.config.channel,
                "username": self.config.username,
                "icon_emoji": ":money_with_wings:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"{emoji} Cash Flow Alert - {alert_type.title()}",
                        "fields": [
                            {
                                "title": "Current Balance",
                                "value": f"${current_balance:,.2f}",
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"${threshold:,.2f}",
                                "short": True
                            },
                            {
                                "title": "Action Required",
                                "value": "Review cash flow projections and consider financing options" if alert_type == "low" else "URGENT: Immediate action required to avoid cash shortfall",
                                "short": False
                            }
                        ],
                        "footer": "Manufacturing Data Simulator",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            response = await self._send_message(message)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending cash flow alert to Slack: {e}")
            return False
    
    def _build_daily_summary_message(self, report: Dict[str, Any], excel_file: Optional[str] = None) -> Dict[str, Any]:
        """Build comprehensive daily summary message"""
        date = report.get('simulation_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Calculate totals and metrics
        total_transactions = report.get('total_transactions', 0)
        cash_balance = report.get('ending_cash_balance', 0)
        
        # Build main message
        message = {
            "channel": self.config.channel,
            "username": self.config.username,
            "icon_emoji": self.config.icon_emoji,
            "text": f"📊 *Daily Manufacturing Report - {date}*",
            "attachments": [
                {
                    "color": "good",
                    "title": "📈 Business Activity Summary",
                    "fields": [
                        {
                            "title": "💰 Invoices Created",
                            "value": f"{report.get('invoices_created', 0)} invoices",
                            "short": True
                        },
                        {
                            "title": "🏭 Production Orders",
                            "value": f"{report.get('production_orders_created', 0)} orders started",
                            "short": True
                        },
                        {
                            "title": "🛒 Purchases Made",
                            "value": f"{report.get('purchases_created', 0)} purchases",
                            "short": True
                        },
                        {
                            "title": "💸 Payments Received",
                            "value": f"{report.get('payments_received', 0)} payments",
                            "short": True
                        },
                        {
                            "title": "💳 Vendor Payments",
                            "value": f"{report.get('vendor_payments_made', 0)} payments made",
                            "short": True
                        },
                        {
                            "title": "💼 Total Transactions",
                            "value": f"{total_transactions} transactions",
                            "short": True
                        }
                    ]
                },
                {
                    "color": "#36a64f" if cash_balance > 50000 else "#ff9900" if cash_balance > 10000 else "#ff0000",
                    "title": "💰 Financial Position",
                    "fields": [
                        {
                            "title": "Cash Balance",
                            "value": f"${cash_balance:,.2f}",
                            "short": True
                        },
                        {
                            "title": "Status",
                            "value": self._get_cash_status(cash_balance),
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        # Add payroll information if processed
        if report.get('payroll_processed', False):
            message["attachments"][0]["fields"].append({
                "title": "👥 Payroll",
                "value": "✅ Bi-weekly payroll processed",
                "short": True
            })
        
        # Add Excel file information
        if excel_file:
            message["attachments"].append({
                "color": "#0066cc",
                "title": "📄 Excel Export",
                "text": f"Daily data exported to: `{os.path.basename(excel_file)}`",
                "footer": "Available in Railway exports volume"
            })
        
        # Add footer with timestamp
        message["attachments"][-1]["footer"] = "Manufacturing Data Simulator"
        message["attachments"][-1]["ts"] = int(datetime.utcnow().timestamp())
        
        return message
    
    def _build_weekly_report_message(self, weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build weekly performance report"""
        return {
            "channel": self.config.channel,
            "username": self.config.username,
            "icon_emoji": ":chart_with_upwards_trend:",
            "text": "📊 *Weekly Manufacturing Performance Report*",
            "attachments": [
                {
                    "color": "good",
                    "title": "📈 Weekly Metrics",
                    "fields": [
                        {
                            "title": "Total Revenue",
                            "value": f"${weekly_data.get('total_revenue', 0):,.2f}",
                            "short": True
                        },
                        {
                            "title": "Total Expenses",
                            "value": f"${weekly_data.get('total_expenses', 0):,.2f}",
                            "short": True
                        },
                        {
                            "title": "Net Cash Flow",
                            "value": f"${weekly_data.get('net_cash_flow', 0):,.2f}",
                            "short": True
                        },
                        {
                            "title": "Orders Completed",
                            "value": f"{weekly_data.get('completed_orders', 0)} orders",
                            "short": True
                        },
                        {
                            "title": "Collection Rate",
                            "value": f"{weekly_data.get('collection_rate', 0):.1f}%",
                            "short": True
                        },
                        {
                            "title": "Production Efficiency",
                            "value": f"{weekly_data.get('production_efficiency', 0):.1f}%",
                            "short": True
                        }
                    ],
                    "footer": "Manufacturing Data Simulator",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }
    
    def _get_cash_status(self, balance: float) -> str:
        """Get cash status emoji and text"""
        if balance > 100000:
            return "🟢 Excellent"
        elif balance > 50000:
            return "🟡 Good"
        elif balance > 10000:
            return "🟠 Caution"
        else:
            return "🔴 Critical"
    
    async def _send_message(self, message: Dict[str, Any]) -> httpx.Response:
        """Send message to Slack webhook"""
        try:
            response = await self.client.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"}
            )
            return response
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            raise

# Utility functions for easy integration

async def send_quick_notification(message: str, webhook_url: str, level: str = "info") -> bool:
    """Send a quick notification to Slack"""
    colors = {
        "info": "good",
        "warning": "warning", 
        "error": "danger",
        "success": "good"
    }
    
    emojis = {
        "info": ":information_source:",
        "warning": ":warning:",
        "error": ":x:",
        "success": ":white_check_mark:"
    }
    
    payload = {
        "text": f"{emojis.get(level, ':factory:')} {message}",
        "attachments": [
            {
                "color": colors.get(level, "good"),
                "footer": "Manufacturing Data Simulator",
                "ts": int(datetime.utcnow().timestamp())
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send quick notification: {e}")
        return False

def create_slack_notifier() -> SlackNotifier:
    """Create Slack notifier from environment variables"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not configured. Slack notifications will be disabled.")
        return None
    
    config = SlackConfig(
        webhook_url=webhook_url,
        channel=os.getenv("SLACK_CHANNEL", "#manufacturing-data"),
        username=os.getenv("SLACK_USERNAME", "Manufacturing Simulator"),
        icon_emoji=os.getenv("SLACK_ICON", ":factory:")
    )
    
    return SlackNotifier(webhook_url, config)