'use client';

import { useState, useEffect } from 'react';
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

import NavigationSidebar from './NavigationSidebar';
import OverviewCharts from './charts/OverviewCharts';
import FinancialCharts from './charts/FinancialCharts';
import ManufacturingCharts from './charts/ManufacturingCharts';
import CashFlowPredictionDashboard from './charts/CashFlowPredictionDashboard';
import AnalyticsCharts from './charts/AnalyticsCharts';
import ManufacturingDashboardSimple from './charts/ManufacturingDashboardSimple';

interface DashboardProps {
  user: any;
  onLogout: () => void;
  apiStatus: string;
}

export default function Dashboard({ user, onLogout, apiStatus }: DashboardProps) {
  const [kpis, setKpis] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadKPIs();
  }, []);

  const loadKPIs = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8004/api/v1/company/kpis', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setKpis(data);
      }
    } catch (error) {
      console.error('Erreur KPIs:', error);
    }
  };

  const generatePrediction = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8004/api/v1/predictions/cashflow', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          revenue: 150000, 
          expenses: 112500, 
          period_days: 30,
          model: "statistical"
        })
      });
      if (response.ok) {
        const data = await response.json();
        setPrediction(data);
      } else {
        console.error('Prediction API error:', response.statusText);
      }
    } catch (error) {
      console.error('Erreur prédiction:', error);
    } finally {
      setLoading(false);
    }
  };

  // Chart options configuration
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

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewCharts kpis={kpis} />;
      case 'financial':
        return <FinancialCharts chartOptions={chartOptions} pieChartOptions={pieChartOptions} />;
      case 'manufacturing':
        return <ManufacturingCharts chartOptions={chartOptions} />;
      case 'manufacturing-bi':
        return <ManufacturingDashboardSimple />;
      case 'predictions':
        return <CashFlowPredictionDashboard 
          chartOptions={chartOptions} 
          pieChartOptions={pieChartOptions}
        />;
      case 'analytics':
        return <AnalyticsCharts chartOptions={chartOptions} pieChartOptions={pieChartOptions} />;
      default:
        return <OverviewCharts kpis={kpis} />;
    }
  };

  return (
    <div className="min-h-screen bg-black text-white font-light">
      {/* Navigation Sidebar */}
      <NavigationSidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content */}
      <div className="ml-64">
        {/* Header */}
        <header className="bg-black border-b border-white/20 sticky top-0 z-30">
          <div className="px-8 py-6">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-xl font-light text-white">Bonjour, {user?.name || 'Utilisateur'}</h1>
                <p className="text-sm font-light text-white/70">{user?.company?.name || 'EZBI Analytics'}</p>
              </div>
              <div className="flex gap-6 items-center">
                {/* API Status */}
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    apiStatus === 'online' ? 'bg-white' : 
                    apiStatus === 'offline' ? 'bg-white/30' : 
                    'bg-white/60 animate-pulse'
                  }`}></div>
                  <span className="text-sm font-light text-white/80">
                    {apiStatus === 'online' ? 'Système en ligne' : 
                     apiStatus === 'offline' ? 'Hors ligne' : 
                     'Vérification...'}
                  </span>
                </div>
                <button 
                  onClick={onLogout}
                  className="border border-white/30 hover:border-white/60 text-white px-4 py-2 font-light transition-colors"
                  style={{backgroundColor: 'transparent'}}
                >
                  Déconnexion
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="p-8">
          {renderActiveTab()}
        </div>
      </div>
    </div>
  );
}