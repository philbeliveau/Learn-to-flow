"""
Slack notification service for EZBI Analytics alerts
Production-grade notification system for cash flow monitoring
"""
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class SlackNotifier:
    """Slack notification service for manufacturing business alerts"""
    
    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.channel = os.getenv('SLACK_CHANNEL', '#finance')
        self.bot_name = os.getenv('SLACK_BOT_NAME', 'EZBI Analytics')
        
        if not self.webhook_url:
            print("⚠️ SLACK_WEBHOOK_URL not configured, notifications disabled")
    
    async def send_cash_flow_alert(self, alert: Dict[str, Any]) -> bool:
        """Send cash flow alert to Slack channel"""
        
        if not self.webhook_url:
            print(f"📢 Alert (Slack disabled): {alert['message']}")
            return False
        
        color_map = {
            'critical': '#FF0000',  # Red
            'warning': '#FFA500',   # Orange  
            'info': '#36a64f'       # Green
        }
        
        # Create severity emoji
        emoji_map = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        severity = alert.get('severity', 'info')
        emoji = emoji_map.get(severity, 'ℹ️')
        
        message = {
            "channel": self.channel,
            "username": self.bot_name,
            "icon_emoji": ":chart_with_upwards_trend:",
            "attachments": [{
                "color": color_map.get(severity, '#808080'),
                "title": f"{emoji} EZBI Analytics - Alerte Cash Flow",
                "text": alert['message'],
                "fields": [
                    {
                        "title": "Type d'alerte",
                        "value": alert['type'].replace('_', ' ').title(),
                        "short": True
                    },
                    {
                        "title": "Sévérité",
                        "value": severity.upper(),
                        "short": True
                    },
                    {
                        "title": "Timestamp",
                        "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "short": True
                    }
                ],
                "footer": "EZBI Manufacturing Intelligence",
                "footer_icon": "https://ezbi.fr/favicon.ico",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        # Add specific fields based on alert type
        if 'current_balance' in alert:
            message['attachments'][0]['fields'].append({
                "title": "Solde Actuel",
                "value": f"€{alert['current_balance']:,.2f}",
                "short": True
            })
        
        if 'daily_trend' in alert:
            trend_emoji = "📈" if alert['daily_trend'] > 0 else "📉"
            message['attachments'][0]['fields'].append({
                "title": f"{trend_emoji} Tendance Quotidienne",
                "value": f"€{alert['daily_trend']:,.2f}/jour",
                "short": True
            })
        
        if 'overdue_amount' in alert:
            message['attachments'][0]['fields'].append({
                "title": "Créances en Retard",
                "value": f"€{alert['overdue_amount']:,.2f}",
                "short": True
            })
        
        # Add action buttons for critical alerts
        if severity == 'critical':
            message['attachments'][0]['actions'] = [
                {
                    "type": "button",
                    "text": "Voir Dashboard",
                    "url": f"{os.getenv('FRONTEND_URL', 'https://ezbi-analytics.vercel.app')}/dashboard"
                },
                {
                    "type": "button", 
                    "text": "Analyse Cash Flow",
                    "url": f"{os.getenv('FRONTEND_URL', 'https://ezbi-analytics.vercel.app')}/cash-flow"
                }
            ]
        
        return await self._send_message(message, f"cash_flow_alert_{alert['type']}")
    
    async def send_daily_summary(self, summary: Dict[str, Any]) -> bool:
        """Send daily business activity summary"""
        
        if not self.webhook_url:
            print(f"📊 Daily Summary (Slack disabled): {summary}")
            return False
        
        seasonal_info = ""
        if 'seasonal_multiplier' in summary and summary['seasonal_multiplier'] != 1.0:
            seasonal_info = f" (Facteur saisonnier: {summary['seasonal_multiplier']:.2f}x pour {summary.get('month', 'ce mois')})"
        
        message = {
            "channel": self.channel,
            "username": self.bot_name,
            "icon_emoji": ":factory:",
            "text": f"📊 Activité Manufacturière Quotidienne - {summary['date']}{seasonal_info}",
            "attachments": [{
                "color": "#36a64f",
                "fields": [
                    {
                        "title": "🔷 Nouvelles Commandes",
                        "value": str(summary['orders_created']),
                        "short": True
                    },
                    {
                        "title": "📄 Factures Générées", 
                        "value": str(summary['invoices_generated']),
                        "short": True
                    },
                    {
                        "title": "💰 Transactions",
                        "value": str(summary['transactions_processed']),
                        "short": True
                    },
                    {
                        "title": "🏭 Statut",
                        "value": "Simulation Active" if summary.get('simulated') else "Production Live",
                        "short": True
                    }
                ],
                "footer": "EZBI Rapport Quotidien",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        # Add warning if simulated
        if summary.get('simulated'):
            message['attachments'][0]['color'] = '#FFA500'
            message['attachments'][0]['fields'].append({
                "title": "⚠️ Mode",
                "value": "Données simulées - Base de données non disponible",
                "short": False
            })
        
        return await self._send_message(message, f"daily_summary_{summary['date']}")
    
    async def send_system_alert(self, alert_type: str, message: str, details: Optional[Dict] = None) -> bool:
        """Send system-level alerts (API errors, deployment issues, etc.)"""
        
        if not self.webhook_url:
            print(f"🔧 System Alert (Slack disabled): {message}")
            return False
        
        color = '#FF4444' if alert_type == 'error' else '#FFA500'
        emoji = '🚨' if alert_type == 'error' else '⚠️'
        
        slack_message = {
            "channel": self.channel,
            "username": f"{self.bot_name} System",
            "icon_emoji": ":warning:",
            "attachments": [{
                "color": color,
                "title": f"{emoji} Alerte Système EZBI",
                "text": message,
                "fields": [
                    {
                        "title": "Type",
                        "value": alert_type.title(),
                        "short": True
                    },
                    {
                        "title": "Timestamp",
                        "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "short": True
                    }
                ],
                "footer": "EZBI System Monitor",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        if details:
            for key, value in details.items():
                slack_message['attachments'][0]['fields'].append({
                    "title": key.title(),
                    "value": str(value),
                    "short": True
                })
        
        return await self._send_message(slack_message, f"system_alert_{alert_type}")
    
    async def send_deployment_notification(self, status: str, environment: str, details: Dict[str, Any]) -> bool:
        """Send deployment status notifications"""
        
        if not self.webhook_url:
            print(f"🚀 Deployment (Slack disabled): {status} - {environment}")
            return False
        
        color_map = {
            'success': '#36a64f',
            'failed': '#FF0000', 
            'started': '#3AA3E3',
            'warning': '#FFA500'
        }
        
        emoji_map = {
            'success': '✅',
            'failed': '❌',
            'started': '🚀',
            'warning': '⚠️'
        }
        
        emoji = emoji_map.get(status, '🔄')
        color = color_map.get(status, '#808080')
        
        message = {
            "channel": self.channel,
            "username": f"{self.bot_name} Deploy",
            "icon_emoji": ":rocket:",
            "attachments": [{
                "color": color,
                "title": f"{emoji} Déploiement EZBI Analytics",
                "text": f"Environment: **{environment}** | Status: **{status.upper()}**",
                "fields": [
                    {
                        "title": "Environment",
                        "value": environment,
                        "short": True
                    },
                    {
                        "title": "Status",
                        "value": status.upper(),
                        "short": True
                    }
                ],
                "footer": "EZBI DevOps",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        for key, value in details.items():
            message['attachments'][0]['fields'].append({
                "title": key.replace('_', ' ').title(),
                "value": str(value),
                "short": True
            })
        
        return await self._send_message(message, f"deployment_{status}_{environment}")
    
    async def _send_message(self, message: Dict, log_id: str) -> bool:
        """Internal method to send message to Slack"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url, 
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        print(f"✅ Slack notification sent: {log_id}")
                        return True
                    else:
                        print(f"❌ Slack notification failed: {response.status} for {log_id}")
                        return False
                        
        except asyncio.TimeoutError:
            print(f"⏰ Slack notification timeout: {log_id}")
            return False
        except Exception as e:
            print(f"❌ Slack notification error for {log_id}: {e}")
            return False
    
    def test_configuration(self) -> bool:
        """Test Slack configuration"""
        
        if not self.webhook_url:
            print("❌ Slack webhook URL not configured")
            return False
        
        print(f"✅ Slack configuration OK")
        print(f"   - Webhook URL: {'*' * 50 + self.webhook_url[-10:]}")
        print(f"   - Channel: {self.channel}")
        print(f"   - Bot Name: {self.bot_name}")
        return True

# Test function for CLI usage
async def test_slack_notifications():
    """Test function for Slack notifications"""
    
    notifier = SlackNotifier()
    
    if not notifier.test_configuration():
        return False
    
    # Test daily summary
    test_summary = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'orders_created': 5,
        'invoices_generated': 8,
        'transactions_processed': 12,
        'seasonal_multiplier': 1.15,
        'month': 'November'
    }
    
    print("📊 Testing daily summary notification...")
    await notifier.send_daily_summary(test_summary)
    
    # Test cash flow alert
    test_alert = {
        'type': 'critical_cash_low',
        'severity': 'warning',
        'message': 'Cash flow monitoring test alert',
        'current_balance': 75000.50,
        'daily_trend': -2500.25
    }
    
    print("🚨 Testing cash flow alert...")
    await notifier.send_cash_flow_alert(test_alert)
    
    # Test system alert
    print("🔧 Testing system alert...")
    await notifier.send_system_alert('info', 'Slack notification system test completed', {
        'version': '2.0.0',
        'environment': 'production'
    })
    
    print("✅ All Slack notification tests completed")
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_slack_notifications())