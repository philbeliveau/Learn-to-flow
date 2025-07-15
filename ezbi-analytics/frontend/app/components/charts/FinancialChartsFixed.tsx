'use client';

import React, { useState, useEffect } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { formatCurrency } from '../../services/syntheticDataService';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface FinancialChartsProps {
  chartOptions: any;
  pieChartOptions: any;
}

interface FinanceData {
  cash_flow_by_type: Array<{
    transaction_type: string;
    transaction_count: number;
    total_amount: number;
  }>;
  monthly_cash_flow: Array<{
    month: string;
    inflow: number;
    outflow: number;
    net_flow: number;
  }>;
  debt_summary: {
    total_loans: number;
    total_principal: number;
    total_outstanding: number;
    avg_interest_rate: number;
    total_monthly_payments: number;
  };
}

interface AccountingData {
  ar_aging: Array<{
    aging_bucket: string;
    invoice_count: number;
    total_amount: number;
  }>;
  ap_summary: {
    total_payables: number;
    total_amount: number;
    avg_days_until_due: number;
  };
  purchase_categories: Array<{
    category: string;
    purchase_count: number;
    total_amount: number;
  }>;
}

const FinancialChartsFixed: React.FC<FinancialChartsProps> = ({ chartOptions, pieChartOptions }) => {
  const [financeData, setFinanceData] = useState<FinanceData | null>(null);
  const [accountingData, setAccountingData] = useState<AccountingData | null>(null);
  const [cashLedger, setCashLedger] = useState<any[]>([]);
  const [debtAccounts, setDebtAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFinancialData();
  }, []);

  const loadFinancialData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch all financial data from manufacturing tables
      const [financeRes, accountingRes, cashLedgerRes, debtAccountsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/manufacturing/finance/kpis`),
        fetch(`${API_BASE_URL}/api/manufacturing/accounting/kpis`),
        fetch(`${API_BASE_URL}/api/manufacturing/finance/cash-ledger`),
        fetch(`${API_BASE_URL}/api/manufacturing/finance/debt-accounts`)
      ]);

      if (!financeRes.ok || !accountingRes.ok || !cashLedgerRes.ok || !debtAccountsRes.ok) {
        throw new Error('Failed to fetch financial data');
      }

      const [finance, accounting, cashData, debtData] = await Promise.all([
        financeRes.json(),
        accountingRes.json(),
        cashLedgerRes.json(),
        debtAccountsRes.json()
      ]);

      setFinanceData(finance);
      setAccountingData(accounting);
      setCashLedger(cashData.transactions || []);
      setDebtAccounts(debtData.debts || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load financial data');
      console.error('Failed to load financial data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('fr-FR').format(num);
  };

  // Generate chart data for cash flow by type
  const getCashFlowByTypeChart = () => {
    if (!financeData) return null;
    
    return {
      labels: financeData.cash_flow_by_type.map(item => item.transaction_type),
      datasets: [{
        label: 'Montant Total',
        data: financeData.cash_flow_by_type.map(item => item.total_amount),
        backgroundColor: [
          '#3B82F6',
          '#10B981',
          '#F59E0B',
          '#EF4444',
          '#8B5CF6'
        ],
        borderColor: '#ffffff',
        borderWidth: 1
      }]
    };
  };

  // Generate chart data for monthly cash flow
  const getMonthlyCashFlowChart = () => {
    if (!financeData) return null;
    
    return {
      labels: financeData.monthly_cash_flow.map(item => item.month),
      datasets: [
        {
          label: 'Entrées',
          data: financeData.monthly_cash_flow.map(item => item.inflow),
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4
        },
        {
          label: 'Sorties',
          data: financeData.monthly_cash_flow.map(item => Math.abs(item.outflow)),
          borderColor: '#EF4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          tension: 0.4
        },
        {
          label: 'Flux net',
          data: financeData.monthly_cash_flow.map(item => item.net_flow),
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4
        }
      ]
    };
  };

  // Generate chart data for AR aging
  const getARAgingChart = () => {
    if (!accountingData) return null;
    
    return {
      labels: accountingData.ar_aging.map(item => item.aging_bucket),
      datasets: [{
        label: 'Montant Outstanding',
        data: accountingData.ar_aging.map(item => item.total_amount),
        backgroundColor: [
          '#10B981',
          '#F59E0B',
          '#EF4444',
          '#DC2626'
        ],
        borderColor: '#ffffff',
        borderWidth: 1
      }]
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500 text-red-400 p-4 rounded-lg">
        <p>Erreur: {error}</p>
        <button 
          onClick={loadFinancialData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-light text-white">Analyse Financière</h2>
        <div className="flex gap-2">
          <span className="bg-blue-600 px-3 py-1 rounded-full text-sm">Finance Tables</span>
          <span className="bg-green-600 px-3 py-1 rounded-full text-sm">Live Data</span>
        </div>
      </div>

      {/* Financial Summary Cards */}
      {financeData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Prêts actifs</h3>
            <p className="text-2xl font-light text-white">{formatNumber(financeData.debt_summary.total_loans)}</p>
            <p className="text-xs text-white/50">Comptes de dette</p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Montant emprunté</h3>
            <p className="text-2xl font-light text-white">{formatCurrency(financeData.debt_summary.total_outstanding)}</p>
            <p className="text-xs text-white/50">Encours total</p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Taux d'intérêt</h3>
            <p className="text-2xl font-light text-white">{(financeData.debt_summary.avg_interest_rate * 100).toFixed(2)}%</p>
            <p className="text-xs text-white/50">Moyenne pondérée</p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Paiements mensuels</h3>
            <p className="text-2xl font-light text-white">{formatCurrency(financeData.debt_summary.total_monthly_payments)}</p>
            <p className="text-xs text-white/50">Total mensuel</p>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cash Flow by Type */}
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
          <h3 className="text-lg font-light text-white mb-4">Flux de trésorerie par type</h3>
          <div className="h-64">
            {getCashFlowByTypeChart() && (
              <Pie data={getCashFlowByTypeChart()!} options={pieChartOptions} />
            )}
          </div>
        </div>

        {/* AR Aging */}
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
          <h3 className="text-lg font-light text-white mb-4">Âge des créances</h3>
          <div className="h-64">
            {getARAgingChart() && (
              <Bar data={getARAgingChart()!} options={chartOptions} />
            )}
          </div>
        </div>

        {/* Monthly Cash Flow Trend */}
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20 col-span-1 lg:col-span-2">
          <h3 className="text-lg font-light text-white mb-4">Tendance mensuelle du flux de trésorerie</h3>
          <div className="h-64">
            {getMonthlyCashFlowChart() && (
              <Line data={getMonthlyCashFlowChart()!} options={chartOptions} />
            )}
          </div>
        </div>
      </div>

      {/* Accounts Payable Summary */}
      {accountingData && (
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
          <h3 className="text-lg font-light text-white mb-4">Comptes fournisseurs</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-light text-white">{formatNumber(accountingData.ap_summary.total_payables)}</p>
              <p className="text-sm text-white/70">Factures à payer</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-light text-white">{formatCurrency(accountingData.ap_summary.total_amount)}</p>
              <p className="text-sm text-white/70">Montant total</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-light text-white">{accountingData.ap_summary.avg_days_until_due.toFixed(0)}</p>
              <p className="text-sm text-white/70">Jours moyens avant échéance</p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Transactions */}
      <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
        <h3 className="text-lg font-light text-white mb-4">Transactions récentes</h3>
        <div className="space-y-3">
          {cashLedger.slice(0, 8).map((transaction, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${transaction.amount > 0 ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <div>
                  <p className="text-white font-medium">{transaction.transaction_number}</p>
                  <p className="text-white/60 text-sm">{transaction.transaction_type} • {transaction.counterparty}</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`font-medium ${transaction.amount > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {formatCurrency(transaction.amount)}
                </p>
                <p className="text-white/60 text-sm">{new Date(transaction.date_recorded).toLocaleDateString('fr-FR')}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Data Source Info */}
      <div className="bg-blue-900/20 border border-blue-500 p-4 rounded-lg">
        <h4 className="text-blue-400 font-medium mb-2">Source des données</h4>
        <p className="text-blue-300 text-sm">
          ✅ Connecté aux tables finance_cash_ledger, finance_debt_accounts, accounting_* • 
          {cashLedger.length > 0 && `${formatNumber(cashLedger.length)} transactions • `}
          {debtAccounts.length > 0 && `${formatNumber(debtAccounts.length)} comptes de dette • `}
          Données manufacturières en temps réel
        </p>
      </div>
    </div>
  );
};

export default FinancialChartsFixed;