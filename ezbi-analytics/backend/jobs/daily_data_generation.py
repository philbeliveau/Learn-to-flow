#!/usr/bin/env python3
"""
Daily manufacturing data generation for realistic business simulation
Production-grade cron job for EZBI Analytics
"""
import asyncio
import random
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add app root to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.core.database import get_async_session
    from sqlalchemy import text
    from jobs.slack_notifier import SlackNotifier
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Running in standalone mode with mock operations")
    SlackNotifier = None

class ManufacturingDataGenerator:
    """Generates realistic daily manufacturing business activity"""
    
    def __init__(self):
        self.seasonal_factors = {
            1: 0.85,   # January - post-holiday slowdown
            2: 0.90,   # February
            3: 1.05,   # March - spring ramp-up
            4: 1.10,   # April
            5: 1.15,   # May - peak production
            6: 1.20,   # June
            7: 0.95,   # July - summer vacation
            8: 0.80,   # August - vacation period
            9: 1.10,   # September - back to business
            10: 1.25,  # October - pre-holiday rush
            11: 1.30,  # November - holiday preparation
            12: 1.15   # December - holiday orders
        }
        
    def get_seasonal_multiplier(self) -> float:
        """Get seasonal multiplier for current month"""
        current_month = datetime.now().month
        return self.seasonal_factors.get(current_month, 1.0)
        
    async def generate_daily_business_activity(self) -> dict:
        """Generate realistic daily manufacturing business activity"""
        
        try:
            if 'get_async_session' not in globals():
                print("💡 Database not available, running in simulation mode")
                return self.simulate_business_activity()
            
            seasonal_mult = self.get_seasonal_multiplier()
            
            async with get_async_session() as db:
                # 1. Generate new customer orders (2-8 per day, seasonally adjusted)
                base_orders = random.randint(2, 8)
                order_count = max(1, int(base_orders * seasonal_mult))
                
                for i in range(order_count):
                    order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                    units_ordered = random.randint(50, 500) * seasonal_mult
                    
                    await db.execute(text("""
                        INSERT INTO operations.production_orders 
                        (order_number, product_id, customer_id, start_date, units_ordered, status)
                        VALUES (
                            :order_number,
                            (SELECT product_id FROM operations.products ORDER BY RANDOM() LIMIT 1),
                            (SELECT customer_id FROM sales.customers ORDER BY RANDOM() LIMIT 1),
                            :start_date,
                            :units_ordered,
                            'Planned'
                        )
                    """), {
                        'order_number': order_number,
                        'start_date': datetime.now(),
                        'units_ordered': int(units_ordered)
                    })
                
                # 2. Generate invoices (3-12 per day, seasonally adjusted)
                base_invoices = random.randint(3, 12)
                invoice_count = max(1, int(base_invoices * seasonal_mult))
                
                for i in range(invoice_count):
                    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                    base_amount = random.uniform(1000, 50000)
                    amount = base_amount * seasonal_mult
                    
                    await db.execute(text("""
                        INSERT INTO sales.invoices 
                        (invoice_number, customer_id, date_issued, due_date, amount, status)
                        VALUES (
                            :invoice_number,
                            (SELECT customer_id FROM sales.customers ORDER BY RANDOM() LIMIT 1),
                            :date_issued,
                            :due_date,
                            :amount,
                            'Open'
                        )
                    """), {
                        'invoice_number': invoice_number,
                        'date_issued': datetime.now(),
                        'due_date': datetime.now() + timedelta(days=30),
                        'amount': amount
                    })
                
                # 3. Generate cash transactions (5-15 per day)
                base_transactions = random.randint(5, 15)
                transaction_count = max(2, int(base_transactions * seasonal_mult))
                
                for i in range(transaction_count):
                    transaction_type = random.choice(['Inflow', 'Outflow'])
                    base_amount = random.uniform(500, 25000)
                    amount = base_amount * seasonal_mult
                    
                    if transaction_type == 'Outflow':
                        amount = -amount
                        
                    counterparties = [
                        'Client ABC SA', 'Fournisseur XYZ', 'Banque Centrale', 
                        'Vendeur Premium', 'Client Industries', 'Matières Premières SA'
                    ]
                    
                    await db.execute(text("""
                        INSERT INTO finance.cash_ledger 
                        (transaction_number, transaction_type, amount, counterparty, date_recorded)
                        VALUES (:txn_number, :txn_type, :amount, :counterparty, :date_recorded)
                    """), {
                        'txn_number': f"TXN-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}",
                        'txn_type': transaction_type,
                        'amount': amount,
                        'counterparty': random.choice(counterparties),
                        'date_recorded': datetime.now()
                    })
                
                await db.commit()
                
                summary = {
                    'success': True,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'orders_created': order_count,
                    'invoices_generated': invoice_count,
                    'transactions_processed': transaction_count,
                    'seasonal_multiplier': seasonal_mult,
                    'month': datetime.now().strftime('%B')
                }
                
                print(f"✅ Generated daily data: {order_count} orders, {invoice_count} invoices, {transaction_count} transactions (seasonal: {seasonal_mult:.2f}x)")
                
                # Send success notification to Slack
                if SlackNotifier:
                    notifier = SlackNotifier()
                    await notifier.send_daily_summary(summary)
                    
                return summary
                
        except Exception as e:
            print(f"❌ Error generating business data: {e}")
            return {
                'success': False,
                'error': str(e),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
    def simulate_business_activity(self) -> dict:
        """Simulate business activity when database is not available"""
        seasonal_mult = self.get_seasonal_multiplier()
        
        order_count = max(1, int(random.randint(2, 8) * seasonal_mult))
        invoice_count = max(1, int(random.randint(3, 12) * seasonal_mult))
        transaction_count = max(2, int(random.randint(5, 15) * seasonal_mult))
        
        summary = {
            'success': True,
            'simulated': True,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'orders_created': order_count,
            'invoices_generated': invoice_count,
            'transactions_processed': transaction_count,
            'seasonal_multiplier': seasonal_mult,
            'month': datetime.now().strftime('%B')
        }
        
        print(f"📊 Simulated daily data: {order_count} orders, {invoice_count} invoices, {transaction_count} transactions")
        return summary

async def main():
    """Main execution function"""
    generator = ManufacturingDataGenerator()
    result = await generator.generate_daily_business_activity()
    
    if result['success']:
        print("🏭 Daily manufacturing data generation completed successfully")
    else:
        print(f"❌ Daily data generation failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())