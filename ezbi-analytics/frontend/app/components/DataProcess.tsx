export default function DataProcess() {
  return (
    <section className="py-20 bg-gray-900">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-8">
              Comment ça marche
            </h2>
            <p className="text-xl text-gray-300">
              De vos données brutes à l'intelligence actionnable en 3 étapes
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-6">
                1
              </div>
              <h3 className="text-xl font-bold text-white mb-4">
                Connexion des données
              </h3>
              <p className="text-gray-300 mb-6">
                Intégration automatique de vos systèmes : ERP, machines IoT, 
                comptabilité, CRM. Aucune saisie manuelle.
              </p>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-sm text-gray-400 space-y-1">
                  <div>📊 ERP (SAP, Odoo...)</div>
                  <div>🏭 Machines IoT</div>
                  <div>💰 Comptabilité</div>
                  <div>📋 Facturation</div>
                </div>
              </div>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-6">
                2
              </div>
              <h3 className="text-xl font-bold text-white mb-4">
                Analyse IA temps réel
              </h3>
              <p className="text-gray-300 mb-6">
                Nos modèles IA (Prophet + LSTM) analysent 218K+ patterns 
                pour prédire votre trésorerie et identifier les risques.
              </p>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-sm text-gray-400 space-y-1">
                  <div>🤖 Prophet + LSTM</div>
                  <div>📈 87% précision</div>
                  <div>⚡ Temps réel</div>
                  <div>🧮 218K+ données</div>
                </div>
              </div>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-6">
                3
              </div>
              <h3 className="text-xl font-bold text-white mb-4">
                Actions recommandées
              </h3>
              <p className="text-gray-300 mb-6">
                Alertes Slack intelligentes avec plans d'action concrets 
                pour optimiser votre trésorerie et production.
              </p>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-sm text-gray-400 space-y-1">
                  <div>💬 Alertes Slack</div>
                  <div>📋 Plans d'action</div>
                  <div>🎯 Recommandations</div>
                  <div>📊 Tableaux de bord</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}