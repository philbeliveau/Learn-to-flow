'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Settings,
  Bell,
  User,
  Menu,
  X,
  Search,
  Filter,
  Download,
  RefreshCw,
  Zap,
  Activity,
  Database,
  Target
} from 'lucide-react';
import { useAuthStore, useDashboardStore, usePredictionStore, useDataStore, useUIStore } from '@/store';
import { cn } from '@/lib/utils';
import { PredictionCard } from '@/components/ui/prediction-card';
import { SmartUploadZone } from '@/components/ui/smart-upload-zone';
import { ConfidenceIndicator } from '@/components/ui/confidence-indicator';
import toast from 'react-hot-toast';

const navigationItems = [
  { id: 'overview', label: 'Vue d\'ensemble', icon: BarChart3 },
  { id: 'analytics', label: 'Analyses', icon: TrendingUp },
  { id: 'models', label: 'Modèles IA', icon: Target },
  { id: 'alerts', label: 'Alertes', icon: AlertTriangle },
];

const mockPredictions = [
  {
    id: '1',
    modelId: 'quality-001',
    modelName: 'Prédiction Qualité',
    modelVersion: '2.1',
    predictionType: 'quality' as const,
    confidence: 0.92,
    result: {
      prediction: 0.95,
      probability: 0.92,
      alternatives: [
        { value: 0.87, probability: 0.08 }
      ]
    },
    inputData: {} as any,
    timestamp: new Date(),
    processingTime: 145,
    features: {},
    explanation: {
      topFeatures: [
        { feature: 'Température', importance: 0.8, direction: 'positive' },
        { feature: 'Pression', importance: 0.6, direction: 'negative' },
        { feature: 'Humidité', importance: 0.4, direction: 'positive' }
      ],
      reasoning: 'La température optimale et l\'humidité stable indiquent une qualité élevée'
    }
  },
  {
    id: '2',
    modelId: 'maintenance-001',
    modelName: 'Prédiction Maintenance',
    modelVersion: '1.8',
    predictionType: 'maintenance' as const,
    confidence: 0.78,
    result: {
      prediction: 'Maintenance requise dans 7 jours',
      probability: 0.78
    },
    inputData: {} as any,
    timestamp: new Date(Date.now() - 3600000),
    processingTime: 287,
    features: {},
  },
  {
    id: '3',
    modelId: 'anomaly-001',
    modelName: 'Détection d\'Anomalies',
    modelVersion: '3.0',
    predictionType: 'anomaly' as const,
    confidence: 0.95,
    result: {
      prediction: false,
      probability: 0.95
    },
    inputData: {} as any,
    timestamp: new Date(Date.now() - 7200000),
    processingTime: 92,
    features: {},
  }
];

export function Dashboard() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  const { user, logout } = useAuthStore();
  const { currentView, setCurrentView } = useDashboardStore();
  const { predictions, fetchPredictions } = usePredictionStore();
  const { manufacturingData, fetchData } = useDataStore();
  const { sidebarCollapsed, setSidebarCollapsed, notifications } = useUIStore();

  useEffect(() => {
    // Simulate data fetching
    const timer = setTimeout(() => {
      // fetchPredictions();
      // fetchData();
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const handleLogout = () => {
    logout();
    toast.success('Déconnexion réussie');
  };

  const handleUpload = (files: File[]) => {
    toast.success(`${files.length} fichier(s) téléchargé(s)`);
  };

  const handleDataParsed = (data: any[]) => {
    toast.success(`${data.length} enregistrements traités`);
  };

  const handlePredictionDetails = (prediction: any) => {
    toast.info(`Détails de la prédiction: ${prediction.modelName}`);
  };

  const handlePredictionRerun = (predictionId: string) => {
    toast.success('Prédiction relancée');
  };

  const renderContent = () => {
    switch (currentView) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="card"
              >
                <div className="card-body">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Prédictions actives
                      </p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {mockPredictions.length}
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                      <Target className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
                className="card"
              >
                <div className="card-body">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Confiance moyenne
                      </p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        88%
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                      <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                    </div>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
                className="card"
              >
                <div className="card-body">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Alertes actives
                      </p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        2
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg flex items-center justify-center">
                      <AlertTriangle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                    </div>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.3 }}
                className="card"
              >
                <div className="card-body">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Données traitées
                      </p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        1.2K
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                      <Database className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Recent Predictions */}
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Prédictions récentes
                </h2>
              </div>
              <div className="card-body">
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                  {mockPredictions.map((prediction) => (
                    <PredictionCard
                      key={prediction.id}
                      prediction={prediction}
                      onDetailsClick={handlePredictionDetails}
                      onRerun={handlePredictionRerun}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'analytics':
        return (
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Téléchargement de données
                </h2>
              </div>
              <div className="card-body">
                <SmartUploadZone
                  onFileUpload={handleUpload}
                  onDataParsed={handleDataParsed}
                />
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Analyse des données
                </h2>
              </div>
              <div className="card-body">
                <div className="text-center py-12">
                  <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">
                    Téléchargez des données pour commencer l'analyse
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'models':
        return (
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Modèles d'IA disponibles
                </h2>
              </div>
              <div className="card-body">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {mockPredictions.map((prediction) => (
                    <div key={prediction.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {prediction.modelName}
                        </h3>
                        <ConfidenceIndicator
                          confidence={prediction.confidence}
                          size="sm"
                        />
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        Version {prediction.modelVersion}
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {prediction.predictionType}
                        </span>
                        <button className="btn btn-outline btn-sm">
                          Utiliser
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'alerts':
        return (
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Alertes du système
                </h2>
              </div>
              <div className="card-body">
                <div className="space-y-4">
                  <div className="flex items-start gap-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        Maintenance préventive recommandée
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        La ligne de production A nécessite une maintenance dans 7 jours
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        Il y a 2 heures
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-400 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        Anomalie détectée
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Température élevée sur le capteur B12
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        Il y a 5 heures
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div className={cn(
        'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-8 h-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              EZBI
            </span>
          </div>
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="mt-5 px-2">
          <div className="space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setCurrentView(item.id as any);
                    setIsSidebarOpen(false);
                  }}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors',
                    currentView === item.id
                      ? 'bg-primary-100 text-primary-900 dark:bg-primary-900/20 dark:text-primary-100'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </button>
              );
            })}
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between h-16 px-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 w-64 text-sm bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 relative">
              <Bell className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full" />
              )}
            </button>

            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-primary-600 dark:text-primary-400" />
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {user?.firstName} {user?.lastName}
              </span>
            </div>

            <button
              onClick={handleLogout}
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              Déconnexion
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">
          {renderContent()}
        </main>
      </div>

      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
    </div>
  );
}