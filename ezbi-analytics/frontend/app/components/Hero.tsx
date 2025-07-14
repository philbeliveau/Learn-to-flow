export default function Hero() {
  return (
    <section className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-800 flex items-center justify-center">
      <div className="container mx-auto px-4 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="hero-title text-white mb-6 animate-fade-in-up">
            Plateforme d'Intelligence Manufacturière
          </h1>
          <p className="hero-subtitle text-white/90 mb-8 animate-fade-in-up">
            Solution IA de prédiction de trésorerie pour les PME manufacturières françaises
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12 animate-fade-in-up">
            <a
              href="#services"
              className="bg-gradient-to-r from-red-600 to-blue-600 text-white px-8 py-4 rounded-lg font-medium hover:scale-105 transition-transform"
            >
              Découvrir nos services
            </a>
            <a
              href="#contact"
              className="border border-white/30 text-white px-8 py-4 rounded-lg font-medium hover:bg-white/10 transition-colors"
            >
              Nous contacter
            </a>
          </div>
          
          {/* Key Stats */}
          <div className="grid md:grid-cols-3 gap-6 mt-16">
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <div className="text-4xl mb-4">🤖</div>
              <h3 className="text-xl font-bold mb-3 text-white">IA Prédictive</h3>
              <p className="text-white/80 mb-4">Modèles Prophet + LSTM avec 87% de confiance</p>
              <div className="text-sm text-blue-300 font-medium">
                ✓ 218K+ enregistrements réels
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-3 text-white">Analytics Manufacturier</h3>
              <p className="text-white/80 mb-4">KPIs de production, qualité et efficacité</p>
              <div className="text-sm text-green-300 font-medium">
                ✓ Temps réel + historique
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <div className="text-4xl mb-4">🇫🇷</div>
              <h3 className="text-xl font-bold mb-3 text-white">Conformité Française</h3>
              <p className="text-white/80 mb-4">SIRET/SIREN, RGPD, EUR</p>
              <div className="text-sm text-purple-300 font-medium">
                ✓ PME manufacturing ready
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}