export default function Services() {
  return (
    <section id="services" className="py-20 bg-black">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-8">
              Nos solutions IA
            </h2>
            <p className="text-xl text-gray-300">
              Intelligence manufacturière alimentée par l'IA pour une gestion proactive
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-gradient-to-br from-blue-900/50 to-purple-900/50 backdrop-blur-lg rounded-xl p-8 border border-blue-500/30">
              <div className="text-5xl mb-6">💰</div>
              <h3 className="text-2xl font-bold text-blue-400 mb-4">
                Cash Flow Radar
              </h3>
              <p className="text-gray-300 mb-6">
                Prédiction de trésorerie avec IA (Prophet + LSTM) basée sur 
                218K+ enregistrements réels de PME manufacturières.
              </p>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>✓ Précision 87% sur 30 jours</li>
                <li>✓ Intégration données production</li>
                <li>✓ Alertes proactives</li>
              </ul>
            </div>
            
            <div className="bg-gradient-to-br from-green-900/50 to-teal-900/50 backdrop-blur-lg rounded-xl p-8 border border-green-500/30">
              <div className="text-5xl mb-6">📊</div>
              <h3 className="text-2xl font-bold text-green-400 mb-4">
                Manufacturing Intelligence
              </h3>
              <p className="text-gray-300 mb-6">
                KPIs temps réel de production, qualité, efficacité avec 
                corrélations automatiques entre process et finance.
              </p>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>✓ 100+ capteurs IoT</li>
                <li>✓ 5 machines surveillées</li>
                <li>✓ Optimisation continue</li>
              </ul>
            </div>
            
            <div className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 backdrop-blur-lg rounded-xl p-8 border border-purple-500/30">
              <div className="text-5xl mb-6">🤖</div>
              <h3 className="text-2xl font-bold text-purple-400 mb-4">
                Early Warning System
              </h3>
              <p className="text-gray-300 mb-6">
                Détection précoce des risques financiers et opérationnels 
                avec recommandations d'actions correctives.
              </p>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>✓ Alertes intelligentes</li>
                <li>✓ Scénarios prédictifs</li>
                <li>✓ Plans d'action automatisés</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}