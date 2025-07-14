export default function TresoreriePage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold mb-8 text-center">
            💰 Prédiction de Trésorerie
          </h1>
          <p className="text-xl text-gray-300 text-center mb-12">
            IA avancée pour anticiper vos flux de trésorerie avec une précision de 87%
          </p>
          
          <div className="bg-gradient-to-br from-green-900/30 to-blue-900/30 backdrop-blur-lg rounded-xl p-8 border border-green-500/30 mb-12">
            <h2 className="text-2xl font-bold mb-6 text-center">Modèles IA Avancés</h2>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-4xl mb-4">🔮</div>
                <h3 className="text-lg font-bold mb-3">Prophet</h3>
                <p className="text-gray-300 text-sm">Détection des tendances saisonnières et cycles métier</p>
              </div>
              
              <div className="text-center">
                <div className="text-4xl mb-4">🧠</div>
                <h3 className="text-lg font-bold mb-3">LSTM</h3>
                <p className="text-gray-300 text-sm">Réseaux de neurones pour patterns complexes</p>
              </div>
              
              <div className="text-center">
                <div className="text-4xl mb-4">⚡</div>
                <h3 className="text-lg font-bold mb-3">Ensemble</h3>
                <p className="text-gray-300 text-sm">Combinaison intelligente pour 87% de précision</p>
              </div>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div className="bg-gray-900 rounded-xl p-6">
              <h3 className="text-xl font-bold mb-4">📊 Données d'Entraînement</h3>
              <ul className="space-y-2 text-gray-300">
                <li>• 203,332 transactions de cash flow réelles</li>
                <li>• 14,089 cycles de production manufacturière</li>
                <li>• 1,001 optimisations d'économies d'échelle</li>
                <li>• 3 années de données historiques</li>
                <li>• 5 PME manufacturières françaises</li>
              </ul>
            </div>
            
            <div className="bg-gray-900 rounded-xl p-6">
              <h3 className="text-xl font-bold mb-4">🎯 Prédictions Précises</h3>
              <ul className="space-y-2 text-gray-300">
                <li>• Horizons 30, 60 et 90 jours</li>
                <li>• Intervalles de confiance détaillés</li>
                <li>• Scénarios optimiste/pessimiste</li>
                <li>• Impact des variables de production</li>
                <li>• Recommandations d'actions correctives</li>
              </ul>
            </div>
          </div>
          
          <div className="text-center">
            <h2 className="text-3xl font-bold mb-8">Intégrations Natives</h2>
            
            <div className="grid md:grid-cols-4 gap-4 mb-12">
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-2xl mb-2">📋</div>
                <div className="text-sm font-semibold">ERP</div>
                <div className="text-xs text-gray-400">SAP, Odoo, Sage</div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-2xl mb-2">🏭</div>
                <div className="text-sm font-semibold">IoT</div>
                <div className="text-xs text-gray-400">Machines, capteurs</div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-2xl mb-2">💳</div>
                <div className="text-sm font-semibold">Banque</div>
                <div className="text-xs text-gray-400">Flux bancaires</div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-2xl mb-2">📊</div>
                <div className="text-sm font-semibold">CRM</div>
                <div className="text-xs text-gray-400">Pipeline ventes</div>
              </div>
            </div>
            
            <a 
              href="/"
              className="bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-lg font-medium transition-colors inline-block"
            >
              ← Retour à l'accueil
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}