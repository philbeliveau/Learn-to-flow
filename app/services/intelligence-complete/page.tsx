import Link from 'next/link';

export default function IntelligenceCompletePage() {
  const capabilities = [
    {
      icon: '🔍',
      title: 'Surveillance continue des liquidités',
      description: 'Calculs automatiques des pistes de liquidités basés sur vos revenus prédits et dépenses courantes. Le système peut projeter votre situation financière jusqu\'à 90 jours à l\'avance.'
    },
    {
      icon: '▲',
      title: 'Analyse du pipeline de ventes',
      description: 'Identification des affaires stagnantes par analyse de patterns de communication et de délais. Les algorithmes détectent les changements de vélocité dans votre processus de vente.'
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
      icon: '◎',
      title: 'Qualification prospects IA',
      description: 'Scoring automatique des prospects basé sur des modèles prédictifs pour optimiser vos efforts de vente et maximiser votre taux de conversion.'
    },
    {
      icon: '↗',
      title: 'Modèles prédictifs avancés',
      description: 'Analyses saisonnières, cycliques et de tendance pour anticiper les fluctuations de votre activité et prendre des décisions éclairées.'
    }
  ];

  const features = [
    'Trésorerie + pipeline + prospects',
    'Analyse prédictive avancée',
    'Recommandations d\'actions optimisées',
    'Intégration Slack complète',
    'Scoring IA des prospects',
    'Modèles saisonniers et cycliques',
    'Alertes multi-niveaux personnalisées',
    'Dashboard temps réel mobile',
    'Support prioritaire',
    'Optimisations trimestrielles'
  ];

  const results = [
    {
      metric: '87%',
      description: 'Amélioration de la précision des prévisions de vente'
    },
    {
      metric: '65%',
      description: 'Réduction du temps d\'analyse manuelle'
    },
    {
      metric: '34%',
      description: 'Augmentation du taux de conversion prospects'
    },
    {
      metric: '90 jours',
      description: 'Visibilité financière avancée garantie'
    }
  ];

  const workflows = [
    {
      title: 'Matinée Executive',
      description: 'Réveil avec un rapport Slack personnalisé: trésorerie, deals prioritaires, prospects chauds'
    },
    {
      title: 'Alertes Proactives',
      description: 'Notifications automatiques avant les problèmes: clients à risque, pipeline ralenti, trésorerie tendue'
    },
    {
      title: 'Décisions Éclairées',
      description: 'Recommandations IA basées sur vos données: quels prospects prioriser, quels clients relancer'
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
            <div className="inline-block bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-medium mb-4">
              SOLUTION COMPLÈTE
            </div>
            <h1 className="text-4xl md:text-6xl font-light tracking-tight mb-6">
              Intelligence Complète
            </h1>
            <p className="text-xl text-gray-300 font-light max-w-3xl mx-auto mb-8">
              La solution tout-en-un pour une visibilité totale sur votre entreprise
            </p>
            <div className="text-3xl font-light text-blue-300">
              4 500$ <span className="text-lg text-gray-400">/mois</span>
            </div>
          </div>

          {/* Results Section */}
          <div className="mb-20">
            <h2 className="text-3xl font-light mb-12 text-center">Impact mesurable sur votre performance</h2>
            <div className="grid md:grid-cols-4 gap-6">
              {results.map((result, index) => (
                <div key={index} className="bg-blue-500/10 border border-blue-400/20 rounded-lg p-6 text-center">
                  <div className="text-3xl font-light text-blue-300 mb-3">{result.metric}</div>
                  <p className="text-gray-300 font-light text-sm">{result.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Workflow Section */}
          <div className="mb-20">
            <h2 className="text-3xl font-light mb-12 text-center">Votre nouveau workflow quotidien</h2>
            <div className="grid lg:grid-cols-3 gap-8">
              {workflows.map((workflow, index) => (
                <div key={index} className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-400/20 rounded-lg p-8">
                  <h3 className="text-xl font-medium text-blue-300 mb-4">{workflow.title}</h3>
                  <p className="text-gray-300 font-light leading-relaxed">{workflow.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Capabilities Section */}
          <div className="mb-20">
            <h2 className="text-3xl font-light mb-12 text-center">Capacités système complètes</h2>
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
            <h2 className="text-3xl font-light mb-12 text-center">Tout ce qui est inclus</h2>
            <div className="bg-white/5 border border-white/10 rounded-lg p-8 max-w-5xl mx-auto">
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
            <h2 className="text-3xl font-light mb-12 text-center">Technologie IA de pointe</h2>
            <div className="grid lg:grid-cols-2 gap-8">
              <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-400/20 rounded-lg p-8">
                <h3 className="text-xl font-medium text-blue-300 mb-4">Machine Learning Adaptatif</h3>
                <p className="text-gray-300 font-light leading-relaxed">
                  Nos algorithmes apprennent continuellement de vos données pour affiner les prédictions et 
                  s'adapter aux spécificités de votre secteur et cycles d'affaires.
                </p>
              </div>
              <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-400/20 rounded-lg p-8">
                <h3 className="text-xl font-medium text-purple-300 mb-4">Analyses Multi-Dimensionnelles</h3>
                <p className="text-gray-300 font-light leading-relaxed">
                  Corrélations entre trésorerie, pipeline, prospects et facteurs externes pour une vision 
                  360° de votre performance et des risques.
                </p>
              </div>
            </div>
          </div>

          {/* Comparison */}
          <div className="mb-20">
            <h2 className="text-3xl font-light mb-12 text-center">Surveillance vs Intelligence Complète</h2>
            <div className="grid lg:grid-cols-2 gap-8">
              <div className="bg-white/5 border border-white/10 rounded-lg p-8">
                <h3 className="text-xl font-medium text-gray-300 mb-6">Surveillance (2 500$/mois)</h3>
                <ul className="space-y-3">
                  <li className="text-gray-400 font-light">• Trésorerie uniquement</li>
                  <li className="text-gray-400 font-light">• Alertes basiques</li>
                  <li className="text-gray-400 font-light">• Rapports standards</li>
                </ul>
              </div>
              <div className="bg-blue-500/10 border border-blue-400/20 rounded-lg p-8">
                <h3 className="text-xl font-medium text-blue-300 mb-6">Intelligence Complète (4 500$/mois)</h3>
                <ul className="space-y-3">
                  <li className="text-blue-200 font-light">• Trésorerie + Pipeline + Prospects</li>
                  <li className="text-blue-200 font-light">• IA prédictive avancée</li>
                  <li className="text-blue-200 font-light">• Recommandations optimisées</li>
                  <li className="text-blue-200 font-light">• Support prioritaire</li>
                </ul>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="text-center">
            <div className="bg-white/10 border border-white/20 rounded-lg p-12 max-w-4xl mx-auto">
              <h3 className="text-2xl font-light mb-6">Transformez votre entreprise avec l'IA</h3>
              <p className="text-gray-300 font-light mb-8">
                Rejoignez les PME qui ont déjà adopté l'intelligence artificielle pour prendre des décisions éclairées
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a 
                  href="mailto:philippebeliveau@ezbi.ca?subject=Intelligence Complète - Demande d'information&body=Bonjour Philippe,%0D%0A%0D%0AJe suis intéressé par la solution Intelligence Complète à 4,500$/mois.%0D%0A%0D%0ANom de l'entreprise: %0D%0ARevenu annuel approximatif: %0D%0ANombre d'employés: %0D%0ALogiciels actuels (CRM, comptabilité): %0D%0A%0D%0AMerci!"
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