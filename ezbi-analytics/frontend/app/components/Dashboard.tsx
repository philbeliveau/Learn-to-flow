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
import OverviewChartsFixed from './charts/OverviewChartsFixed';
import FinancialChartsFixed from './charts/FinancialChartsFixed';
import ManufacturingCharts from './charts/ManufacturingCharts';
import ManufacturingChartsFixed from './charts/ManufacturingChartsFixed';
import PredictionsCharts from './charts/PredictionsCharts';
import AnalyticsChartsFixed from './charts/AnalyticsChartsFixed';
import ManufacturingDashboardSimple from './charts/ManufacturingDashboardSimple';
import RoleGuard, { CanWriteDashboard, CanWriteAnalytics, AdminOnly, ManagerOrHigher } from './auth/RoleGuard';
import { authService, User, UserRole, Permission } from '../services/authService';
import { cacheService, CACHE_KEYS } from '../services/cacheService';
import { syntheticDataService } from '../services/syntheticDataService';
import { robustApiService } from '../services/robustApiService';
import MobileResponsiveWrapper from './ui/MobileResponsiveWrapper';
import SystemHealthDashboard from './SystemHealthDashboard';

interface DashboardProps {
  user: User;
  onLogout: () => void;
  apiStatus: string;
}

export default function Dashboard({ user, onLogout, apiStatus }: DashboardProps) {
  const [kpis, setKpis] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [showHealthDashboard, setShowHealthDashboard] = useState(false);

  useEffect(() => {
    loadKPIs();
  }, []);

  const loadKPIs = async () => {
    try {
      // Use robust API service for optimized data loading
      const kpiResponse = await robustApiService.getCompanyKPIs();
      if (kpiResponse.success) {
        setKpis(kpiResponse.data);
      } else {
        console.error('Error loading KPIs:', kpiResponse.error);
      }
    } catch (error) {
      console.error('Error loading KPIs:', error);
    }
  };

  const generatePrediction = async () => {
    setLoading(true);
    try {
      // Use robust API service for predictions
      const predictionResponse = await robustApiService.getCashFlowPrediction(30);
      if (predictionResponse.success) {
        setPrediction(predictionResponse.data);
      } else {
        console.error('Error generating prediction:', predictionResponse.error);
      }
    } catch (error) {
      console.error('Error generating prediction:', error);
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
        return <OverviewChartsFixed kpis={kpis} />;
      case 'financial':
        return <FinancialChartsFixed chartOptions={chartOptions} pieChartOptions={pieChartOptions} />;
      case 'manufacturing':
        return <ManufacturingChartsFixed chartOptions={chartOptions} pieChartOptions={pieChartOptions} />;
      case 'manufacturing-bi':
        return <ManufacturingDashboardSimple />;
      case 'predictions':
        return <PredictionsCharts chartOptions={chartOptions} pieChartOptions={pieChartOptions} />;
      case 'analytics':
        return <AnalyticsChartsFixed chartOptions={chartOptions} pieChartOptions={pieChartOptions} />;
      default:
        return <OverviewChartsFixed kpis={kpis} />;
    }
  };

  return (
    <MobileResponsiveWrapper>
      <div className="min-h-screen bg-black text-white font-light">
        {/* Navigation Sidebar */}
        <NavigationSidebar activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Main Content */}
        <div className="ml-0 md:ml-64">
        {/* Header */}
        <header className="bg-black border-b border-white/20 sticky top-0 z-30">
          <div className="px-8 py-6">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-xl font-light text-white">Welcome, {user?.name || 'User'}</h1>
                <div className="flex items-center gap-3">
                  <p className="text-sm font-light text-white/70">{user?.company?.name || 'EZBI Analytics'}</p>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    user?.role === UserRole.ADMIN ? 'bg-red-500/20 text-red-300' :
                    user?.role === UserRole.MANAGER ? 'bg-blue-500/20 text-blue-300' :
                    user?.role === UserRole.ANALYST ? 'bg-green-500/20 text-green-300' :
                    'bg-gray-500/20 text-gray-300'
                  }`}>
                    {user?.role?.toUpperCase()}
                  </span>
                  {user?.is_mfa_enabled && (
                    <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-300">
                      MFA
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-6 items-center">
                {/* API Status */}
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    apiStatus === 'online' ? 'bg-green-500' : 
                    apiStatus === 'offline' ? 'bg-red-500' : 
                    'bg-yellow-500 animate-pulse'
                  }`}></div>
                  <span className="text-sm font-light text-white/80">
                    {apiStatus === 'online' ? 'System Online' : 
                     apiStatus === 'offline' ? 'System Offline' : 
                     'Checking...'}
                  </span>
                </div>
                
                {/* Role-based actions */}
                <AdminOnly>
                  <button 
                    onClick={() => setShowHealthDashboard(true)}
                    className="border border-white/30 hover:border-white/60 text-white px-3 py-1 text-sm font-light transition-colors"
                    style={{backgroundColor: 'transparent'}}
                  >
                    System Health
                  </button>
                  <button 
                    onClick={() => {
                      cacheService.clear();
                      robustApiService.clearCache();
                    }}
                    className="border border-white/30 hover:border-white/60 text-white px-3 py-1 text-sm font-light transition-colors"
                    style={{backgroundColor: 'transparent'}}
                  >
                    Clear Cache
                  </button>
                </AdminOnly>
                
                <button 
                  onClick={onLogout}
                  className="border border-white/30 hover:border-white/60 text-white px-4 py-2 font-light transition-colors"
                  style={{backgroundColor: 'transparent'}}
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="p-4 md:p-8">
          {renderActiveTab()}
        </div>
      </div>
    </div>
    
    {/* System Health Dashboard */}
    <SystemHealthDashboard 
      isVisible={showHealthDashboard}
      onClose={() => setShowHealthDashboard(false)}
    />
    </MobileResponsiveWrapper>
  );
}