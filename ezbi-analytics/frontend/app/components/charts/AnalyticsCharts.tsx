'use client';

import React, { useState, useEffect } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';

interface AnalyticsChartsProps {
  chartOptions: any;
  pieChartOptions: any;
}

const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ chartOptions, pieChartOptions }) => {
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Simulate loading comprehensive analytics data
      // In a real app, this would load from multiple endpoints
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setAnalyticsData({
        loaded: true
      });

    } catch (error) {
      console.error('Erreur lors du chargement des analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-8">
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

  // Sample data for analytics charts
  const performanceData = {
    labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun'],
    datasets: [{
      label: 'Performance Globale (%)',
      data: [85, 87, 89, 86, 91, 88],
      borderColor: '#74a6be',
      backgroundColor: 'rgba(116, 166, 190, 0.1)',
      borderWidth: 2,
      fill: true
    }]
  };

  const efficiencyData = {
    labels: ['Processus A', 'Processus B', 'Processus C', 'Processus D'],
    datasets: [{
      label: 'Efficacité (%)',
      data: [92, 87, 94, 89],
      backgroundColor: '#a7292e',
      borderColor: '#a7292e',
      borderWidth: 1
    }]
  };

  const distributionData = {
    labels: ['Excellent', 'Bon', 'Moyen', 'À améliorer'],
    datasets: [{
      data: [45, 30, 20, 5],
      backgroundColor: ['#74a6be', '#a7292e', '#ffffff', '#000000'],
      borderColor: '#ffffff',
      borderWidth: 2
    }]
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-light text-white">Analytics Avancées</h2>

      {/* Performance Overview */}
      <div className="bg-black border border-white/20 p-8">
        <h3 className="text-xl font-light text-white mb-6">Performance Globale</h3>
        <div className="h-80">
          <Line data={performanceData} options={chartOptions} />
        </div>
        <p className="text-sm font-light text-white/70 mt-4">
          Évolution de la performance système sur les 6 derniers mois
        </p>
      </div>

      {/* Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Process Efficiency */}
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">
            Efficacité par Processus
          </h3>
          <div className="h-80">
            <Bar data={efficiencyData} options={chartOptions} />
          </div>
          <p className="text-sm font-light text-white/70 mt-4">
            Comparaison de l'efficacité des différents processus métier
          </p>
        </div>

        {/* Quality Distribution */}
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">
            Distribution Qualité
          </h3>
          <div className="h-80">
            <Pie data={distributionData} options={pieChartOptions} />
          </div>
          <p className="text-sm font-light text-white/70 mt-4">
            Répartition des niveaux de qualité dans l'organisation
          </p>
        </div>
      </div>

      {/* Data Intelligence */}
      <div className="bg-black border border-white/20 p-8">
        <h3 className="text-xl font-light text-white mb-6">Intelligence des Données</h3>
        <div className="grid md:grid-cols-4 gap-6">
          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#74a6be'}}>Sources</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Cash Flow:</span>
                <span className="text-white">203,331</span>
              </div>
              <div className="flex justify-between">
                <span>Capteurs IoT:</span>
                <span className="text-white">14,088</span>
              </div>
              <div className="flex justify-between">
                <span>Entreprises:</span>
                <span className="text-white">4,714</span>
              </div>
              <div className="flex justify-between">
                <span>Économies:</span>
                <span className="text-white">1,001</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Traitement</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Algorithmes:</span>
                <span className="text-white">27+</span>
              </div>
              <div className="flex justify-between">
                <span>Modèles IA:</span>
                <span className="text-white">Neural</span>
              </div>
              <div className="flex justify-between">
                <span>WASM SIMD:</span>
                <span className="text-white">Activé</span>
              </div>
              <div className="flex justify-between">
                <span>Optimisation:</span>
                <span className="text-white">Auto</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#74a6be'}}>Performance</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Vitesse:</span>
                <span className="text-white">2.8-4.4x</span>
              </div>
              <div className="flex justify-between">
                <span>Précision:</span>
                <span className="text-white">84.8%</span>
              </div>
              <div className="flex justify-between">
                <span>Tokens réduits:</span>
                <span className="text-white">32.3%</span>
              </div>
              <div className="flex justify-between">
                <span>Latence:</span>
                <span className="text-white">&lt; 200ms</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Insights</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Anomalies:</span>
                <span className="text-white">3 détectées</span>
              </div>
              <div className="flex justify-between">
                <span>Tendances:</span>
                <span className="text-white">7 identifiées</span>
              </div>
              <div className="flex justify-between">
                <span>Recommandations:</span>
                <span className="text-white">12 actives</span>
              </div>
              <div className="flex justify-between">
                <span>Alertes:</span>
                <span className="text-white">0 critiques</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* System Architecture */}
      <div className="bg-black border border-white/20 p-8">
        <h3 className="text-xl font-light text-white mb-6">Architecture Système</h3>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="space-y-4">
            <h4 className="text-lg font-light" style={{color: '#74a6be'}}>Claude Flow Core</h4>
            <div className="space-y-3 text-sm font-light text-white/70">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Swarm Orchestration</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Neural Networks</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Memory Management</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>GitHub Integration</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Data Pipeline</h4>
            <div className="space-y-3 text-sm font-light text-white/70">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Real-time Ingestion</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Data Validation</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Statistical Analysis</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Visualization Engine</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-lg font-light" style={{color: '#74a6be'}}>Security & Scale</h4>
            <div className="space-y-3 text-sm font-light text-white/70">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>JWT Authentication</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Auto-scaling</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Load Balancing</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-white"></div>
                <span>Health Monitoring</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Monitoring */}
      <div className="bg-black border border-white/20 p-8">
        <h3 className="text-xl font-light text-white mb-6">Monitoring Temps Réel</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { label: 'CPU Usage', value: '23%', color: '#74a6be' },
            { label: 'Memory', value: '1.2GB', color: '#a7292e' },
            { label: 'Active Users', value: '47', color: '#74a6be' },
            { label: 'API Calls/min', value: '1,234', color: '#a7292e' }
          ].map((metric, idx) => (
            <div key={idx} className="text-center">
              <div className="text-2xl font-light text-white mb-2">{metric.value}</div>
              <div className="text-sm font-light" style={{color: metric.color}}>{metric.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsCharts;