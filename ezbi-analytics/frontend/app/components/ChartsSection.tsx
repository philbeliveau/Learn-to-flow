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
        labels: {
          color: '#ffffff',
          font: {
            weight: 300,
            size: 12
          }
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#ffffff',
        borderWidth: 1
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        },
        ticks: {
          color: '#ffffff',
          font: {
            weight: 300
          }
        },
        title: {
          display: true,
          color: '#ffffff',
          font: {
            weight: 300
          }
        },
      },
      y: {
        display: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        },
        ticks: {
          color: '#ffffff',
          font: {
            weight: 300
          }
        },
        title: {
          display: true,
          color: '#ffffff',
          font: {
            weight: 300
          }
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
        labels: {
          color: '#ffffff',
          font: {
            weight: 300,
            size: 12
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#ffffff',
        borderWidth: 1,
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
      <div className="w-full p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-white/10 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-80 bg-white/10"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full p-8 space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-light text-white">Analytics Dashboard</h2>
        <div className="flex gap-4">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="bg-black border border-white/30 text-white px-4 py-2 font-light"
            style={{backgroundColor: 'black'}}
          >
            <option value="1M">1 Mois</option>
            <option value="3M">3 Mois</option>
            <option value="6M">6 Mois</option>
            <option value="1Y">1 Année</option>
          </select>
          <select
            value={predictionDays}
            onChange={(e) => setPredictionDays(Number(e.target.value))}
            className="bg-black border border-white/30 text-white px-4 py-2 font-light"
            style={{backgroundColor: 'black'}}
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
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">
            Cash Flow Timeline - {timeframe}
          </h3>
          <div className="h-80">
            <Line data={cashFlowData} options={chartOptions} />
          </div>
          <p className="text-sm font-light text-white/70 mt-4">
            Analyse des flux de trésorerie basée sur plus de 203K enregistrements réels
          </p>
        </div>
      )}

      {/* Predictions Chart */}
      {predictionData && (
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">
            Prédictions Cash Flow - {predictionDays} jours
          </h3>
          <div className="h-80">
            <Line data={predictionData} options={chartOptions} />
          </div>
          <p className="text-sm font-light text-white/70 mt-4">
            Prédictions statistiques avec intervalles de confiance basées sur des données historiques réelles
          </p>
        </div>
      )}

      {/* Banking Trends Grid */}
      {bankingData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Company Comparison */}
          {bankingData.company_comparison && (
            <div className="bg-black border border-white/20 p-8">
              <h3 className="text-xl font-light text-white mb-6">
                {bankingData.company_comparison.title}
              </h3>
              <div className="h-80">
                <Bar 
                  data={{
                    labels: bankingData.company_comparison.labels,
                    datasets: [{
                      label: 'Cash Flow (€B)',
                      data: bankingData.company_comparison.data,
                      backgroundColor: '#74a6be',
                      borderColor: '#74a6be',
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
            <div className="bg-black border border-white/20 p-8">
              <h3 className="text-xl font-light text-white mb-6">
                Distribution des Flux de Trésorerie
              </h3>
              <div className="h-80">
                <Pie 
                  data={{
                    labels: bankingData.cash_flow_distribution.labels,
                    datasets: [{
                      data: bankingData.cash_flow_distribution.data,
                      backgroundColor: ['#74a6be', '#a7292e', '#ffffff', '#000000'],
                      borderColor: '#ffffff',
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Machine Performance */}
          {manufacturingData.machine_performance && (
            <div className="bg-black border border-white/20 p-8">
              <h3 className="text-xl font-light text-white mb-6">
                {manufacturingData.machine_performance.title}
              </h3>
              <div className="h-80">
                <Line data={manufacturingData.machine_performance} options={chartOptions} />
              </div>
              <p className="text-sm font-light text-white/70 mt-4">
                Suivi en temps réel basé sur plus de 14K lectures de capteurs
              </p>
            </div>
          )}

          {/* Temperature Monitoring */}
          {manufacturingData.temperature_monitoring && (
            <div className="bg-black border border-white/20 p-8">
              <h3 className="text-xl font-light text-white mb-6">
                {manufacturingData.temperature_monitoring.title}
              </h3>
              <div className="h-80">
                <Bar 
                  data={{
                    labels: manufacturingData.temperature_monitoring.labels,
                    datasets: [{
                      label: 'Température (°C)',
                      data: manufacturingData.temperature_monitoring.data,
                      backgroundColor: '#a7292e',
                      borderColor: '#a7292e',
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
            <div className="bg-black border border-white/20 p-8 col-span-full">
              <h3 className="text-xl font-light text-white mb-6">
                {manufacturingData.quality_control.title}
              </h3>
              <div className="h-80">
                <Bar data={manufacturingData.quality_control} options={chartOptions} />
              </div>
              <p className="text-sm font-light text-white/70 mt-4">
                Analyse de qualité : Valeurs réelles vs objectifs de consigne
              </p>
            </div>
          )}
        </div>
      )}

      {/* Data Source Information */}
      <div className="border border-white/20 p-6">
        <h4 className="text-lg font-light text-white mb-4">Sources de Données</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm font-light text-white/70">
          <div>
            <div className="text-white mb-1">Cash Flow</div>
            <div>203,331 enregistrements réels</div>
          </div>
          <div>
            <div className="text-white mb-1">Manufacturing</div>
            <div>14,088 lectures de capteurs</div>
          </div>
          <div>
            <div className="text-white mb-1">Companies</div>
            <div>4,714 entreprises mappées</div>
          </div>
          <div>
            <div className="text-white mb-1">Analytics</div>
            <div>Données authentiques EZBI</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartsSection;