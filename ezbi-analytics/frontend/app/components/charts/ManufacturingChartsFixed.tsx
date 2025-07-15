'use client';

import React, { useState, useEffect } from 'react';
import { Bar, Line, Pie } from 'react-chartjs-2';
import { formatCurrency } from '../../services/syntheticDataService';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface ManufacturingChartsProps {
  chartOptions: any;
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

interface ProductsData {
  products: Array<{
    product_id: number;
    product_name: string;
    product_code: string;
    base_cost: number;
    labor_hours: number;
    material_cost: number;
    total_orders: number;
    total_units_produced: number;
  }>;
}

interface ProductionOrdersData {
  orders: Array<{
    order_id: number;
    order_number: string;
    product_name: string;
    company_name: string;
    status: string;
    units_ordered: number;
    units_produced: number;
    cost_of_goods_sold: number;
    labor_cost: number;
    material_cost: number;
    start_date: string;
    completion_date: string;
  }>;
}

const ManufacturingChartsFixed: React.FC<ManufacturingChartsProps> = ({ chartOptions }) => {
  const [operationsData, setOperationsData] = useState<OperationsData | null>(null);
  const [productsData, setProductsData] = useState<ProductsData | null>(null);
  const [ordersData, setOrdersData] = useState<ProductionOrdersData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadManufacturingData();
  }, []);

  const loadManufacturingData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch all manufacturing data from operations tables
      const [operationsRes, productsRes, ordersRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/manufacturing/operations/kpis`),
        fetch(`${API_BASE_URL}/api/manufacturing/operations/products`),
        fetch(`${API_BASE_URL}/api/manufacturing/operations/production-orders`)
      ]);

      if (!operationsRes.ok || !productsRes.ok || !ordersRes.ok) {
        throw new Error('Failed to fetch manufacturing data');
      }

      const [operations, products, orders] = await Promise.all([
        operationsRes.json(),
        productsRes.json(),
        ordersRes.json()
      ]);

      setOperationsData(operations);
      setProductsData(products);
      setOrdersData(orders);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load manufacturing data');
      console.error('Failed to load manufacturing data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('fr-FR').format(num);
  };

  // Generate chart data for order status breakdown
  const getOrderStatusChart = () => {
    if (!operationsData) return null;
    
    return {
      labels: operationsData.status_breakdown.map(item => item.status),
      datasets: [{
        label: 'Nombre de commandes',
        data: operationsData.status_breakdown.map(item => item.order_count),
        backgroundColor: [
          '#10B981',
          '#F59E0B',
          '#EF4444',
          '#3B82F6',
          '#8B5CF6'
        ],
        borderColor: '#ffffff',
        borderWidth: 1
      }]
    };
  };

  // Generate chart data for top products
  const getTopProductsChart = () => {
    if (!operationsData) return null;
    
    return {
      labels: operationsData.top_products.map(item => item.product_name),
      datasets: [{
        label: 'Unités produites',
        data: operationsData.top_products.map(item => item.total_produced),
        backgroundColor: '#3B82F6',
        borderColor: '#ffffff',
        borderWidth: 1
      }]
    };
  };

  // Generate chart data for product costs
  const getProductCostsChart = () => {
    if (!productsData) return null;
    
    const topProducts = productsData.products
      .sort((a, b) => b.total_units_produced - a.total_units_produced)
      .slice(0, 10);
    
    return {
      labels: topProducts.map(item => item.product_name),
      datasets: [
        {
          label: 'Coût matières',
          data: topProducts.map(item => item.material_cost),
          backgroundColor: '#EF4444',
          borderColor: '#ffffff',
          borderWidth: 1
        },
        {
          label: 'Coût main-d\'œuvre',
          data: topProducts.map(item => item.labor_hours * 50), // Assuming 50€/hour
          backgroundColor: '#F59E0B',
          borderColor: '#ffffff',
          borderWidth: 1
        },
        {
          label: 'Coût de base',
          data: topProducts.map(item => item.base_cost),
          backgroundColor: '#10B981',
          borderColor: '#ffffff',
          borderWidth: 1
        }
      ]
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
          onClick={loadManufacturingData}
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
        <h2 className="text-2xl font-light text-white">Production</h2>
        <div className="flex gap-2">
          <span className="bg-blue-600 px-3 py-1 rounded-full text-sm">Operations Tables</span>
          <span className="bg-green-600 px-3 py-1 rounded-full text-sm">Live Data</span>
        </div>
      </div>

      {/* Production Summary Cards */}
      {operationsData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Commandes totales</h3>
            <p className="text-2xl font-light text-white">{formatNumber(operationsData.efficiency.total_orders)}</p>
            <p className="text-xs text-white/50">Ordres de production</p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Unités produites</h3>
            <p className="text-2xl font-light text-white">{formatNumber(operationsData.efficiency.total_units_produced)}</p>
            <p className="text-xs text-white/50">Production réalisée</p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Unités commandées</h3>
            <p className="text-2xl font-light text-white">{formatNumber(operationsData.efficiency.total_units_ordered)}</p>
            <p className="text-xs text-white/50">Demande totale</p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
            <h3 className="text-sm font-light text-white/70">Efficacité</h3>
            <p className="text-2xl font-light text-white">{operationsData.efficiency.avg_efficiency?.toFixed(1)}%</p>
            <p className="text-xs text-white/50">Moyenne générale</p>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Order Status Distribution */}
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
          <h3 className="text-lg font-light text-white mb-4">Répartition des commandes</h3>
          <div className="h-64">
            {getOrderStatusChart() && (
              <Pie data={getOrderStatusChart()!} options={chartOptions} />
            )}
          </div>
        </div>

        {/* Top Products by Volume */}
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
          <h3 className="text-lg font-light text-white mb-4">Produits les plus produits</h3>
          <div className="h-64">
            {getTopProductsChart() && (
              <Bar data={getTopProductsChart()!} options={chartOptions} />
            )}
          </div>
        </div>

        {/* Product Costs Breakdown */}
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20 col-span-1 lg:col-span-2">
          <h3 className="text-lg font-light text-white mb-4">Répartition des coûts par produit</h3>
          <div className="h-64">
            {getProductCostsChart() && (
              <Bar data={getProductCostsChart()!} options={chartOptions} />
            )}
          </div>
        </div>
      </div>

      {/* Products Overview */}
      {productsData && (
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
          <h3 className="text-lg font-light text-white mb-4">Aperçu des produits</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-light text-white">{formatNumber(productsData.products.length)}</p>
              <p className="text-sm text-white/70">Produits au catalogue</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-light text-white">
                {formatCurrency(productsData.products.reduce((sum, p) => sum + p.base_cost, 0) / productsData.products.length)}
              </p>
              <p className="text-sm text-white/70">Coût moyen</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-light text-white">
                {formatNumber(productsData.products.reduce((sum, p) => sum + p.total_units_produced, 0))}
              </p>
              <p className="text-sm text-white/70">Total produit</p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Production Orders */}
      <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
        <h3 className="text-lg font-light text-white mb-4">Commandes récentes</h3>
        <div className="space-y-3">
          {ordersData?.orders.slice(0, 8).map((order, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${
                  order.status === 'Completed' ? 'bg-green-400' : 
                  order.status === 'In Progress' ? 'bg-blue-400' : 
                  'bg-yellow-400'
                }`}></div>
                <div>
                  <p className="text-white font-medium">{order.order_number}</p>
                  <p className="text-white/60 text-sm">{order.product_name} • {order.company_name}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-white font-medium">{formatNumber(order.units_produced)}/{formatNumber(order.units_ordered)}</p>
                <p className="text-white/60 text-sm">{order.status}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Production Efficiency Breakdown */}
      {operationsData && (
        <div className="bg-gray-800 p-6 rounded-lg border border-white/20">
          <h3 className="text-lg font-light text-white mb-4">Efficacité par statut</h3>
          <div className="space-y-3">
            {operationsData.status_breakdown.map((status, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
                <div>
                  <p className="text-white font-medium">{status.status}</p>
                  <p className="text-white/60 text-sm">{formatNumber(status.order_count)} commandes</p>
                </div>
                <div className="text-right">
                  <p className="text-white">{formatNumber(status.units_produced)}/{formatNumber(status.units_ordered)}</p>
                  <p className="text-white/60 text-sm">
                    {status.units_ordered > 0 ? ((status.units_produced / status.units_ordered) * 100).toFixed(1) : 0}% d'efficacité
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Source Info */}
      <div className="bg-blue-900/20 border border-blue-500 p-4 rounded-lg">
        <h4 className="text-blue-400 font-medium mb-2">Source des données</h4>
        <p className="text-blue-300 text-sm">
          ✅ Connecté aux tables operations_products, operations_production_orders • 
          {productsData && `${formatNumber(productsData.products.length)} produits • `}
          {ordersData && `${formatNumber(ordersData.orders.length)} commandes • `}
          Données manufacturières en temps réel
        </p>
      </div>
    </div>
  );
};

export default ManufacturingChartsFixed;