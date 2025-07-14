import Link from 'next/link';

export default function TresoreriePage() {
  const capabilities = [
    {
      icon: '🔍',
      title: 'Surveillance continue des liquidités',
      description: 'Calculs automatiques des pistes de liquidités basés sur vos revenus prédits et dépenses courantes. Le système peut projeter votre situation financière jusqu\'à 90 jours à l\'avance.'
    },
    {
      icon: '⏰',
      title: 'Détection précoce des retards',
      description: 'Surveillance automatique des délais de paiement avec calculs statistiques pour identifier les patterns de retard avant qu\'ils deviennent problématiques.'
    },
    {
      icon: '📱',
      title: 'Visibilité en temps réel',
      description: 'Dashboard centralisé avec alertes Slack automatiques pour les événements critiques. Accès mobile pour suivre les métriques importantes où que vous soyez.'
    },
    {
      icon: '▲',
      title: 'Analyse prédictive',
      description: 'Le système analyse les patterns de paiement de vos clients et détecte les signaux précoces de difficultés financières jusqu\'à 60 jours à l\'avance.'
    }
  ];

  const features = [
    'Connexion QuickBooks + alertes Slack',
    'Calculs de réserve et prévisions 90 jours',
    'Alertes de paiements en retard',
    'Détection de patterns de paiement client',
    'Projections de trésorerie automatisées',
    'Recommandations d\'actions prioritaires'
  ];

  const results = [
    {
      metric: '47 jours',
      description: 'Délai moyen d\'alerte avant épuisement de trésorerie'
    },
    {
      metric: '78%',
      description: 'Réduction du temps passé à analyser les finances'
    },
    {
      metric: '23 jours',
      description: 'Détection précoce des retards de paiement'
    }
  ];

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-white/10 py-4">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <Link href="/" className="text-2xl font-light text-white hover:text-blue-300 transition-colors">
            EZBI
          </Link>
          <Link href="/#pricing" className="text-gray-300 hover:text-white transition-colors font-light">
            ← Retour aux offres
          </Link>
        </div>
      </header>

      <main className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          {/* Hero Section */}
          <div className="text-center mb-20">
            <h1 className="text-4xl md:text-6xl font-light tracking-tight mb-6">
              Surveillance Trésorerie
            </h1>
            <p className="text-xl text-gray-300 font-light max-w-3xl mx-auto mb-8">
              Éliminez l'incertitude financière avec une surveillance continue et des alertes intelligentes
            </p>
            <div className="text-3xl font-light text-blue-300">
              2 500$ <span className="text-lg text-gray-400">/mois</span>
            </div>
          </div>

          {/* Results Section */}
          <div className="mb-20">
            <h2 className="text-3xl font-light mb-12 text-center">Résultats concrets pour votre PME</h2>
            <div className="grid md:grid-cols-3 gap-8">
              {results.map((result, index) => (
                <div key={index} className="bg-blue-500/10 border border-blue-400/20 rounded-lg p-8 text-center">
                  <div className="text-4xl font-light text-blue-300 mb-4">{result.metric}</div>
                  <p className="text-gray-300 font-light">{result.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Capabilities Section */}
          <div className="mb-20">
            <h2 className="text-3xl font-light mb-12 text-center">Capacités du système</h2>
            <div className="grid lg:grid-cols-2 gap-8">
              {capabilities.map((capability, index) => (
                <div key={index} className="bg-white/5 border border-white/10 rounded-lg p-8">
                  <div className="flex items-start space-x-4">
                    <div className="text-4xl flex-shrink-0">{capability.icon}</div>
                    <div>
                      <h3 className="text-xl font-medium text-white mb-3">{capability.title}</h3>
                      <p className="text-gray-300 font-light leading-relaxed">{capability.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Features Included */}
          <div className="mb-20">
            <h2 className="text-3xl font-light mb-12 text-center">Fonctionnalités incluses</h2>
            <div className="bg-white/5 border border-white/10 rounded-lg p-8 max-w-4xl mx-auto">
              <div className="grid md:grid-cols-2 gap-6">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-start">
                    <span className="text-green-400 mr-3 mt-1 flex-shrink-0">✓</span>
                    <span className="text-gray-300 font-light">{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Technology Section */}
          <div className="mb-20">
            <h2 className="text-3xl font-light mb-12 text-center">Technologie basée sur l'analyse prédictive</h2>
            <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-400/20 rounded-lg p-8">
              <p className="text-lg text-gray-200 font-light leading-relaxed text-center">
                Le système analyse les patterns de paiement de vos clients et détecte les signaux précoces de difficultés financières. 
                Les algorithmes peuvent identifier des changements de comportement jusqu'à 60 jours avant qu'un client signale 
                officiellement des problèmes de paiement.
              </p>
            </div>
          </div>

          {/* CTA Section */}
          <div className="text-center">
            <div className="bg-white/10 border border-white/20 rounded-lg p-12 max-w-4xl mx-auto">
              <h3 className="text-2xl font-light mb-6">Prêt à sécuriser votre trésorerie?</h3>
              <p className="text-gray-300 font-light mb-8">
                Commencez par une évaluation gratuite pour analyser vos flux de trésorerie actuels
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a 
                  href="mailto:philippebeliveau@ezbi.ca?subject=Surveillance Trésorerie - Demande d'information&body=Bonjour Philippe,%0D%0A%0D%0AJe suis intéressé par le service de Surveillance Trésorerie à 2,500$/mois.%0D%0A%0D%0ANom de l'entreprise: %0D%0ARevenu annuel approximatif: %0D%0ALogiciel comptable utilisé: %0D%0A%0D%0AMerci!"
                  className="inline-flex items-center px-8 py-3 text-white bg-blue-600 hover:bg-blue-700 transition-colors font-light rounded"
                >
                  Commencer maintenant
                </a>
                <Link 
                  href="/#contact"
                  className="inline-flex items-center px-8 py-3 text-white border border-white/20 hover:border-white/40 transition-colors font-light rounded"
                >
                  Évaluation gratuite
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}