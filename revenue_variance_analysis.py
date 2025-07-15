#!/usr/bin/env python3
"""
Revenue Variance Analysis for SPARC Data Engineering Fix
"""

import sqlite3
import json
from datetime import datetime

def analyze_revenue_variance():
    """Analyze the revenue recognition variance in detail"""
    
    # Connect to database
    conn = sqlite3.connect('data/ezbi_analytics.db')
    conn.row_factory = sqlite3.Row
    
    print("=== DETAILED REVENUE VARIANCE ANALYSIS ===")
    
    # Find cash entries without corresponding invoices
    orphaned_cash = conn.execute('''
        SELECT 
            cl.transaction_id,
            cl.transaction_number,
            cl.amount,
            cl.reference_id,
            cl.reference_type,
            cl.description,
            cl.date_recorded
        FROM finance_cash_ledger cl
        WHERE cl.transaction_type = 'Sale'
        AND (cl.reference_type != 'Invoice' OR cl.reference_id IS NULL OR NOT EXISTS (
            SELECT 1 FROM sales_invoices si 
            WHERE si.invoice_id = cl.reference_id
        ))
        ORDER BY cl.amount DESC
        LIMIT 10
    ''').fetchall()
    
    print("Orphaned cash entries (showing top 10 by amount):")
    for entry in orphaned_cash:
        print(f"  {entry['transaction_number']}: €{entry['amount']:,.2f} - {entry['description']}")
    
    # Get total orphaned amount
    total_orphaned_query = conn.execute('''
        SELECT SUM(cl.amount) as total_orphaned
        FROM finance_cash_ledger cl
        WHERE cl.transaction_type = 'Sale'
        AND (cl.reference_type != 'Invoice' OR cl.reference_id IS NULL OR NOT EXISTS (
            SELECT 1 FROM sales_invoices si 
            WHERE si.invoice_id = cl.reference_id
        ))
    ''').fetchone()
    
    print(f"\nTotal orphaned cash amount: €{total_orphaned_query['total_orphaned']:,.2f}")
    
    # Find invoices without cash entries
    missing_cash_invoices = conn.execute('''
        SELECT 
            si.invoice_id,
            si.invoice_number,
            si.amount,
            si.status,
            si.payment_date
        FROM sales_invoices si
        WHERE si.status = 'Paid'
        AND NOT EXISTS (
            SELECT 1 FROM finance_cash_ledger cl 
            WHERE cl.reference_id = si.invoice_id 
            AND cl.reference_type = 'Invoice'
            AND cl.transaction_type = 'Sale'
        )
        ORDER BY si.amount DESC
        LIMIT 5
    ''').fetchall()
    
    print(f"\nPaid invoices without cash entries (top 5):")
    for invoice in missing_cash_invoices:
        print(f"  {invoice['invoice_number']}: €{invoice['amount']:,.2f} - Status: {invoice['status']}")
    
    # Calculate variance breakdown
    print("\n=== VARIANCE BREAKDOWN ===")
    paid_invoices = conn.execute('SELECT SUM(amount) FROM sales_invoices WHERE status = "Paid"').fetchone()[0]
    cash_sales = conn.execute('SELECT SUM(amount) FROM finance_cash_ledger WHERE transaction_type = "Sale"').fetchone()[0]
    
    print(f"Paid invoices total: €{paid_invoices:,.2f}")
    print(f"Cash sales total: €{cash_sales:,.2f}")
    print(f"Revenue variance: €{paid_invoices - cash_sales:,.2f}")
    
    # Check for duplicate cash entries
    duplicate_cash = conn.execute('''
        SELECT reference_id, COUNT(*) as count, SUM(amount) as total_amount
        FROM finance_cash_ledger 
        WHERE transaction_type = 'Sale' AND reference_type = 'Invoice'
        GROUP BY reference_id 
        HAVING COUNT(*) > 1
        ORDER BY total_amount DESC
        LIMIT 5
    ''').fetchall()
    
    print(f"\nDuplicate cash entries for same invoice (top 5):")
    for dup in duplicate_cash:
        print(f"  Invoice ID {dup['reference_id']}: {dup['count']} entries, €{dup['total_amount']:,.2f}")
    
    conn.close()
    
    return {
        'orphaned_cash_amount': total_orphaned_query['total_orphaned'],
        'paid_invoices_total': paid_invoices,
        'cash_sales_total': cash_sales,
        'variance': paid_invoices - cash_sales
    }

if __name__ == "__main__":
    results = analyze_revenue_variance()
    print(f"\n=== SUMMARY ===")
    print(f"Revenue variance to fix: €{results['variance']:,.2f}")
    print(f"Orphaned cash causing issue: €{results['orphaned_cash_amount']:,.2f}")