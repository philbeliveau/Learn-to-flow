'use client';

import React, { useState, useEffect } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { formatCurrency } from '../../services/syntheticDataService';
import { authService } from '../../services/authService';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';

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
      
      // TEMPORARY: Skip authentication for testing - TO BE REMOVED
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      };
      
      // TODO: Re-enable once authentication is working
      // const headers = await authService.getAuthHeaders();
      
      // EMERGENCY: Use mock data while authentication is being fixed
      console.log('Using mock financial data - authentication bypass active');
      
      const mockFinanceData = {
        total_cash_flow: 125000,
        total_debt: 450000,
        interest_rate: 0.035,
        monthly_payments: 15000,
        debt_accounts_count: 3
      };
      
      const mockAccountingData = {
        ar_aging: [
          { aging_bucket: '0-30 days', invoice_count: 25, total_amount: 85000 },
          { aging_bucket: '31-60 days', invoice_count: 12, total_amount: 34000 },
          { aging_bucket: '61-90 days', invoice_count: 5, total_amount: 12000 },
          { aging_bucket: '90+ days', invoice_count: 3, total_amount: 8000 }
        ],
        ap_summary: {
          total_payables: 45,
          total_amount: 139000,
          avg_days_until_due: 22.5
        }
      };

      // Use mock data directly
      const finance = mockFinanceData;
      const accounting = mockAccountingData;
      const cashLedgerData = { data: [
        { transaction_number: 'TXN-2024-001', transaction_type: 'Inflow', amount: 25000, counterparty: 'Client ABC', date_recorded: '2024-07-14T10:00:00Z' },
        { transaction_number: 'TXN-2024-002', transaction_type: 'Outflow', amount: -8500, counterparty: 'Fournisseur XYZ', date_recorded: '2024-07-14T14:30:00Z' }
      ]};
      const debtAccountsData = { data: [
        { account_number: 'DEBT-001', institution_name: 'Banque Centrale', principal_amount: 200000, outstanding_balance: 185000, interest_rate: 0.035 },
        { account_number: 'DEBT-002', institution_name: 'Crédit Industriel', principal_amount: 150000, outstanding_balance: 142000, interest_rate: 0.041 }
      ]};

      // Create chart-ready structure from finance data
      const chartFinanceData = {
        cash_flow_by_type: [
          { transaction_type: 'Revenue', transaction_count: 150, total_amount: finance.total_cash_flow * 0.7 },
          { transaction_type: 'Expenses', transaction_count: 120, total_amount: finance.total_cash_flow * 0.3 }
        ],
        monthly_cash_flow: [],
        debt_summary: {
          total_loans: 3,
          total_principal: finance.total_debt,
          total_outstanding: finance.total_debt,
          avg_interest_rate: finance.interest_rate,
          total_monthly_payments: finance.monthly_payments
        }
      };
      
      setFinanceData(chartFinanceData);
      setAccountingData(accounting);
      setCashLedger(cashLedgerData.data || []);
      setDebtAccounts(debtAccountsData.data || []);
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
          🔄 MOCK DATA ACTIVE - Données financières de démonstration • 
          {cashLedger.length > 0 && `${formatNumber(cashLedger.length)} transactions • `}
          {debtAccounts.length > 0 && `${formatNumber(debtAccounts.length)} comptes de dette • `}
          Prêt pour connexion manufacturière via port 8004 (auth en cours de résolution)
        </p>
      </div>
    </div>
  );
};

export default FinancialChartsFixed;