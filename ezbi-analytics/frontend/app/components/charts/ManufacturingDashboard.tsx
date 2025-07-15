"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Area, AreaChart
} from 'recharts';
import { 
  Building2, Users, Package, CreditCard, TrendingUp, TrendingDown,
  DollarSign, ShoppingCart, Truck, Calendar, AlertCircle, CheckCircle
} from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface DashboardData {
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
  recent_activity: Array<{
    type: string;
    reference: string;
    amount: number;
    date: string;
  }>;
}

interface SalesData {
  totals: {
    total_invoices: number;
    total_revenue: number;
    avg_invoice_value: number;
    active_customers: number;
  };
  status_breakdown: Array<{
    status: string;
    count: number;
    total_amount: number;
  }>;
  monthly_trend: Array<{
    month: string;
    revenue: number;
    invoice_count: number;
  }>;
  top_customers: Array<{
    company_name: string;
    total_revenue: number;
    invoice_count: number;
  }>;
}

interface OperationsData {
  efficiency: {
    total_orders: number;
    total_units_ordered: number;
    total_units_produced: number;
    avg_efficiency: number;
  };
  status_breakdown: Array<{
    status: string;
    order_count: number;
    units_ordered: number;
    units_produced: number;
  }>;
  top_products: Array<{
    product_name: string;
    total_produced: number;
    order_count: number;
  }>;
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

interface HRData {
  employee_summary: {
    total_employees: number;
    avg_salary: number;
    departments: number;
  };
  department_breakdown: Array<{
    department: string;
    employee_count: number;
    avg_salary: number;
  }>;
  monthly_payroll: Array<{
    month: string;
    total_gross: number;
    total_deductions: number;
    total_net: number;
    total_overtime: number;
  }>;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function ManufacturingDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [salesData, setSalesData] = useState<SalesData | null>(null);
  const [operationsData, setOperationsData] = useState<OperationsData | null>(null);
  const [financeData, setFinanceData] = useState<FinanceData | null>(null);
  const [hrData, setHRData] = useState<HRData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      
      // Fetch all data in parallel
      const [dashboardRes, salesRes, operationsRes, financeRes, hrRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/manufacturing/dashboard/overview`),
        fetch(`${API_BASE_URL}/api/manufacturing/sales/kpis`),
        fetch(`${API_BASE_URL}/api/manufacturing/operations/kpis`),
        fetch(`${API_BASE_URL}/api/manufacturing/finance/kpis`),
        fetch(`${API_BASE_URL}/api/manufacturing/hr/kpis`)
      ]);

      if (!dashboardRes.ok || !salesRes.ok || !operationsRes.ok || !financeRes.ok || !hrRes.ok) {
        throw new Error('Failed to fetch data');
      }

      const [dashboard, sales, operations, finance, hr] = await Promise.all([
        dashboardRes.json(),
        salesRes.json(),
        operationsRes.json(),
        financeRes.json(),
        hrRes.json()
      ]);

      setDashboardData(dashboard);
      setSalesData(sales);
      setOperationsData(operations);
      setFinanceData(finance);
      setHRData(hr);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('fr-FR').format(num);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">{error}</p>
            <Button onClick={fetchAllData} className="mt-4">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Manufacturing Dashboard</h1>
          <p className="text-gray-600">Complete business intelligence for manufacturing operations</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline">3,527 Records</Badge>
          <Badge variant="outline">13 Tables</Badge>
          <Badge variant="outline">Live Data</Badge>
        </div>
      </div>

      {/* Overview Cards */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(dashboardData.overview.total_revenue)}</div>
              <p className="text-xs text-muted-foreground">
                From {formatNumber(dashboardData.overview.total_customers)} customers
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Production Orders</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(dashboardData.overview.total_orders)}</div>
              <p className="text-xs text-muted-foreground">
                {formatNumber(dashboardData.overview.total_units_produced)} units produced
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Employees</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(dashboardData.overview.active_employees)}</div>
              <p className="text-xs text-muted-foreground">
                {formatCurrency(dashboardData.overview.monthly_fixed_costs)} monthly costs
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Outstanding Debt</CardTitle>
              <CreditCard className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(dashboardData.overview.total_debt)}</div>
              <p className="text-xs text-muted-foreground">
                {formatCurrency(dashboardData.overview.total_receivables)} receivables
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sales">Sales</TabsTrigger>
          <TabsTrigger value="operations">Operations</TabsTrigger>
          <TabsTrigger value="finance">Finance</TabsTrigger>
          <TabsTrigger value="hr">HR</TabsTrigger>
          <TabsTrigger value="accounting">Accounting</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboardData?.recent_activity.slice(0, 8).map((activity, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div className="flex items-center gap-3">
                        {activity.type === 'Invoice' ? (
                          <ShoppingCart className="h-4 w-4 text-blue-600" />
                        ) : (
                          <Package className="h-4 w-4 text-green-600" />
                        )}
                        <div>
                          <p className="font-medium">{activity.reference}</p>
                          <p className="text-sm text-gray-600">{activity.type}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{formatCurrency(activity.amount)}</p>
                        <p className="text-sm text-gray-600">{new Date(activity.date).toLocaleDateString('fr-FR')}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Business Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Customer Base</span>
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-blue-600" />
                      <span>{formatNumber(dashboardData?.overview.total_customers || 0)} customers</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Production Capacity</span>
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4 text-green-600" />
                      <span>{formatNumber(dashboardData?.overview.total_units_produced || 0)} units</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Team Size</span>
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-purple-600" />
                      <span>{formatNumber(dashboardData?.overview.active_employees || 0)} employees</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Monthly Fixed Costs</span>
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-red-600" />
                      <span>{formatCurrency(dashboardData?.overview.monthly_fixed_costs || 0)}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Sales Tab */}
        <TabsContent value="sales" className="space-y-4">
          {salesData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Sales Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatNumber(salesData.totals.total_invoices)}</p>
                      <p className="text-sm text-gray-600">Total Invoices</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatCurrency(salesData.totals.total_revenue)}</p>
                      <p className="text-sm text-gray-600">Total Revenue</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatCurrency(salesData.totals.avg_invoice_value)}</p>
                      <p className="text-sm text-gray-600">Avg Invoice Value</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatNumber(salesData.totals.active_customers)}</p>
                      <p className="text-sm text-gray-600">Active Customers</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Invoice Status Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={salesData.status_breakdown}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ status, count }) => `${status}: ${count}`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="count"
                        >
                          {salesData.status_breakdown.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => formatNumber(value as number)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              <Card className="col-span-2">
                <CardHeader>
                  <CardTitle>Monthly Revenue Trend</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={salesData.monthly_trend}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip formatter={(value) => formatCurrency(value as number)} />
                        <Area type="monotone" dataKey="revenue" stroke="#8884d8" fill="#8884d8" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Operations Tab */}
        <TabsContent value="operations" className="space-y-4">
          {operationsData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Production Efficiency</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatNumber(operationsData.efficiency.total_orders)}</p>
                      <p className="text-sm text-gray-600">Total Orders</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatNumber(operationsData.efficiency.total_units_produced)}</p>
                      <p className="text-sm text-gray-600">Units Produced</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatNumber(operationsData.efficiency.total_units_ordered)}</p>
                      <p className="text-sm text-gray-600">Units Ordered</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold">{operationsData.efficiency.avg_efficiency?.toFixed(1)}%</p>
                      <p className="text-sm text-gray-600">Avg Efficiency</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Order Status Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={operationsData.status_breakdown}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="status" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="order_count" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              <Card className="col-span-2">
                <CardHeader>
                  <CardTitle>Top Products by Volume</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={operationsData.top_products}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="product_name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="total_produced" fill="#82ca9d" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Finance Tab */}
        <TabsContent value="finance" className="space-y-4">
          {financeData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Debt Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Total Loans:</span>
                      <span className="font-medium">{formatNumber(financeData.debt_summary.total_loans)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Outstanding:</span>
                      <span className="font-medium">{formatCurrency(financeData.debt_summary.total_outstanding)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Monthly Payments:</span>
                      <span className="font-medium">{formatCurrency(financeData.debt_summary.total_monthly_payments)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg Interest Rate:</span>
                      <span className="font-medium">{financeData.debt_summary.avg_interest_rate?.toFixed(2)}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Cash Flow by Type</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={financeData.cash_flow_by_type}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ transaction_type, total_amount }) => `${transaction_type}: ${formatCurrency(total_amount)}`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="transaction_count"
                        >
                          {financeData.cash_flow_by_type.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => formatNumber(value as number)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              <Card className="col-span-2">
                <CardHeader>
                  <CardTitle>Monthly Cash Flow</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={financeData.monthly_cash_flow}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip formatter={(value) => formatCurrency(value as number)} />
                        <Area type="monotone" dataKey="inflow" stackId="1" stroke="#82ca9d" fill="#82ca9d" />
                        <Area type="monotone" dataKey="outflow" stackId="1" stroke="#8884d8" fill="#8884d8" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* HR Tab */}
        <TabsContent value="hr" className="space-y-4">
          {hrData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Employee Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatNumber(hrData.employee_summary.total_employees)}</p>
                      <p className="text-sm text-gray-600">Total Employees</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatCurrency(hrData.employee_summary.avg_salary)}</p>
                      <p className="text-sm text-gray-600">Avg Salary</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold">{formatNumber(hrData.employee_summary.departments)}</p>
                      <p className="text-sm text-gray-600">Departments</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Department Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={hrData.department_breakdown}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="department" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="employee_count" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              <Card className="col-span-2">
                <CardHeader>
                  <CardTitle>Monthly Payroll Costs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={hrData.monthly_payroll}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip formatter={(value) => formatCurrency(value as number)} />
                        <Area type="monotone" dataKey="total_gross" stroke="#8884d8" fill="#8884d8" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Accounting Tab */}
        <TabsContent value="accounting" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Accounts Receivable</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Current</span>
                    <Badge variant="outline">Low Risk</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">1-30 days</span>
                    <Badge variant="outline">Medium Risk</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">31-60 days</span>
                    <Badge variant="outline">High Risk</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">60+ days</span>
                    <Badge variant="destructive">Critical</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Accounts Payable</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Due Today</span>
                    <Badge variant="destructive">Urgent</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Due This Week</span>
                    <Badge variant="outline">Important</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Due This Month</span>
                    <Badge variant="outline">Normal</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Due Later</span>
                    <Badge variant="outline">Low Priority</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}