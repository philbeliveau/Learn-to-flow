export default function Pricing() {
  return (
    <section id="pricing" className="py-20 bg-black">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-light text-white mb-8 tracking-tight">
              Commencez gratuitement,
              <br />
              <span style={{color: '#a7292e'}}>payez quand ça marche</span>
            </h2>
            <p className="text-xl font-light text-gray-300 max-w-3xl mx-auto leading-relaxed">
              Pas de setup, pas de contrat. On installe tout, vous payez seulement quand vous voyez de la valeur.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Free Assessment */}
            <div className="bg-black border border-gray-700 p-8 hover:scale-105 transition-transform duration-300">
              <div className="mb-8">
                <h3 className="text-2xl font-light text-white mb-4">Évaluation gratuite</h3>
                <div className="text-4xl font-light mb-2" style={{color: '#74a6be'}}>0$</div>
                <div className="text-gray-400 font-light">Toujours gratuit</div>
              </div>
              
              <ul className="space-y-4 mb-8 font-light">
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#74a6be'}}></div>
                  <span className="text-gray-300">Audit complet de vos données</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#74a6be'}}></div>
                  <span className="text-gray-300">Identification des risques</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#74a6be'}}></div>
                  <span className="text-gray-300">Plan d'action personnalisé</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#74a6be'}}></div>
                  <span className="text-gray-300">Aucun engagement</span>
                </li>
              </ul>
              
              <button className="w-full text-white px-6 py-3 font-light transition-colors" style={{backgroundColor: '#74a6be'}}>
                Réserver mon audit
              </button>
            </div>

            {/* Surveillance */}
            <div className="bg-black border border-gray-700 p-8 hover:scale-105 transition-transform duration-300">
              <div className="mb-8">
                <h3 className="text-2xl font-light text-white mb-4">Surveillance</h3>
                <div className="text-4xl font-light text-white mb-2">2,500$</div>
                <div className="text-gray-400 font-light">/mois</div>
              </div>
              
              <ul className="space-y-4 mb-8 font-light">
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#a7292e'}}></div>
                  <span className="text-gray-300">Alertes cash flow temps réel</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#a7292e'}}></div>
                  <span className="text-gray-300">Monitoring comptes clients</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#a7292e'}}></div>
                  <span className="text-gray-300">Tableau de bord exécutif</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#a7292e'}}></div>
                  <span className="text-gray-300">Intégration Slack/Teams</span>
                </li>
              </ul>
              
              <button className="w-full text-white px-6 py-3 font-light transition-colors" style={{backgroundColor: '#a7292e'}}>
                Commencer maintenant
              </button>
            </div>
            
            {/* Intelligence Complete */}
            <div className="border-2 p-8 hover:scale-105 transition-transform duration-300 relative" style={{backgroundColor: 'rgba(167, 41, 46, 0.1)', borderColor: '#a7292e'}}>
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="text-white px-4 py-1 text-sm font-light" style={{backgroundColor: '#a7292e'}}>
                  Plus populaire
                </span>
              </div>
              
              <div className="mb-8">
                <h3 className="text-2xl font-light text-white mb-4">Intelligence complète</h3>
                <div className="text-4xl font-light text-white mb-2">4,500$</div>
                <div className="text-gray-400 font-light">/mois</div>
              </div>
              
              <ul className="space-y-4 mb-8 font-light">
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#a7292e'}}></div>
                  <span className="text-gray-300">Tout de "Surveillance"</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#a7292e'}}></div>
                  <span className="text-gray-300">Prédictions IA 30/60/90 jours</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#a7292e'}}></div>
                  <span className="text-gray-300">Optimisation automatique</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2" style={{backgroundColor: '#a7292e'}}></div>
                  <span className="text-gray-300">Recommandations actionables</span>
                </li>
              </ul>
              
              <button className="w-full text-white px-6 py-3 font-light transition-colors" style={{backgroundColor: '#a7292e'}}>
                Démarrer l'intelligence
              </button>
            </div>
            
            {/* Pilot Custom */}
            <div className="bg-black border border-gray-700 p-8 hover:scale-105 transition-transform duration-300">
              <div className="mb-8">
                <h3 className="text-2xl font-light text-white mb-4">Pilote sur mesure</h3>
                <div className="text-4xl font-light text-gray-400 mb-2">Sur devis</div>
                <div className="text-gray-400 font-light">3-6 mois</div>
              </div>
              
              <ul className="space-y-4 mb-8 font-light">
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-gray-400 mt-2"></div>
                  <span className="text-gray-300">Solution entièrement custom</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-gray-400 mt-2"></div>
                  <span className="text-gray-300">IA spécialisée pour votre secteur</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-gray-400 mt-2"></div>
                  <span className="text-gray-300">Formations équipe incluses</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-gray-400 mt-2"></div>
                  <span className="text-gray-300">Support dédié 24/7</span>
                </li>
              </ul>
              
              <button className="w-full border border-gray-600 hover:border-gray-400 text-white px-6 py-3 font-light transition-colors">
                Discuter du projet
              </button>
            </div>
          </div>
          
          {/* Guarantees */}
          <div className="text-center mt-16 space-y-4">
            <p className="text-lg font-light text-gray-300">
              🔒 <span className="text-white">Garanties incluses :</span> Hébergement au Canada, conformité PIPEDA, 
              données jamais partagées
            </p>
            <p className="text-lg font-light" style={{color: '#74a6be'}}>
              ✓ <span className="text-white">30 jours satisfait ou remboursé</span> - Aucun risque pour vous
            </p>
            <p className="text-sm font-light text-gray-400">
              Installation et formation incluses dans tous les forfaits payants
            </p>
          </div>

          {/* Bottom CTA */}
          <div className="text-center mt-12">
            <a
              href="#contact"
              className="inline-block text-white px-8 py-4 font-light transition-all hover:scale-105"
              style={{backgroundColor: '#a7292e'}}
            >
              Commencer par l'évaluation gratuite
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}