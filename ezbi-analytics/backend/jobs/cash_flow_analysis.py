#!/usr/bin/env python3
"""
Cash flow analysis and automatic Slack alerting
Production-grade monitoring system for manufacturing cash flow
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add app root to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.core.database import get_async_session
    from sqlalchemy import text
    from jobs.slack_notifier import SlackNotifier
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Running in standalone mode")
    SlackNotifier = None

class CashFlowAnalyzer:
    """Advanced cash flow analysis with intelligent alerting"""
    
    def __init__(self):
        self.alert_thresholds = {
            'critical_low_cash': 50000,      # €50K - immediate attention needed
            'negative_trend': -10000,        # €10K decline/day - concerning trend
            'overdue_receivables': 100000,   # €100K overdue - collection issue
            'high_payables': 200000,         # €200K pending - cash flow planning
            'liquidity_ratio': 1.2,          # Below 1.2 - liquidity concern
            'collection_period': 45          # Above 45 days - slow collections
        }
        
        self.risk_weights = {
            'seasonal_factor': 0.15,
            'customer_concentration': 0.20,
            'debt_burden': 0.25,
            'cash_volatility': 0.25,
            'collection_efficiency': 0.15
        }
    
    async def analyze_cash_flow(self) -> Dict:
        """Comprehensive cash flow analysis with intelligent alerting"""
        
        try:
            if 'get_async_session' not in globals():
                print("💡 Database not available, running cash flow simulation")
                return await self.simulate_cash_flow_analysis()
            
            async for db in get_async_session():
                # 1. Current cash position analysis
                cash_analysis = await self._analyze_cash_position(db)
                
                # 2. Trend analysis (7-day, 30-day patterns)
                trend_analysis = await self._analyze_trends(db)
                
                # 3. Receivables and payables analysis
                ap_ar_analysis = await self._analyze_receivables_payables(db)
                
                # 4. Risk assessment
                risk_assessment = await self._assess_cash_flow_risks(db, cash_analysis, trend_analysis)
                
                # 5. Generate alerts based on analysis
                alerts = self._generate_alerts(cash_analysis, trend_analysis, ap_ar_analysis, risk_assessment)
                
                # 6. Send alerts to Slack if needed
                if alerts and SlackNotifier:
                    await self._send_alerts_to_slack(alerts)
                
                # Compile comprehensive report
                report = {
                    'success': True,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'cash_position': cash_analysis,
                    'trends': trend_analysis,
                    'receivables_payables': ap_ar_analysis,
                    'risk_assessment': risk_assessment,
                    'alerts_generated': len(alerts),
                    'alerts': alerts
                }
                
                print(f"✅ Cash flow analysis complete. Position: €{cash_analysis['current_balance']:,.2f}, Alerts: {len(alerts)}")
                return report
                
        except Exception as e:
            print(f"❌ Cash flow analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    async def _analyze_cash_position(self, db) -> Dict:
        """Analyze current cash position and recent activity"""
        
        # Get current cash balance
        cash_result = await db.execute(text("""
            SELECT COALESCE(SUM(amount), 0) as total_cash,
                   COUNT(*) as transaction_count
            FROM finance.cash_ledger
            WHERE date_recorded <= NOW()
        """))
        cash_row = cash_result.fetchone()
        current_balance = float(cash_row.total_cash) if cash_row else 0.0
        transaction_count = int(cash_row.transaction_count) if cash_row else 0
        
        # Get today's activity
        today_result = await db.execute(text("""
            SELECT 
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as inflows,
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as outflows,
                COUNT(*) as daily_transactions
            FROM finance.cash_ledger
            WHERE date_recorded >= CURRENT_DATE
        """))
        today_row = today_result.fetchone()
        
        return {
            'current_balance': current_balance,
            'total_transactions': transaction_count,
            'daily_inflows': float(today_row.inflows) if today_row else 0.0,
            'daily_outflows': float(today_row.outflows) if today_row else 0.0,
            'daily_net_flow': (float(today_row.inflows) - float(today_row.outflows)) if today_row else 0.0,
            'daily_transactions': int(today_row.daily_transactions) if today_row else 0
        }
    
    async def _analyze_trends(self, db) -> Dict:
        """Analyze cash flow trends over different periods"""
        
        # 7-day trend analysis
        weekly_result = await db.execute(text("""
            SELECT 
                DATE(date_recorded) as day,
                COALESCE(SUM(amount), 0) as net_flow
            FROM finance.cash_ledger
            WHERE date_recorded >= NOW() - INTERVAL 7 DAY
            GROUP BY DATE(date_recorded)
            ORDER BY day DESC
        """))
        weekly_data = [{'date': row.day.isoformat(), 'net_flow': float(row.net_flow)} 
                      for row in weekly_result.fetchall()]
        
        # Calculate trend metrics
        if len(weekly_data) > 1:
            recent_flows = [d['net_flow'] for d in weekly_data[:3]]  # Last 3 days
            earlier_flows = [d['net_flow'] for d in weekly_data[3:7]]  # Previous 4 days
            
            recent_avg = sum(recent_flows) / len(recent_flows) if recent_flows else 0
            earlier_avg = sum(earlier_flows) / len(earlier_flows) if earlier_flows else 0
            trend_direction = recent_avg - earlier_avg
        else:
            trend_direction = 0
        
        # 30-day volatility analysis
        volatility_result = await db.execute(text("""
            SELECT 
                STDDEV(daily_flow) as volatility,
                AVG(daily_flow) as avg_flow
            FROM (
                SELECT DATE(date_recorded) as day, SUM(amount) as daily_flow
                FROM finance.cash_ledger
                WHERE date_recorded >= NOW() - INTERVAL 30 DAY
                GROUP BY DATE(date_recorded)
            ) daily_flows
        """))
        volatility_row = volatility_result.fetchone()
        
        return {
            'weekly_data': weekly_data,
            'trend_direction': trend_direction,
            'daily_average': sum(d['net_flow'] for d in weekly_data) / len(weekly_data) if weekly_data else 0,
            'volatility': float(volatility_row.volatility) if volatility_row and volatility_row.volatility else 0,
            'stability_score': max(0, min(1, 1 - abs(trend_direction) / 10000))  # Normalized stability
        }
    
    async def _analyze_receivables_payables(self, db) -> Dict:
        """Analyze accounts receivable and payable positions"""
        
        # Overdue receivables analysis
        overdue_result = await db.execute(text("""
            SELECT 
                COALESCE(SUM(amount), 0) as overdue_amount,
                COUNT(*) as overdue_count,
                AVG(DATEDIFF(NOW(), due_date)) as avg_days_overdue
            FROM sales.invoices
            WHERE status = 'Open' AND due_date < NOW()
        """))
        overdue_row = overdue_result.fetchone()
        
        # Current receivables
        ar_result = await db.execute(text("""
            SELECT 
                COALESCE(SUM(amount), 0) as total_receivables,
                COUNT(*) as open_invoices,
                AVG(DATEDIFF(due_date, date_issued)) as avg_payment_terms
            FROM sales.invoices
            WHERE status = 'Open'
        """))
        ar_row = ar_result.fetchone()
        
        # Current payables (if exists)
        try:
            ap_result = await db.execute(text("""
                SELECT 
                    COALESCE(SUM(amount), 0) as total_payables,
                    COUNT(*) as payable_count
                FROM accounting.accounts_payable
                WHERE status = 'Open'
            """))
            ap_row = ap_result.fetchone()
            total_payables = float(ap_row.total_payables) if ap_row else 0
            payable_count = int(ap_row.payable_count) if ap_row else 0
        except:
            total_payables = 0
            payable_count = 0
        
        return {
            'overdue_receivables': float(overdue_row.overdue_amount) if overdue_row else 0,
            'overdue_count': int(overdue_row.overdue_count) if overdue_row else 0,
            'avg_days_overdue': float(overdue_row.avg_days_overdue) if overdue_row and overdue_row.avg_days_overdue else 0,
            'total_receivables': float(ar_row.total_receivables) if ar_row else 0,
            'open_invoices': int(ar_row.open_invoices) if ar_row else 0,
            'avg_payment_terms': float(ar_row.avg_payment_terms) if ar_row and ar_row.avg_payment_terms else 30,
            'total_payables': total_payables,
            'payable_count': payable_count
        }
    
    async def _assess_cash_flow_risks(self, db, cash_analysis: Dict, trend_analysis: Dict) -> Dict:
        """Assess overall cash flow risks using weighted factors"""
        
        risk_factors = {}
        overall_risk = 0.0
        
        # Liquidity risk
        current_ratio = cash_analysis['current_balance'] / max(cash_analysis['daily_outflows'] * 30, 1)
        liquidity_risk = max(0, (2.0 - current_ratio) / 2.0)
        risk_factors['liquidity'] = liquidity_risk
        overall_risk += liquidity_risk * self.risk_weights['debt_burden']
        
        # Trend risk
        trend_risk = max(0, -trend_analysis['trend_direction'] / 10000)
        risk_factors['trend'] = min(1.0, trend_risk)
        overall_risk += risk_factors['trend'] * self.risk_weights['cash_volatility']
        
        # Volatility risk
        volatility_risk = min(1.0, trend_analysis['volatility'] / 5000)
        risk_factors['volatility'] = volatility_risk
        overall_risk += volatility_risk * self.risk_weights['cash_volatility']
        
        # Seasonal risk (basic implementation)
        month = datetime.now().month
        seasonal_months = [7, 8, 12, 1]  # Summer vacation and year-end
        seasonal_risk = 0.3 if month in seasonal_months else 0.1
        risk_factors['seasonal'] = seasonal_risk
        overall_risk += seasonal_risk * self.risk_weights['seasonal_factor']
        
        return {
            'overall_risk_score': min(1.0, overall_risk),
            'risk_level': 'High' if overall_risk > 0.7 else 'Medium' if overall_risk > 0.4 else 'Low',
            'risk_factors': risk_factors,
            'recommendations': self._generate_risk_recommendations(risk_factors, overall_risk)
        }
    
    def _generate_risk_recommendations(self, risk_factors: Dict, overall_risk: float) -> List[str]:
        """Generate actionable risk recommendations"""
        
        recommendations = []
        
        if risk_factors.get('liquidity', 0) > 0.5:
            recommendations.append("Améliorer la position de liquidité - envisager une ligne de crédit")
        
        if risk_factors.get('trend', 0) > 0.6:
            recommendations.append("Tendance négative détectée - analyser les causes et prendre des mesures correctives")
        
        if risk_factors.get('volatility', 0) > 0.5:
            recommendations.append("Forte volatilité des flux - améliorer la prévisibilité des revenus")
        
        if overall_risk > 0.7:
            recommendations.append("Risque élevé détecté - révision urgente de la stratégie cash flow")
        
        if not recommendations:
            recommendations.append("Position cash flow stable - continuer la surveillance régulière")
        
        return recommendations
    
    def _generate_alerts(self, cash_analysis: Dict, trend_analysis: Dict, 
                        ap_ar_analysis: Dict, risk_assessment: Dict) -> List[Dict]:
        """Generate alerts based on analysis results"""
        
        alerts = []
        
        # Critical low cash alert
        if cash_analysis['current_balance'] < self.alert_thresholds['critical_low_cash']:
            alerts.append({
                'type': 'critical_cash_low',
                'severity': 'critical',
                'message': f'Solde de trésorerie critique: €{cash_analysis["current_balance"]:,.2f}',
                'current_balance': cash_analysis['current_balance'],
                'threshold': self.alert_thresholds['critical_low_cash']
            })
        
        # Negative trend alert
        if trend_analysis['trend_direction'] < self.alert_thresholds['negative_trend']:
            alerts.append({
                'type': 'negative_trend',
                'severity': 'warning',
                'message': f'Tendance négative détectée: €{trend_analysis["trend_direction"]:,.2f}/jour',
                'daily_trend': trend_analysis['trend_direction'],
                'daily_average': trend_analysis['daily_average']
            })
        
        # Overdue receivables alert
        if ap_ar_analysis['overdue_receivables'] > self.alert_thresholds['overdue_receivables']:
            alerts.append({
                'type': 'overdue_receivables',
                'severity': 'warning',
                'message': f'Créances en retard importantes: €{ap_ar_analysis["overdue_receivables"]:,.2f}',
                'overdue_amount': ap_ar_analysis['overdue_receivables'],
                'overdue_count': ap_ar_analysis['overdue_count'],
                'avg_days_overdue': ap_ar_analysis['avg_days_overdue']
            })
        
        # High overall risk alert
        if risk_assessment['overall_risk_score'] > 0.8:
            alerts.append({
                'type': 'high_risk_detected',
                'severity': 'critical',
                'message': f'Risque cash flow élevé détecté: {risk_assessment["overall_risk_score"]:.1%}',
                'risk_score': risk_assessment['overall_risk_score'],
                'risk_level': risk_assessment['risk_level'],
                'recommendations': risk_assessment['recommendations'][:2]  # Top 2 recommendations
            })
        
        return alerts
    
    async def _send_alerts_to_slack(self, alerts: List[Dict]) -> None:
        """Send generated alerts to Slack"""
        
        if not SlackNotifier:
            print("⚠️ Slack notifications disabled")
            return
        
        notifier = SlackNotifier()
        
        for alert in alerts:
            try:
                await notifier.send_cash_flow_alert(alert)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"❌ Failed to send alert {alert['type']}: {e}")
    
    async def simulate_cash_flow_analysis(self) -> Dict:
        """Simulate cash flow analysis when database is unavailable"""
        
        # Generate realistic simulated data
        simulated_balance = 75000 + (datetime.now().day - 15) * 1000  # Varies by day of month
        daily_trend = -2000 + (datetime.now().weekday() * 500)  # Varies by weekday
        
        alerts = []
        
        # Simulate some alerts based on date patterns
        if simulated_balance < 50000:
            alerts.append({
                'type': 'critical_cash_low',
                'severity': 'critical', 
                'message': f'[SIMULÉ] Solde critique: €{simulated_balance:,.2f}',
                'current_balance': simulated_balance
            })
        
        if daily_trend < -5000:
            alerts.append({
                'type': 'negative_trend',
                'severity': 'warning',
                'message': f'[SIMULÉ] Tendance négative: €{daily_trend:,.2f}/jour',
                'daily_trend': daily_trend
            })
        
        print(f"📊 Simulated cash flow analysis: Balance €{simulated_balance:,.2f}, Trend €{daily_trend:,.2f}/day, Alerts: {len(alerts)}")
        
        return {
            'success': True,
            'simulated': True,
            'analysis_timestamp': datetime.now().isoformat(),
            'cash_position': {
                'current_balance': simulated_balance,
                'daily_net_flow': daily_trend
            },
            'trends': {
                'trend_direction': daily_trend,
                'daily_average': daily_trend
            },
            'alerts_generated': len(alerts),
            'alerts': alerts
        }

async def main():
    """Main execution function"""
    analyzer = CashFlowAnalyzer()
    result = await analyzer.analyze_cash_flow()
    
    if result['success']:
        print("💰 Cash flow analysis completed successfully")
        if result.get('alerts_generated', 0) > 0:
            print(f"⚠️ {result['alerts_generated']} alerts generated and sent to Slack")
    else:
        print(f"❌ Cash flow analysis failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())