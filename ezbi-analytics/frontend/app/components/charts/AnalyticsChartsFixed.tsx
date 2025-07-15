'use client';

import React, { useState, useEffect } from 'react';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
import { formatCurrency } from '../../services/syntheticDataService';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface AnalyticsChartsProps {
  chartOptions: any;
  pieChartOptions: any;
}

interface ComprehensiveAnalytics {
  overview: {
    total_customers: number;
    total_revenue: number;
    total_orders: number;
    total_units_produced: number;
    active_employees: number;
    monthly_fixed_costs: number;
    total_debt: number;
    total_receivables: number;
  };
  sales_kpis: {
    total_invoices: number;
    total_revenue: number;
    avg_invoice_value: number;
    active_customers: number;
    monthly_trend: Array<{
      month: string;
      revenue: number;
      invoice_count: number;
    }>;
  };
  operations_kpis: {
    total_orders: number;
    total_units_produced: number;
    avg_efficiency: number;
    top_products: Array<{
      product_name: string;
      total_produced: number;
      order_count: number;
    }>;
  };
  finance_kpis: {
    debt_summary: {
      total_loans: number;
      total_outstanding: number;
      avg_interest_rate: number;
      total_monthly_payments: number;
    };
    cash_flow_by_type: Array<{
      transaction_type: string;
      total_amount: number;
    }>;
  };
  hr_kpis: {
    total_employees: number;
    avg_salary: number;
    departments: number;
    department_breakdown: Array<{
      department: string;
      employee_count: number;
      avg_salary: number;
    }>;
  };
}

const AnalyticsChartsFixed: React.FC<AnalyticsChartsProps> = ({ chartOptions, pieChartOptions }) => {
  const [analyticsData, setAnalyticsData] = useState<ComprehensiveAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch comprehensive analytics from all manufacturing tables
      const [overviewRes, salesRes, operationsRes, financeRes, hrRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/manufacturing/dashboard/overview`),
        fetch(`${API_BASE_URL}/api/manufacturing/sales/kpis`),
        fetch(`${API_BASE_URL}/api/manufacturing/operations/kpis`),
        fetch(`${API_BASE_URL}/api/manufacturing/finance/kpis`),
        fetch(`${API_BASE_URL}/api/manufacturing/hr/kpis`)
      ]);

      if (!overviewRes.ok || !salesRes.ok || !operationsRes.ok || !financeRes.ok || !hrRes.ok) {
        throw new Error('Failed to fetch analytics data');
      }

      const [overview, sales, operations, finance, hr] = await Promise.all([
        overviewRes.json(),
        salesRes.json(),
        operationsRes.json(),
        financeRes.json(),
        hrRes.json()
      ]);

      setAnalyticsData({
        overview: overview.overview,
        sales_kpis: {
          ...sales.totals,
          monthly_trend: sales.monthly_trend
        },
        operations_kpis: {
          ...operations.efficiency,
          top_products: operations.top_products
        },
        finance_kpis: {
          debt_summary: finance.debt_summary,
          cash_flow_by_type: finance.cash_flow_by_type
        },
        hr_kpis: {
          ...hr.employee_summary,
          department_breakdown: hr.department_breakdown
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics data');
      console.error('Failed to load analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('fr-FR').format(num);
  };

  // Generate comprehensive business performance chart
  const getBusinessPerformanceChart = () => {
    if (!analyticsData) return null;
    
    return {
      labels: analyticsData.sales_kpis.monthly_trend.map(item => item.month),
      datasets: [
        {
          label: 'Chiffre d\'affaires',
          data: analyticsData.sales_kpis.monthly_trend.map(item => item.revenue),
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
          yAxisID: 'y'
        },
        {
          label: 'Nombre de factures',
          data: analyticsData.sales_kpis.monthly_trend.map(item => item.invoice_count),
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
          yAxisID: 'y1'
        }
      ]
    };
  };

  // Generate department performance chart
  const getDepartmentPerformanceChart = () => {
    if (!analyticsData) return null;
    
    return {
      labels: analyticsData.hr_kpis.department_breakdown.map(dept => dept.department),
      datasets: [
        {
          label: 'Nombre d\'employés',
          data: analyticsData.hr_kpis.department_breakdown.map(dept => dept.employee_count),
          backgroundColor: '#3B82F6',
          borderColor: '#ffffff',
          borderWidth: 1
        },
        {
          label: 'Salaire moyen (k€)',
          data: analyticsData.hr_kpis.department_breakdown.map(dept => dept.avg_salary / 1000),
          backgroundColor: '#10B981',
          borderColor: '#ffffff',
          borderWidth: 1
        }
      ]
    };
  };

  // Generate cash flow distribution chart
  const getCashFlowDistributionChart = () => {
    if (!analyticsData) return null;
    
    return {
      labels: analyticsData.finance_kpis.cash_flow_by_type.map(item => item.transaction_type),
      datasets: [{
        label: 'Montant',
        data: analyticsData.finance_kpis.cash_flow_by_type.map(item => Math.abs(item.total_amount)),
        backgroundColor: [
          '#3B82F6',
          '#10B981',
          '#F59E0B',
          '#EF4444',
          '#8B5CF6',
          '#EC4899'
        ],
        borderColor: '#ffffff',
        borderWidth: 2
      }]
    };
  };

  // Generate production efficiency chart
  const getProductionEfficiencyChart = () => {
    if (!analyticsData) return null;
    
    return {
      labels: analyticsData.operations_kpis.top_products.map(prod => prod.product_name),
      datasets: [{
        label: 'Unités produites',
        data: analyticsData.operations_kpis.top_products.map(prod => prod.total_produced),
        backgroundColor: '#8B5CF6',
        borderColor: '#ffffff',
        borderWidth: 1
      }]
    };
  };

  // Calculate key business ratios
  const getBusinessRatios = () => {
    if (!analyticsData) return null;
    
    const revenuePerEmployee = analyticsData.overview.total_revenue / analyticsData.overview.active_employees;
    const debtToRevenue = analyticsData.overview.total_debt / analyticsData.overview.total_revenue;
    const productionEfficiency = analyticsData.operations_kpis.avg_efficiency;
    const avgInvoiceValue = analyticsData.sales_kpis.avg_invoice_value;
    
    return {
      revenue_per_employee: revenuePerEmployee,
      debt_to_revenue_ratio: debtToRevenue,
      production_efficiency: productionEfficiency,
      avg_invoice_value: avgInvoiceValue
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
          onClick={loadAnalyticsData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Réessayer
        </button>
      </div>
    );
  }

  const businessRatios = getBusinessRatios();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-light text-white">Analytics Avancées</h2>
        <div className="flex gap-2">
          <span className="bg-blue-600 px-3 py-1 rounded-full text-sm">All 13 Tables</span>
          <span className="bg-green-600 px-3 py-1 rounded-full text-sm">Advanced Analytics</span>
        </div>
      </div>

      {/* Business Ratios Cards */}
      {businessRatios && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">CA par employé</h3>
            <p className="text-2xl font-light text-white">{formatCurrency(businessRatios.revenue_per_employee)}</p>
            <p className="text-xs text-white/50">Productivité</p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Ratio dette/CA</h3>
            <p className="text-2xl font-light text-white">{(businessRatios.debt_to_revenue_ratio * 100).toFixed(1)}%</p>
            <p className="text-xs text-white/50">Endettement</p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Efficacité production</h3>
            <p className="text-2xl font-light text-white">{businessRatios.production_efficiency.toFixed(1)}%</p>
            <p className="text-xs text-white/50">Performance</p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Facture moyenne</h3>
            <p className="text-2xl font-light text-white">{formatCurrency(businessRatios.avg_invoice_value)}</p>
            <p className="text-xs text-white/50">Panier moyen</p>
          </div>
        </div>
      )}

      {/* Main Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Business Performance Trend */}
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20 col-span-1 lg:col-span-2">
          <h3 className="text-lg font-light text-white mb-4">Performance commerciale</h3>
          <div className="h-64">
            {getBusinessPerformanceChart() && (
              <Line 
                data={getBusinessPerformanceChart()!} 
                options={{
                  ...chartOptions,
                  scales: {
                    ...chartOptions.scales,
                    y: {
                      ...chartOptions.scales.y,
                      type: 'linear',
                      display: true,
                      position: 'left',
                    },
                    y1: {
                      ...chartOptions.scales.y,
                      type: 'linear',
                      display: true,
                      position: 'right',
                      grid: {
                        drawOnChartArea: false,
                      },
                    },
                  }
                }}
              />
            )}
          </div>
        </div>

        {/* Department Performance */}
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
          <h3 className="text-lg font-light text-white mb-4">Performance par département</h3>
          <div className="h-64">
            {getDepartmentPerformanceChart() && (
              <Bar data={getDepartmentPerformanceChart()!} options={chartOptions} />
            )}
          </div>
        </div>

        {/* Cash Flow Distribution */}
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
          <h3 className="text-lg font-light text-white mb-4">Distribution des flux</h3>
          <div className="h-64">
            {getCashFlowDistributionChart() && (
              <Doughnut data={getCashFlowDistributionChart()!} options={pieChartOptions} />
            )}
          </div>
        </div>
      </div>

      {/* Production Analytics */}
      <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
        <h3 className="text-lg font-light text-white mb-4">Analyse de production</h3>
        <div className="h-64">
          {getProductionEfficiencyChart() && (
            <Bar data={getProductionEfficiencyChart()!} options={chartOptions} />
          )}
        </div>
      </div>

      {/* Comprehensive Business Overview */}
      {analyticsData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-lg font-light text-white mb-4">Ventes & Clients</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-white/70">Clients actifs:</span>
                <span className="text-white">{formatNumber(analyticsData.overview.total_customers)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Factures totales:</span>
                <span className="text-white">{formatNumber(analyticsData.sales_kpis.total_invoices)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">CA total:</span>
                <span className="text-white">{formatCurrency(analyticsData.overview.total_revenue)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Créances:</span>
                <span className="text-white">{formatCurrency(analyticsData.overview.total_receivables)}</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-lg font-light text-white mb-4">Production</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-white/70">Commandes:</span>
                <span className="text-white">{formatNumber(analyticsData.overview.total_orders)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Unités produites:</span>
                <span className="text-white">{formatNumber(analyticsData.overview.total_units_produced)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Efficacité:</span>
                <span className="text-white">{analyticsData.operations_kpis.avg_efficiency.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Produits actifs:</span>
                <span className="text-white">{formatNumber(analyticsData.operations_kpis.top_products.length)}</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-lg font-light text-white mb-4">Finance & RH</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-white/70">Employés:</span>
                <span className="text-white">{formatNumber(analyticsData.overview.active_employees)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Salaire moyen:</span>
                <span className="text-white">{formatCurrency(analyticsData.hr_kpis.avg_salary)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Dettes totales:</span>
                <span className="text-white">{formatCurrency(analyticsData.overview.total_debt)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Charges mensuelles:</span>
                <span className="text-white">{formatCurrency(analyticsData.overview.monthly_fixed_costs)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Data Source Info */}
      <div className="bg-blue-900/20 border border-blue-500 p-4 rounded-lg">
        <h4 className="text-blue-400 font-medium mb-2">Source des données analytiques</h4>
        <p className="text-blue-300 text-sm">
          ✅ Analyse complète des 13 tables manufacturières • 
          {analyticsData && (
            <>
              {formatNumber(analyticsData.overview.total_customers)} clients • 
              {formatNumber(analyticsData.overview.total_orders)} commandes • 
              {formatNumber(analyticsData.overview.active_employees)} employés • 
              {formatNumber(analyticsData.finance_kpis.debt_summary.total_loans)} prêts • 
            </>
          )}
          Analytics en temps réel
        </p>
      </div>
    </div>
  );
};

export default AnalyticsChartsFixed;