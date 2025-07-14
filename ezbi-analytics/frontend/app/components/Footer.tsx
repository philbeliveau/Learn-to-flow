export default function Footer() {
  return (
    <footer className="bg-gray-900 border-t border-gray-700">
      <div className="container mx-auto px-4 py-16">
        {/* Main Footer Content */}
        <div className="grid md:grid-cols-3 gap-12 mb-12">
          {/* Company Info */}
          <div>
            <div className="flex items-center gap-2 mb-6">
              <span className="text-2xl font-light" style={{color: '#74a6be'}}>E</span>
              <span className="text-2xl font-light" style={{color: '#74a6be'}}>Z</span>
              <span className="text-2xl font-light" style={{color: '#a7292e'}}>B</span>
              <span className="text-2xl font-light" style={{color: '#a7292e'}}>I</span>
              <span className="text-xl font-light text-white ml-2">Analytics</span>
            </div>
            <p className="text-gray-400 font-light leading-relaxed mb-6">
              Intelligence d'affaires pour PME québécoises.
              <br />
              Transformez vos données en décisions éclairées.
            </p>
            <div className="space-y-2 text-sm font-light text-gray-400">
              <div>Montréal, QC</div>
              <div>info@ezbi-analytics.ca</div>
              <div>+1 (514) 555-EZBI</div>
            </div>
          </div>
          
          {/* Solutions */}
          <div>
            <h4 className="text-lg font-light text-white mb-6">Solutions</h4>
            <ul className="space-y-3 font-light">
              <li><a href="#services" className="text-gray-400 hover:text-white transition-colors">Évaluation gratuite</a></li>
              <li><a href="#services" className="text-gray-400 hover:text-white transition-colors">Surveillance cash flow</a></li>
              <li><a href="#services" className="text-gray-400 hover:text-white transition-colors">Intelligence complète</a></li>
              <li><a href="#services" className="text-gray-400 hover:text-white transition-colors">Pilote sur mesure</a></li>
              <li><a href="#login-section" className="text-gray-400 hover:text-white transition-colors">Accès dashboard</a></li>
            </ul>
          </div>
          
          {/* Resources & Support */}
          <div>
            <h4 className="text-lg font-light text-white mb-6">Ressources</h4>
            <ul className="space-y-3 font-light">
              <li><a href="#contact" className="text-gray-400 hover:text-white transition-colors">Nous contacter</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Centre d'aide</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Guides PME</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Cas d'usage</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Documentation API</a></li>
            </ul>
          </div>
        </div>
        
        {/* Call to Action */}
        <div className="border-t border-gray-700 pt-12 mb-12">
          <div className="text-center">
            <h3 className="text-2xl font-light text-white mb-4">
              Prêt à reprendre le contrôle de votre PME?
            </h3>
            <p className="text-gray-400 font-light mb-8 max-w-2xl mx-auto">
              Commencez par une évaluation gratuite de vos données. 
              Aucun engagement, des résultats concrets en 48h.
            </p>
            <a
              href="#contact"
              className="inline-block text-white px-8 py-4 font-light transition-all hover:scale-105"
              style={{backgroundColor: '#a7292e'}}
            >
              Réserver mon évaluation gratuite
            </a>
          </div>
        </div>
        
        {/* Bottom Footer */}
        <div className="border-t border-gray-700 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-gray-400 text-sm font-light">
              © 2024 EZBI Analytics. Tous droits réservés.
            </div>
            <div className="flex flex-wrap gap-6 text-sm font-light">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                Confidentialité
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                Conditions
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                PIPEDA
              </a>
            </div>
          </div>
          
          <div className="mt-6 text-center">
            <p className="text-xs font-light text-gray-500">
              Hébergé au Canada • Conforme PIPEDA • Données sécurisées • Support en français
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}