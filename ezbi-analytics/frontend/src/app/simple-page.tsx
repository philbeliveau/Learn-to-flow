'use client';

import { useState } from 'react';

export default function SimplePage() {
  const [isLoading, setIsLoading] = useState(false);

  const testAPI = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8003/health');
      const data = await response.json();
      alert(`API Status: ${data.status}`);
    } catch (error) {
      alert(`API Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Header */}
          <div className="mb-12">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              🏭 EZBI Analytics
            </h1>
            <p className="text-xl text-gray-600 mb-6">
              Intelligence manufacturière alimentée par l'IA
            </p>
            <p className="text-lg text-blue-600">
              Solution IA de prédiction de trésorerie pour les PME manufacturières françaises
            </p>
          </div>

          {/* Status Cards */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="text-3xl mb-2">🤖</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">IA Prédictive</h3>
              <p className="text-gray-600 text-sm">Modèles Prophet + LSTM avec 87% de confiance</p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="text-3xl mb-2">📊</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Données Réelles</h3>
              <p className="text-gray-600 text-sm">218K+ enregistrements de fabrication</p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="text-3xl mb-2">🇫🇷</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Conformité FR</h3>
              <p className="text-gray-600 text-sm">SIRET/SIREN, RGPD, EUR</p>
            </div>
          </div>

          {/* API Test */}
          <div className="bg-white p-8 rounded-lg shadow-lg mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Test de l'API Backend
            </h2>
            <p className="text-gray-600 mb-6">
              Testez la connexion avec le backend EZBI Analytics
            </p>
            <button
              onClick={testAPI}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              {isLoading ? 'Test en cours...' : 'Tester l\'API'}
            </button>
          </div>

          {/* Features */}
          <div className="bg-white p-8 rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Fonctionnalités Disponibles
            </h2>
            <div className="grid md:grid-cols-2 gap-4 text-left">
              <div className="flex items-start gap-3">
                <div className="text-green-500 text-xl">✅</div>
                <div>
                  <h4 className="font-semibold">Authentification JWT</h4>
                  <p className="text-sm text-gray-600">Système de login sécurisé</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="text-green-500 text-xl">✅</div>
                <div>
                  <h4 className="font-semibold">Prédictions Cash Flow</h4>
                  <p className="text-sm text-gray-600">IA Prophet + LSTM</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="text-green-500 text-xl">✅</div>
                <div>
                  <h4 className="font-semibold">KPIs Manufacturing</h4>
                  <p className="text-sm text-gray-600">Analytics complets</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="text-green-500 text-xl">✅</div>
                <div>
                  <h4 className="font-semibold">Base de Données</h4>
                  <p className="text-sm text-gray-600">PostgreSQL avec données réelles</p>
                </div>
              </div>
            </div>
          </div>

          {/* Links */}
          <div className="mt-8 space-y-4">
            <div>
              <a 
                href="http://localhost:8003/test" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium transition-colors mr-4"
              >
                🧪 Interface de Test
              </a>
              <a 
                href="http://localhost:8003/docs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-block bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                📚 Documentation API
              </a>
            </div>
            <p className="text-sm text-gray-500">
              Backend API: http://localhost:8003 | Frontend: http://localhost:3000
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}