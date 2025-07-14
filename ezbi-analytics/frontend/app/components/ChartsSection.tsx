'use client';

import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement
);

interface ChartData {
  labels: string[];
  datasets: any[];
}

const ChartsSection: React.FC = () => {
  const [cashFlowData, setCashFlowData] = useState<ChartData | null>(null);
  const [predictionData, setPredictionData] = useState<ChartData | null>(null);
  const [bankingData, setBankingData] = useState<any>(null);
  const [manufacturingData, setManufacturingData] = useState<any>(null);
  const [timeframe, setTimeframe] = useState('6M');
  const [predictionDays, setPredictionDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadChartsData();
  }, [timeframe, predictionDays]);

  const loadChartsData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load cash flow timeline
      const cashFlowResponse = await fetch(
        `http://localhost:8004/api/v1/analytics/cash-flow-timeline?timeframe=${timeframe}`,
        { headers }
      );
      if (cashFlowResponse.ok) {
        const cashFlowResult = await cashFlowResponse.json();
        setCashFlowData(cashFlowResult.chart_data);
      }

      // Load predictions
      const predictionResponse = await fetch(
        `http://localhost:8004/api/v1/analytics/predictions-chart?days_ahead=${predictionDays}`,
        { headers }
      );
      if (predictionResponse.ok) {
        const predictionResult = await predictionResponse.json();
        setPredictionData(predictionResult.chart_data);
      }

      // Load banking trends
      const bankingResponse = await fetch(
        'http://localhost:8004/api/v1/analytics/banking-trends',
        { headers }
      );
      if (bankingResponse.ok) {
        const bankingResult = await bankingResponse.json();
        setBankingData(bankingResult.charts);
      }

      // Load manufacturing dashboard
      const manufacturingResponse = await fetch(
        'http://localhost:8004/api/v1/analytics/manufacturing-dashboard',
        { headers }
      );
      if (manufacturingResponse.ok) {
        const manufacturingResult = await manufacturingResponse.json();
        setManufacturingData(manufacturingResult.dashboards);
      }

    } catch (error) {
      console.error('Erreur lors du chargement des graphiques:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
        },
      },
      y: {
        display: true,
        title: {
          display: true,
        },
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
  };

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const label = context.label || '';
            const value = context.formattedValue;
            return `${label}: €${value}B`;
          }
        }
      }
    },
  };

  if (loading) {
    return (
      <div className="w-full p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-80 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Analytics Dashboard</h2>
        <div className="flex gap-4">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="1M">1 Mois</option>
            <option value="3M">3 Mois</option>
            <option value="6M">6 Mois</option>
            <option value="1Y">1 Année</option>
          </select>
          <select
            value={predictionDays}
            onChange={(e) => setPredictionDays(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value={7}>7 jours</option>
            <option value={15}>15 jours</option>
            <option value={30}>30 jours</option>
            <option value={60}>60 jours</option>
          </select>
        </div>
      </div>

      {/* Cash Flow Timeline */}
      {cashFlowData && (
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h3 className="text-xl font-semibold mb-4">
            Cash Flow Timeline - {timeframe}
          </h3>
          <div className="h-80">
            <Line data={cashFlowData} options={chartOptions} />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Analyse des flux de trésorerie basée sur plus de 203K enregistrements réels
          </p>
        </div>
      )}

      {/* Predictions Chart */}
      {predictionData && (
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h3 className="text-xl font-semibold mb-4">
            Prédictions Cash Flow - {predictionDays} jours
          </h3>
          <div className="h-80">
            <Line data={predictionData} options={chartOptions} />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Prédictions ML avec intervalles de confiance basées sur des données historiques réelles
          </p>
        </div>
      )}

      {/* Banking Trends Grid */}
      {bankingData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Company Comparison */}
          {bankingData.company_comparison && (
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-xl font-semibold mb-4">
                {bankingData.company_comparison.title}
              </h3>
              <div className="h-80">
                <Bar 
                  data={{
                    labels: bankingData.company_comparison.labels,
                    datasets: [{
                      label: 'Cash Flow (€B)',
                      data: bankingData.company_comparison.data,
                      backgroundColor: 'rgba(59, 130, 246, 0.8)',
                      borderColor: 'rgba(59, 130, 246, 1)',
                      borderWidth: 1
                    }]
                  }} 
                  options={chartOptions} 
                />
              </div>
            </div>
          )}

          {/* Cash Flow Distribution */}
          {bankingData.cash_flow_distribution && (
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-xl font-semibold mb-4">
                Distribution des Flux de Trésorerie
              </h3>
              <div className="h-80">
                <Pie 
                  data={{
                    labels: bankingData.cash_flow_distribution.labels,
                    datasets: [{
                      data: bankingData.cash_flow_distribution.data,
                      backgroundColor: bankingData.cash_flow_distribution.backgroundColor,
                      borderWidth: 2
                    }]
                  }} 
                  options={pieChartOptions} 
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Manufacturing Dashboard */}
      {manufacturingData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Machine Performance */}
          {manufacturingData.machine_performance && (
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-xl font-semibold mb-4">
                {manufacturingData.machine_performance.title}
              </h3>
              <div className="h-80">
                <Line data={manufacturingData.machine_performance} options={chartOptions} />
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Suivi en temps réel basé sur plus de 14K lectures de capteurs
              </p>
            </div>
          )}

          {/* Temperature Monitoring */}
          {manufacturingData.temperature_monitoring && (
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-xl font-semibold mb-4">
                {manufacturingData.temperature_monitoring.title}
              </h3>
              <div className="h-80">
                <Bar 
                  data={{
                    labels: manufacturingData.temperature_monitoring.labels,
                    datasets: [{
                      label: 'Température (°C)',
                      data: manufacturingData.temperature_monitoring.data,
                      backgroundColor: manufacturingData.temperature_monitoring.backgroundColor,
                      borderWidth: 1
                    }]
                  }} 
                  options={chartOptions} 
                />
              </div>
            </div>
          )}

          {/* Quality Control */}
          {manufacturingData.quality_control && (
            <div className="bg-white p-6 rounded-lg shadow-lg col-span-full">
              <h3 className="text-xl font-semibold mb-4">
                {manufacturingData.quality_control.title}
              </h3>
              <div className="h-80">
                <Bar data={manufacturingData.quality_control} options={chartOptions} />
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Analyse de qualité : Valeurs réelles vs objectifs de consigne
              </p>
            </div>
          )}
        </div>
      )}

      {/* Data Source Information */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h4 className="font-semibold text-blue-800 mb-2">Sources de Données</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-blue-700">
          <div>
            <strong>Cash Flow:</strong><br />
            203,331 enregistrements réels
          </div>
          <div>
            <strong>Manufacturing:</strong><br />
            14,088 lectures de capteurs
          </div>
          <div>
            <strong>Companies:</strong><br />
            4,714 entreprises mappées
          </div>
          <div>
            <strong>Analytics:</strong><br />
            Données authentiques EZBI
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartsSection;