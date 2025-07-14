'use client';

import React, { useState, useEffect } from 'react';
import { Line, Bar } from 'react-chartjs-2';

interface ManufacturingChartsProps {
  chartOptions: any;
}

const ManufacturingCharts: React.FC<ManufacturingChartsProps> = ({ chartOptions }) => {
  const [manufacturingData, setManufacturingData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadManufacturingData();
  }, []);

  const loadManufacturingData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

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
      console.error('Erreur lors du chargement des données de production:', error);
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

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-light text-white">Analyses de Production</h2>

      {/* Manufacturing KPIs */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-black border border-white/20 p-6">
          <div className="flex items-center gap-3 mb-4">
            <svg className="w-8 h-8" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            <h3 className="text-lg font-light text-white">Efficacité Globale</h3>
          </div>
          <p className="text-3xl font-light text-white mb-2">87.3%</p>
          <p className="text-sm font-light text-white/70">Amélioration de +2.1% ce mois</p>
        </div>

        <div className="bg-black border border-white/20 p-6">
          <div className="flex items-center gap-3 mb-4">
            <svg className="w-8 h-8" style={{color: '#a7292e'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
            <h3 className="text-lg font-light text-white">Qualité Production</h3>
          </div>
          <p className="text-3xl font-light text-white mb-2">96.8%</p>
          <p className="text-sm font-light text-white/70">Taux de défaut: 2.8%</p>
        </div>

        <div className="bg-black border border-white/20 p-6">
          <div className="flex items-center gap-3 mb-4">
            <svg className="w-8 h-8" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
            <h3 className="text-lg font-light text-white">Capacité Utilisée</h3>
          </div>
          <p className="text-3xl font-light text-white mb-2">84.7%</p>
          <p className="text-sm font-light text-white/70">1,247 unités produites</p>
        </div>
      </div>

      {/* Manufacturing Charts */}
      {manufacturingData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Machine Performance */}
          {manufacturingData.machine_performance && (
            <div className="bg-black border border-white/20 p-8">
              <h3 className="text-xl font-light text-white mb-6">
                Performance Machine
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
                Monitoring Température
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
              <p className="text-sm font-light text-white/70 mt-4">
                Surveillance thermique des équipements critiques
              </p>
            </div>
          )}
        </div>
      )}

      {/* Quality Control */}
      {manufacturingData?.quality_control && (
        <div className="bg-black border border-white/20 p-8">
          <h3 className="text-xl font-light text-white mb-6">
            Contrôle Qualité
          </h3>
          <div className="h-80">
            <Bar data={manufacturingData.quality_control} options={chartOptions} />
          </div>
          <p className="text-sm font-light text-white/70 mt-4">
            Analyse de qualité : Valeurs réelles vs objectifs de consigne
          </p>
        </div>
      )}

      {/* Production Metrics */}
      <div className="bg-black border border-white/20 p-8">
        <h3 className="text-xl font-light text-white mb-6">Métriques de Production</h3>
        <div className="grid md:grid-cols-4 gap-6">
          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#74a6be'}}>Rendement</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>OEE:</span>
                <span className="text-white">87.3%</span>
              </div>
              <div className="flex justify-between">
                <span>Disponibilité:</span>
                <span className="text-white">94.2%</span>
              </div>
              <div className="flex justify-between">
                <span>Performance:</span>
                <span className="text-white">92.7%</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Qualité</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Taux de qualité:</span>
                <span className="text-white">96.8%</span>
              </div>
              <div className="flex justify-between">
                <span>Défauts/heure:</span>
                <span className="text-white">0.3</span>
              </div>
              <div className="flex justify-between">
                <span>Reprises:</span>
                <span className="text-white">1.2%</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#74a6be'}}>Maintenance</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>MTBF:</span>
                <span className="text-white">156h</span>
              </div>
              <div className="flex justify-between">
                <span>MTTR:</span>
                <span className="text-white">2.4h</span>
              </div>
              <div className="flex justify-between">
                <span>Prédictive:</span>
                <span className="text-white">78%</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-lg font-light" style={{color: '#a7292e'}}>Énergie</h4>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Consommation:</span>
                <span className="text-white">2.4 MWh</span>
              </div>
              <div className="flex justify-between">
                <span>Efficacité:</span>
                <span className="text-white">89.2%</span>
              </div>
              <div className="flex justify-between">
                <span>Économies:</span>
                <span className="text-white">-12%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManufacturingCharts;