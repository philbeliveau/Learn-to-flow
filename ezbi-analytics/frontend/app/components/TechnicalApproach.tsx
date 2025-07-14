export default function TechnicalApproach() {
  return (
    <section className="py-20 bg-black">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-8">
              Approche technique avancée
            </h2>
            <p className="text-xl text-gray-300">
              IA de pointe adaptée aux spécificités du manufacturing français
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-2xl font-bold text-white mb-6">
                Stack technologique
              </h3>
              
              <div className="space-y-6">
                <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
                  <h4 className="text-lg font-bold text-blue-400 mb-3">🤖 Machine Learning</h4>
                  <ul className="space-y-2 text-gray-300">
                    <li>• Prophet: Détection des tendances saisonnières</li>
                    <li>• LSTM: Réseaux de neurones pour patterns complexes</li>
                    <li>• Ensemble: Combinaison pour 87% de précision</li>
                  </ul>
                </div>
                
                <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
                  <h4 className="text-lg font-bold text-green-400 mb-3">🏗️ Infrastructure</h4>
                  <ul className="space-y-2 text-gray-300">
                    <li>• Docker + Kubernetes: Scalabilité automatique</li>
                    <li>• PostgreSQL: Base de données optimisée</li>
                    <li>• Redis: Cache haute performance</li>
                  </ul>
                </div>
                
                <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
                  <h4 className="text-lg font-bold text-purple-400 mb-3">🔒 Sécurité & Conformité</h4>
                  <ul className="space-y-2 text-gray-300">
                    <li>• RGPD: Conformité totale des données</li>
                    <li>• Chiffrement AES-256</li>
                    <li>• Hébergement France (OVH)</li>
                  </ul>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-2xl font-bold text-white mb-6">
                Données d'entraînement
              </h3>
              
              <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 backdrop-blur-lg rounded-xl p-8 border border-blue-500/30">
                <div className="grid grid-cols-2 gap-6 mb-8">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-400">218K+</div>
                    <div className="text-sm text-gray-300">Enregistrements réels</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-400">87%</div>
                    <div className="text-sm text-gray-300">Précision prédiction</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-400">3 ans</div>
                    <div className="text-sm text-gray-300">Données historiques</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-orange-400">5</div>
                    <div className="text-sm text-gray-300">PME manufacturières</div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="bg-black/30 rounded-lg p-3">
                    <span className="text-blue-400 font-semibold">Cash Flow:</span>
                    <span className="text-gray-300 ml-2">203,332 transactions réelles</span>
                  </div>
                  <div className="bg-black/30 rounded-lg p-3">
                    <span className="text-green-400 font-semibold">Production:</span>
                    <span className="text-gray-300 ml-2">14,089 cycles machines</span>
                  </div>
                  <div className="bg-black/30 rounded-lg p-3">
                    <span className="text-purple-400 font-semibold">Économies:</span>
                    <span className="text-gray-300 ml-2">1,001 optimisations</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}