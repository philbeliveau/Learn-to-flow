export default function Footer() {
  return (
    <footer className="bg-gray-900 border-t border-gray-800">
      <div className="container mx-auto px-4 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-xl font-bold text-white mb-4">🏭 EZBI Analytics</h3>
            <p className="text-gray-400 mb-4">
              Intelligence manufacturière pour PME françaises. 
              Anticipez vos défis avec l'IA.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                LinkedIn
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                Twitter
              </a>
            </div>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">Solutions</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Cash Flow Radar</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Manufacturing Intelligence</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Early Warning System</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Slack Integration</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">Ressources</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Documentation</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Guides PME</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Études de cas</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Blog</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">Support</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Centre d'aide</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Nous contacter</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Formation</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Statut API</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-800 mt-8 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-gray-400 text-sm">
              © 2024 EZBI Analytics. Tous droits réservés.
            </div>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <a href="#" className="text-gray-400 hover:text-white transition-colors text-sm">
                Mentions légales
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors text-sm">
                Politique de confidentialité
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors text-sm">
                RGPD
              </a>
            </div>
          </div>
          
          <div className="mt-4 text-center">
            <p className="text-xs text-gray-500">
              Hébergé en France • Conforme RGPD • Chiffrement AES-256 • Support français
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}