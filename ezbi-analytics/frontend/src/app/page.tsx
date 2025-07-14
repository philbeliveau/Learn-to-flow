'use client';

import { useState, useEffect } from 'react';

export default function EZBIApp() {
  const [currentView, setCurrentView] = useState('home');
  const [apiStatus, setApiStatus] = useState('checking');
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [prediction, setPrediction] = useState(null);

  // Check API status on mount
  useEffect(() => {
    checkAPIStatus();
  }, []);

  // Load KPIs when dashboard view is active
  useEffect(() => {
    if (currentView === 'dashboard' && isAuthenticated) {
      loadKPIs();
    }
  }, [currentView, isAuthenticated]);

  const checkAPIStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      setApiStatus(data.status === 'healthy' ? 'online' : 'offline');
    } catch (error) {
      setApiStatus('offline');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData)
      });
      const data = await response.json();
      if (data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
        setCurrentView('dashboard');
      }
    } catch (error) {
      alert('Erreur de connexion: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const loadKPIs = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/company/kpis');
      const data = await response.json();
      setKpis(data);
    } catch (error) {
      console.error('Erreur KPIs:', error);
    }
  };

  const generatePrediction = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/predictions/cashflow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ revenue: 150000, expenses: 112500, period_days: 30 })
      });
      const data = await response.json();
      setPrediction(data);
    } catch (error) {
      console.error('Erreur prédiction:', error);
    }
  };

  // Status indicator
  const StatusIndicator = () => (
    <div className="flex items-center gap-2 mb-4">
      <div className={`w-3 h-3 rounded-full ${apiStatus === 'online' ? 'bg-green-500' : apiStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'}`}></div>
      <span className="text-sm font-medium">
        API: {apiStatus === 'online' ? 'En ligne' : apiStatus === 'offline' ? 'Hors ligne' : 'Vérification...'}
      </span>
    </div>
  );

  // Home Page
  if (currentView === 'home') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-800">
        <div className="container mx-auto px-4 py-8">
          <StatusIndicator />
          
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="text-center mb-12">
              <h1 className="text-6xl font-bold text-white mb-4">
                🏭 EZBI Analytics
              </h1>
              <p className="text-2xl text-white/90 mb-6">
                Plateforme d'Intelligence Manufacturière
              </p>
              <p className="text-lg text-white/80 max-w-2xl mx-auto">
                Solution IA de prédiction de trésorerie pour les PME manufacturières françaises
              </p>
            </div>

            {/* Features Grid */}
            <div className="grid md:grid-cols-3 gap-8 mb-12">
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                <div className="text-4xl mb-4">🤖</div>
                <h3 className="text-xl font-bold mb-3 text-white">IA Prédictive</h3>
                <p className="text-white/80 mb-4">Modèles Prophet + LSTM avec 87% de confiance</p>
                <div className="text-sm text-blue-300 font-medium">
                  ✓ 218K+ enregistrements réels
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                <div className="text-4xl mb-4">📊</div>
                <h3 className="text-xl font-bold mb-3 text-white">Analytics Manufacturier</h3>
                <p className="text-white/80 mb-4">KPIs de production, qualité et efficacité</p>
                <div className="text-sm text-green-300 font-medium">
                  ✓ Temps réel + historique
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                <div className="text-4xl mb-4">🇫🇷</div>
                <h3 className="text-xl font-bold mb-3 text-white">Conformité Française</h3>
                <p className="text-white/80 mb-4">SIRET/SIREN, RGPD, EUR</p>
                <div className="text-sm text-purple-300 font-medium">
                  ✓ PME manufacturing ready
                </div>
              </div>
            </div>

            {/* Login Section */}
            <div className="max-w-md mx-auto bg-white/10 backdrop-blur-lg rounded-xl p-8 border border-white/20">
              <h2 className="text-2xl font-bold text-center mb-6 text-white">Connexion</h2>
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-white/90">Email</label>
                  <input
                    type="email"
                    className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-white/60"
                    value={loginData.email}
                    onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                    placeholder="demo@ezbi.fr"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-white/90">Mot de passe</label>
                  <input
                    type="password"
                    className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-white/60"
                    value={loginData.password}
                    onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                    placeholder="demo123"
                  />
                </div>
                <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 transform hover:scale-105">
                  Se connecter
                </button>
              </form>

              <div className="mt-6 p-4 bg-blue-500/20 rounded-lg border border-blue-400/30">
                <p className="text-sm text-blue-200">
                  <strong>Demo:</strong> demo@ezbi.fr / demo123
                </p>
              </div>
            </div>

            {/* Quick Links */}
            <div className="text-center mt-12">
              <div className="space-x-4">
                <a href="http://localhost:8000/docs" target="_blank" className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 transform hover:scale-105 inline-block">
                  📚 Documentation API
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Dashboard
  if (currentView === 'dashboard' && isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="container mx-auto px-4 py-4">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold">🏭 EZBI Analytics</h1>
                <p className="text-gray-600">Bonjour, {user?.name || 'Jean Dupont'}</p>
              </div>
              <div className="flex gap-4 items-center">
                <StatusIndicator />
                <button 
                  onClick={() => {setIsAuthenticated(false); setCurrentView('home');}}
                  className="text-red-600 hover:text-red-800 px-4 py-2 rounded-lg hover:bg-red-50"
                >
                  Déconnexion
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="container mx-auto px-4 py-8">
          {/* KPIs Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-sm font-medium text-gray-600">Efficacité Production</h3>
              <p className="text-2xl font-bold text-green-600">
                {kpis?.production?.efficiency ? (kpis.production.efficiency * 100).toFixed(1) + '%' : '85%'}
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-sm font-medium text-gray-600">Utilisation Capacité</h3>
              <p className="text-2xl font-bold text-blue-600">
                {kpis?.production?.capacity_utilization ? (kpis.production.capacity_utilization * 100).toFixed(1) + '%' : '78%'}
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-sm font-medium text-gray-600">Position Cash</h3>
              <p className="text-2xl font-bold text-purple-600">
                {kpis?.financial?.cash_position ? '€' + kpis.financial.cash_position.toLocaleString() : '€450,000'}
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-sm font-medium text-gray-600">Taux de Défaut</h3>
              <p className="text-2xl font-bold text-orange-600">
                {kpis?.production?.defect_rate ? (kpis.production.defect_rate * 100).toFixed(1) + '%' : '3%'}
              </p>
            </div>
          </div>

          {/* Prediction Section */}
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Prédiction Cash Flow IA</h2>
              <p className="text-gray-600 mb-4">
                Générez une prédiction de trésorerie basée sur l'IA (Prophet + LSTM)
              </p>
              <button 
                onClick={generatePrediction}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 transform hover:scale-105 mb-4"
              >
                🤖 Générer Prédiction
              </button>
              
              {prediction && (
                <div className="p-4 bg-green-50 rounded-lg">
                  <h3 className="font-bold text-green-800 mb-2">Résultat Prédiction:</h3>
                  <p className="text-lg font-bold text-green-600">
                    €{prediction.prediction?.amount?.toLocaleString()} EUR
                  </p>
                  <p className="text-sm text-green-700">
                    Confiance: {prediction.prediction?.confidence ? (prediction.prediction.confidence * 100).toFixed(1) + '%' : '87%'}
                  </p>
                  <p className="text-sm text-green-700">
                    Période: {prediction.prediction?.period_days || 30} jours
                  </p>
                </div>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Données Manufacturières</h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Processus Manufacturing:</span>
                  <span className="font-bold">14,089 records</span>
                </div>
                <div className="flex justify-between">
                  <span>Données Cash Flow:</span>
                  <span className="font-bold">203,332 records</span>
                </div>
                <div className="flex justify-between">
                  <span>Analyse Coûts:</span>
                  <span className="font-bold">1,001 records</span>
                </div>
                <div className="flex justify-between border-t pt-2">
                  <span className="font-bold">Total Dataset:</span>
                  <span className="font-bold text-blue-600">218,422 records</span>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="text-center mt-8">
            <div className="space-x-4">
              <a href="http://localhost:8000/docs" target="_blank" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 transform hover:scale-105 inline-block">
                📚 API Documentation
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}