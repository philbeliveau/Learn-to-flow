export default function Contact() {
  return (
    <section id="contact" className="py-20 bg-black">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-8">
              Prêt à transformer votre PME ?
            </h2>
            <p className="text-xl text-gray-300">
              Démarrez votre transformation digitale dès aujourd'hui
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <h3 className="text-2xl font-bold text-white mb-6">
                Parlons de votre projet
              </h3>
              
              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-sm">📧</span>
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-2">Email</h4>
                    <p className="text-gray-300">philippebeliveau@ezbi.ca</p>
                    <p className="text-sm text-gray-400">Réponse sous 24h</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-sm">📱</span>
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-2">Démonstration</h4>
                    <p className="text-gray-300">Demandez une démo personnalisée</p>
                    <p className="text-sm text-gray-400">30 minutes pour découvrir EZBI</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-sm">🏢</span>
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-2">Siège social</h4>
                    <p className="text-gray-300">Montréal, Quebec, Canada</p>
                    <p className="text-sm text-gray-400">Service client France</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-8 p-6 bg-gradient-to-br from-blue-900/30 to-purple-900/30 backdrop-blur-lg rounded-xl border border-blue-500/30">
                <h4 className="text-white font-bold mb-3">🎯 Audit gratuit</h4>
                <p className="text-gray-300 text-sm mb-4">
                  Nous analysons gratuitement vos données sur 30 jours pour identifier 
                  vos opportunités d'optimisation.
                </p>
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                  Demander un audit
                </button>
              </div>
            </div>
            
            <div>
              <div className="bg-gray-900 rounded-xl p-8 border border-gray-700">
                <h3 className="text-xl font-bold text-white mb-6">
                  Contactez-nous
                </h3>
                
                <form className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Nom de l'entreprise *
                    </label>
                    <input
                      type="text"
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                      placeholder="Votre PME manufacturière"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Email professionnel *
                    </label>
                    <input
                      type="email"
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                      placeholder="dirigeant@votrepme.fr"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Nombre d'employés
                    </label>
                    <select className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white">
                      <option value="">Sélectionner</option>
                      <option value="10-50">10-50 employés</option>
                      <option value="50-100">50-100 employés</option>
                      <option value="100-250">100-250 employés</option>
                      <option value="250+">250+ employés</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Votre défi principal
                    </label>
                    <textarea
                      rows={4}
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                      placeholder="Décrivez votre problématique de trésorerie ou production..."
                    ></textarea>
                  </div>
                  
                  <button
                    type="submit"
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-all transform hover:scale-105"
                  >
                    Envoyer ma demande
                  </button>
                </form>
                
                <p className="text-xs text-gray-400 mt-4 text-center">
                  En envoyant ce formulaire, vous acceptez d'être contacté par EZBI Analytics. 
                  Vos données sont protégées selon le RGPD.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}