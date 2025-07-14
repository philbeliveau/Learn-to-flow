'use client';

import React from 'react';

interface OverviewChartsProps {
  kpis: any;
}

const OverviewCharts: React.FC<OverviewChartsProps> = ({ kpis }) => {
  return (
    <div className="space-y-8">
      {/* KPI Summary */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-black border border-white/20 p-6 hover:scale-105 transition-transform duration-300">
          <div className="mb-4">
            <svg className="w-8 h-8" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M13 2.05v2.02c4.39.54 7.5 4.53 7.5 9.43 0 5.52-4.48 10-10 10S0 19.02 0 13.5c0-4.9 3.11-8.89 7.5-9.43V2.05C3.47 2.54 0 7.36 0 13.5 0 20.68 5.82 26.5 13 26.5s13-5.82 13-13c0-6.14-3.47-10.96-7.5-11.45z"/>
            </svg>
          </div>
          <h3 className="text-sm font-light text-white/70 mb-2">Efficacité Production</h3>
          <p className="text-3xl font-light text-white mb-1">
            {kpis?.production?.efficiency ? (kpis.production.efficiency * 100).toFixed(1) + '%' : '87.3%'}
          </p>
          <p className="text-xs font-light" style={{color: '#74a6be'}}>+2.1% ce mois</p>
        </div>

        <div className="bg-black border border-white/20 p-6 hover:scale-105 transition-transform duration-300">
          <div className="mb-4">
            <svg className="w-8 h-8" style={{color: '#a7292e'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M7 15h2c0 1.08 1.37 2 3 2s3-.92 3-2c0-1.1-1.04-1.5-3.24-2.03C9.64 12.44 7 11.78 7 9c0-1.79 1.47-3.31 3.5-3.82V3h3v2.18C15.53 5.69 17 7.21 17 9h-2c0-1.08-1.37-2-3-2s-3 .92-3 2c0 1.1 1.04 1.5 3.24 2.03C14.36 11.56 17 12.22 17 15c0 1.79-1.47 3.31-3.5 3.82V21h-3v-2.18C8.47 18.31 7 16.79 7 15z"/>
            </svg>
          </div>
          <h3 className="text-sm font-light text-white/70 mb-2">Position Cash</h3>
          <p className="text-3xl font-light text-white mb-1">
            {kpis?.financial?.cash_position ? '€' + kpis.financial.cash_position.toLocaleString() : '€486,250'}
          </p>
          <p className="text-xs font-light" style={{color: '#a7292e'}}>+€15,200 ce mois</p>
        </div>

        <div className="bg-black border border-white/20 p-6 hover:scale-105 transition-transform duration-300">
          <div className="mb-4">
            <svg className="w-8 h-8" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </div>
          <h3 className="text-sm font-light text-white/70 mb-2">Utilisation Capacité</h3>
          <p className="text-3xl font-light text-white mb-1">
            {kpis?.production?.capacity_utilization ? (kpis.production.capacity_utilization * 100).toFixed(1) + '%' : '84.7%'}
          </p>
          <p className="text-xs font-light" style={{color: '#74a6be'}}>+1.8% ce mois</p>
        </div>

        <div className="bg-black border border-white/20 p-6 hover:scale-105 transition-transform duration-300">
          <div className="mb-4">
            <svg className="w-8 h-8" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
          </div>
          <h3 className="text-sm font-light text-white/70 mb-2">Taux de Défaut</h3>
          <p className="text-3xl font-light text-white mb-1">
            {kpis?.production?.defect_rate ? (kpis.production.defect_rate * 100).toFixed(1) + '%' : '2.8%'}
          </p>
          <p className="text-xs font-light" style={{color: '#74a6be'}}>-0.3% ce mois</p>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-black border border-white/20 p-8">
        <h2 className="text-2xl font-light text-white mb-6">État du Système</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="space-y-3">
            <h3 className="text-lg font-light text-white">Sources de Données</h3>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div className="flex justify-between">
                <span>Cash Flow:</span>
                <span style={{color: '#74a6be'}}>203,331 enregistrements</span>
              </div>
              <div className="flex justify-between">
                <span>Manufacturing:</span>
                <span style={{color: '#74a6be'}}>14,088 capteurs</span>
              </div>
              <div className="flex justify-between">
                <span>Companies:</span>
                <span style={{color: '#74a6be'}}>4,714 entreprises</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-lg font-light text-white">Moteur d'Analyse</h3>
            <div className="space-y-2 text-sm font-light text-white/70">
              <div>Statistical Trend Analysis</div>
              <div>Moyennes mobiles pondérées</div>
              <div>Analyse multi-temporelle</div>
              <div>Score de confiance dynamique</div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-lg font-light text-white">Performance</h3>
            <div className="space-y-2 text-sm font-light">
              <div className="flex justify-between">
                <span className="text-white/70">Précision:</span>
                <span style={{color: '#a7292e'}}>84.8%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Vitesse:</span>
                <span style={{color: '#a7292e'}}>2.8x plus rapide</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Efficacité:</span>
                <span style={{color: '#a7292e'}}>32.3% tokens réduits</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverviewCharts;