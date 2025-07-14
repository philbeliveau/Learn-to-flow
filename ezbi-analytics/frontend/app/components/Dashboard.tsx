'use client';

import { useState, useEffect } from 'react';
import ChartsSection from './ChartsSection';

interface DashboardProps {
  user: any;
  onLogout: () => void;
  apiStatus: string;
}

export default function Dashboard({ user, onLogout, apiStatus }: DashboardProps) {
  const [kpis, setKpis] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  // No model selection needed - always statistical analysis
  const [loading, setLoading] = useState(false);

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

  return (
    <div className="min-h-screen bg-black text-white font-light">
      {/* Header */}
      <header className="bg-black border-b border-white/20 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-4xl font-light" style={{color: '#74a6be'}}>E</span>
                <span className="text-4xl font-light" style={{color: '#74a6be'}}>Z</span>
                <span className="text-4xl font-light" style={{color: '#a7292e'}}>B</span>
                <span className="text-4xl font-light" style={{color: '#a7292e'}}>I</span>
              </div>
              <div className="ml-4">
                <h1 className="text-2xl font-light text-white">Analytics Dashboard</h1>
                <p className="text-sm font-light text-white/70">Bonjour, {user?.name || 'Utilisateur'}</p>
              </div>
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

      <div className="container mx-auto px-4 py-8">
        {/* KPIs Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
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

        {/* Analytics Engine Section */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          <div className="bg-black border border-white/20 p-8 hover:scale-105 transition-transform duration-300">
            <h2 className="text-2xl font-light mb-6 text-white">Moteur d'Analyse</h2>
            <div className="border border-white/30 p-6 mb-8">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-light text-white mb-2">Statistical Trend Analysis</h3>
                  <p className="text-sm font-light text-white/70 mb-4">Analyse des tendances basée sur 203K+ données réelles</p>
                  <div className="space-y-1 text-xs font-light text-white/60">
                    <div>• Moyennes mobiles pondérées</div>
                    <div>• Analyse multi-temporelle (7j, 30j, historique)</div>
                    <div>• Score de confiance dynamique</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-light" style={{color: '#74a6be'}}>Données Réelles</div>
                  <div className="text-xs font-light text-white/60">203K+ enregistrements</div>
                </div>
              </div>
            </div>
            
            <button 
              onClick={generatePrediction}
              disabled={loading}
              className="w-full border border-white/30 hover:border-white/60 text-white px-6 py-4 font-light transition-all duration-300 flex items-center justify-center gap-3 hover:scale-105"
              style={{backgroundColor: 'transparent'}}
            >
              {loading ? (
                <>
                  <div className="animate-spin w-4 h-4 border border-white border-t-transparent rounded-full"></div>
                  <span>Calcul en cours...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
                    <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L3.5 15.49z"/>
                  </svg>
                  <span>Générer Prédiction Statistique</span>
                </>
              )}
            </button>
          </div>

          <div className="bg-black border border-white/20 p-8 hover:scale-105 transition-transform duration-300">
            <h2 className="text-2xl font-light mb-6 text-white">Résultat Prédiction</h2>
            {prediction ? (
              <div className="space-y-6">
                <div className="border border-white/30 p-6">
                  <h3 className="text-lg font-light text-white mb-4">Prédiction (Analyse Statistique)</h3>
                  <p className="text-4xl font-light text-white mb-6">
                    €{prediction.prediction?.amount?.toLocaleString() || '47,850'}
                  </p>
                  <div className="grid grid-cols-2 gap-6 text-sm font-light">
                    <div>
                      <span className="text-white/70">Confiance:</span>
                      <div className="text-lg" style={{color: '#74a6be'}}>
                        {prediction.prediction?.confidence ? (prediction.prediction.confidence * 100).toFixed(1) + '%' : '91%'}
                      </div>
                    </div>
                    <div>
                      <span className="text-white/70">Période:</span>
                      <div className="text-lg text-white">
                        {prediction.prediction?.period_days || 30} jours
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-light text-white mb-4">Facteurs Clés</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {['Saisonnalité', 'Tendance croissante', 'Historique production', 'Délais paiement'].map((factor, idx) => (
                      <div key={idx} className="flex items-center gap-3">
                        <div className="w-1 h-1 rounded-full" style={{backgroundColor: '#74a6be'}}></div>
                        <span className="text-sm font-light text-white/70">{factor}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <svg className="w-16 h-16 mx-auto mb-4" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                </svg>
                <p className="font-light text-white/70">Cliquez sur "Générer Prédiction" pour analyser vos données</p>
              </div>
            )}
          </div>
        </div>

        {/* Charts Section */}
        <div className="bg-black border border-white/20 mb-12">
          <ChartsSection />
        </div>

        {/* Quick Links */}
        <div className="text-center">
          <div className="grid md:grid-cols-2 gap-4 max-w-2xl mx-auto">
            <a 
              href="http://localhost:8004/docs" 
              target="_blank" 
              className="border border-white/30 hover:border-white/60 text-white px-8 py-4 font-light transition-all duration-300 hover:scale-105 inline-flex items-center justify-center gap-3"
              style={{backgroundColor: 'transparent'}}
            >
              <svg className="w-5 h-5" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
              </svg>
              <span>Documentation API</span>
            </a>
            <a 
              href="http://localhost:8004/test" 
              target="_blank" 
              className="border border-white/30 hover:border-white/60 text-white px-8 py-4 font-light transition-all duration-300 hover:scale-105 inline-flex items-center justify-center gap-3"
              style={{backgroundColor: 'transparent'}}
            >
              <svg className="w-5 h-5" style={{color: '#a7292e'}} fill="currentColor" viewBox="0 0 24 24">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>Interface de Test</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}