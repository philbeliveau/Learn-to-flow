export default function IntelligenceCompletePage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold mb-8 text-center">
            🤖 Intelligence Complète
          </h1>
          <p className="text-xl text-gray-300 text-center mb-12">
            Suite complète d'intelligence manufacturière alimentée par l'IA
          </p>
          
          <div className="grid md:grid-cols-2 gap-12 mb-16">
            <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 backdrop-blur-lg rounded-xl p-8 border border-blue-500/30">
              <h2 className="text-2xl font-bold mb-6">📊 Analytics Avancés</h2>
              <ul className="space-y-3 text-gray-300">
                <li>• Prédiction trésorerie avec 87% de précision</li>
                <li>• Modèles Prophet + LSTM combinés</li>
                <li>• 218K+ enregistrements d'entraînement</li>
                <li>• Corrélations production-finance automatiques</li>
              </ul>
            </div>
            
            <div className="bg-gradient-to-br from-green-900/30 to-teal-900/30 backdrop-blur-lg rounded-xl p-8 border border-green-500/30">
              <h2 className="text-2xl font-bold mb-6">🏭 Manufacturing Intelligence</h2>
              <ul className="space-y-3 text-gray-300">
                <li>• Surveillance temps réel de 5 machines</li>
                <li>• 100+ capteurs IoT intégrés</li>
                <li>• KPIs production, qualité, efficacité</li>
                <li>• Optimisation continue des process</li>
              </ul>
            </div>
          </div>
          
          <div className="text-center">
            <h2 className="text-3xl font-bold mb-8">Fonctionnalités Intégrées</h2>
            
            <div className="grid md:grid-cols-3 gap-6 mb-12">
              <div className="bg-gray-900 rounded-lg p-6">
                <div className="text-4xl mb-4">💰</div>
                <h3 className="text-xl font-bold mb-3">Cash Flow Radar</h3>
                <p className="text-gray-400">Prédiction précise de votre trésorerie sur 30, 60 et 90 jours</p>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-6">
                <div className="text-4xl mb-4">⚠️</div>
                <h3 className="text-xl font-bold mb-3">Early Warning</h3>
                <p className="text-gray-400">Alertes proactives sur les risques financiers et opérationnels</p>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-6">
                <div className="text-4xl mb-4">💬</div>
                <h3 className="text-xl font-bold mb-3">Slack Integration</h3>
                <p className="text-gray-400">Notifications intelligentes directement dans votre Slack</p>
              </div>
            </div>
            
            <a 
              href="/"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg font-medium transition-colors inline-block"
            >
              ← Retour à l'accueil
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}