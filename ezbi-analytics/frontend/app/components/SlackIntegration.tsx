export default function SlackIntegration() {
  return (
    <section className="py-20 bg-gray-800">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-8">
            Intégration Slack native
          </h2>
          <p className="text-xl text-gray-300 mb-12">
            Recevez vos alertes et insights directement dans Slack
          </p>
          
          <div className="bg-gradient-to-br from-green-900/30 to-blue-900/30 backdrop-blur-lg rounded-xl p-8 border border-green-500/30">
            <div className="flex items-center justify-center gap-8 mb-8">
              <div className="text-6xl">💬</div>
              <div className="text-4xl text-gray-400">+</div>
              <div className="text-6xl">🤖</div>
            </div>
            
            <h3 className="text-2xl font-bold text-white mb-4">
              Alertes intelligentes en temps réel
            </h3>
            <p className="text-gray-300 mb-6">
              L'IA EZBI surveille vos données 24/7 et vous alerte instantanément 
              des risques et opportunités via Slack.
            </p>
            
            <div className="grid md:grid-cols-2 gap-6 mt-8">
              <div className="bg-black/30 rounded-lg p-4">
                <h4 className="font-bold text-green-400 mb-2">🟢 Opportunité détectée</h4>
                <p className="text-sm text-gray-300">
                  "Commande importante prévue. Prévoir augmentation trésorerie +€45K en 15 jours."
                </p>
              </div>
              <div className="bg-black/30 rounded-lg p-4">
                <h4 className="font-bold text-red-400 mb-2">🔴 Risque identifié</h4>
                <p className="text-sm text-gray-300">
                  "Retard fournisseur détecté. Impact trésorerie -€12K possible."
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}