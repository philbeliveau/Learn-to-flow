export default function Services() {
  return (
    <section id="services" className="py-20 bg-black">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-light text-white mb-8 tracking-tight">
              Notre méthode en 3 étapes
            </h2>
            <p className="text-xl font-light text-white/70 max-w-3xl mx-auto leading-relaxed">
              On transforme vos données éparses en intelligence d'affaires actionnable.
              Progressivement, sans déranger vos opérations.
            </p>
          </div>
          
          <div className="space-y-12">
            {/* Step 1 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 text-white font-light text-2xl flex items-center justify-center" style={{backgroundColor: '#a7292e'}}>
                    1
                  </div>
                  <h3 className="text-3xl font-light text-white">
                    Surveillance de base
                  </h3>
                </div>
                <p className="text-lg font-light text-white/70 mb-6 leading-relaxed">
                  On connecte vos systèmes existants (QuickBooks, Excel, CRM) et on met en place 
                  des alertes automatiques dans Slack.
                </p>
                <ul className="space-y-3 text-white/60 font-light">
                  <li className="flex items-center gap-3">
                    <div className="w-2 h-2" style={{backgroundColor: '#a7292e'}}></div>
                    Alerte si compte en banque &lt; 30 jours d'opérations
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-2 h-2" style={{backgroundColor: '#a7292e'}}></div>
                    Notification factures impayées &gt; 60 jours
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-2 h-2" style={{backgroundColor: '#a7292e'}}></div>
                    Surveillance ventes hebdomadaires vs objectifs
                  </li>
                </ul>
              </div>
              <div className="bg-black border border-white/20 p-6">
                <div className="bg-black border border-white/20 p-4 mb-4">
                  <p className="text-sm font-light" style={{color: '#74a6be'}}>#finance-alerts</p>
                </div>
                <div className="space-y-3">
                  <div className="bg-white border-l-4 p-3" style={{borderLeftColor: '#a7292e'}}>
                    <p className="text-black text-sm font-light">
                      🚨 Cash flow: 23 jours restants
                    </p>
                  </div>
                  <div className="bg-white border-l-4 p-3" style={{borderLeftColor: '#74a6be'}}>
                    <p className="text-black text-sm font-light">
                      ⚠️ Facture ABC Corp: 45 jours de retard
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div className="order-2 md:order-1">
                <div className="bg-black border border-white/20 p-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-black border border-white/20 p-4 text-center">
                      <p className="text-2xl font-light text-white">87%</p>
                      <p className="text-sm text-white/60">Précision 30j</p>
                    </div>
                    <div className="bg-black border border-white/20 p-4 text-center">
                      <p className="text-2xl font-light" style={{color: '#a7292e'}}>-15k$</p>
                      <p className="text-sm text-white/60">Prédit dans 7j</p>
                    </div>
                    <div className="bg-black border border-white/20 p-4 text-center">
                      <p className="text-2xl font-light" style={{color: '#74a6be'}}>+23%</p>
                      <p className="text-sm text-white/60">Opp. détectées</p>
                    </div>
                    <div className="bg-black border border-white/20 p-4 text-center">
                      <p className="text-2xl font-light" style={{color: '#74a6be'}}>42j</p>
                      <p className="text-sm text-white/60">Délai moyen</p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="order-1 md:order-2">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 text-white font-light text-2xl flex items-center justify-center" style={{backgroundColor: '#a7292e'}}>
                    2
                  </div>
                  <h3 className="text-3xl font-light text-white">
                    Prédictions intelligentes
                  </h3>
                </div>
                <p className="text-lg font-light text-white/70 mb-6 leading-relaxed">
                  On ajoute l'IA pour prédire votre cash flow, identifier les patterns de ventes 
                  et anticiper les problèmes avant qu'ils arrivent.
                </p>
                <ul className="space-y-3 text-white/60 font-light">
                  <li className="flex items-center gap-3">
                    <div className="w-2 h-2" style={{backgroundColor: '#a7292e'}}></div>
                    Prédiction cash flow 30/60/90 jours
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-2 h-2" style={{backgroundColor: '#a7292e'}}></div>
                    Probabilité de conversion des prospects
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-2 h-2" style={{backgroundColor: '#a7292e'}}></div>
                    Détection automatique d'anomalies
                  </li>
                </ul>
              </div>
            </div>

            {/* Step 3 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 text-white font-light text-2xl flex items-center justify-center" style={{backgroundColor: '#a7292e'}}>
                    3
                  </div>
                  <h3 className="text-3xl font-light text-white">
                    Optimisation continue
                  </h3>
                </div>
                <p className="text-lg font-light text-white/70 mb-6 leading-relaxed">
                  On intègre tous vos processus pour une vue 360°. Le système apprend de vos 
                  décisions et s'améliore automatiquement.
                </p>
                <ul className="space-y-3 text-white/60 font-light">
                  <li className="flex items-center gap-3">
                    <div className="w-2 h-2" style={{backgroundColor: '#a7292e'}}></div>
                    Recommandations d'actions spécifiques
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-2 h-2" style={{backgroundColor: '#a7292e'}}></div>
                    Optimisation automatique des processus
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-2 h-2" style={{backgroundColor: '#a7292e'}}></div>
                    Tableau de bord exécutif temps réel
                  </li>
                </ul>
              </div>
              <div className="bg-black border border-white/20 p-6">
                <div className="space-y-4">
                  <div className="bg-white border-l-4 p-3" style={{borderLeftColor: '#74a6be'}}>
                    <p className="text-black text-sm font-light">
                      💡 <strong>RECOMMANDATION:</strong> Relancer client XYZ avant vendredi
                    </p>
                  </div>
                  <div className="bg-white border-l-4 p-3" style={{borderLeftColor: '#74a6be'}}>
                    <p className="text-black text-sm font-light">
                      ✅ <strong>ACTION:</strong> Crédit fournisseur négocié (+15 jours)
                    </p>
                  </div>
                  <div className="bg-white border-l-4 p-3" style={{borderLeftColor: '#a7292e'}}>
                    <p className="text-black text-sm font-light">
                      🎯 <strong>OPTIMISATION:</strong> Process commandes +12% plus rapide
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom CTA */}
          <div className="text-center mt-16">
            <p className="text-xl font-light text-white/70 mb-8">
              Chaque étape vous donne de la valeur immédiate.
            </p>
            <a
              href="#pricing"
              className="inline-block text-white px-8 py-4 font-light transition-all hover:scale-105"
              style={{backgroundColor: '#a7292e'}}
            >
              Voir les prix et commencer
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}