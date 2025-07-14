export default function Hero() {
  return (
    <section className="min-h-screen bg-black flex items-center justify-center">
      <div className="container mx-auto px-4 text-center">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-6xl md:text-7xl font-light text-white mb-8 tracking-tight">
            Arrêtez de gérer votre PME
            <br />
            <span style={{color: '#a7292e'}}>à l'aveugle</span>
          </h1>
          <p className="text-xl md:text-2xl font-light text-gray-300 mb-12 max-w-4xl mx-auto leading-relaxed">
            Transformez vos données Excel et QuickBooks en alertes intelligentes Slack.
            <br />
            Système d'alerte précoce pour PME québécoises.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-20">
            <a
              href="#contact"
              className="text-white px-8 py-4 font-light transition-all hover:scale-105"
              style={{backgroundColor: '#a7292e'}}
            >
              Évaluation gratuite
            </a>
            <a
              href="#services"
              className="border border-gray-600 hover:border-gray-400 text-white px-8 py-4 font-light transition-all hover:scale-105"
            >
              Voir nos solutions
            </a>
          </div>

          {/* Slack Integration Preview */}
          <div className="bg-gray-900 border border-gray-700 p-8 max-w-2xl mx-auto">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-6 h-6 rounded" style={{backgroundColor: '#74a6be'}}></div>
              <span className="text-white font-light">#finance-alerts</span>
            </div>
            <div className="text-left space-y-3">
              <div className="bg-white border-l-4 p-3" style={{borderLeftColor: '#a7292e'}}>
                <p className="text-black text-sm font-light">
                  🚨 <strong>ALERTE TRÉSORERIE</strong> - Position cash: -15,450$ dans 7 jours
                </p>
              </div>
              <div className="bg-white border-l-4 p-3" style={{borderLeftColor: '#74a6be'}}>
                <p className="text-black text-sm font-light">
                  ⚠️ <strong>VENTES EN BAISSE</strong> - Pipeline: -23% vs mois dernier
                </p>
              </div>
              <div className="bg-white border-l-4 p-3" style={{borderLeftColor: '#74a6be'}}>
                <p className="text-black text-sm font-light">
                  💡 <strong>OPPORTUNITÉ</strong> - Client ABC: facture de 45,000$ en retard
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}