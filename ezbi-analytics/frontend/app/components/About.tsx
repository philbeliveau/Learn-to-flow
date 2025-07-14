export default function About() {
  return (
    <section id="about" className="py-20 bg-gray-800">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-8">
            À propos d'EZBI Analytics
          </h2>
          <p className="text-xl text-gray-300 mb-12">
            Experts en intelligence manufacturière pour les PME françaises
          </p>
          
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="text-left">
              <h3 className="text-2xl font-bold text-white mb-6">Notre mission</h3>
              <p className="text-gray-300 mb-6">
                Nous aidons les PME manufacturières françaises à anticiper leurs défis 
                financiers et opérationnels grâce à l'intelligence artificielle.
              </p>
              
              <p className="text-gray-300 mb-6">
                Fondée par des experts en IA et manufacturing, EZBI Analytics combine 
                une connaissance approfondie du secteur industriel français avec les 
                technologies les plus avancées.
              </p>
              
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-gray-300">15+ années d'expérience manufacturing</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-300">Expertise IA et machine learning</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                  <span className="text-gray-300">Spécialisation PME françaises</span>
                </div>
              </div>
            </div>
            
            <div>
              <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 backdrop-blur-lg rounded-xl p-8 border border-blue-500/30">
                <h4 className="text-xl font-bold text-white mb-6">Nos résultats</h4>
                
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-black/30 rounded-lg">
                    <span className="text-gray-300">Réduction surprises financières</span>
                    <span className="text-green-400 font-bold">-78%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-black/30 rounded-lg">
                    <span className="text-gray-300">Amélioration trésorerie</span>
                    <span className="text-blue-400 font-bold">+24%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-black/30 rounded-lg">
                    <span className="text-gray-300">Optimisation production</span>
                    <span className="text-purple-400 font-bold">+31%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-black/30 rounded-lg">
                    <span className="text-gray-300">ROI moyen sur 12 mois</span>
                    <span className="text-orange-400 font-bold">247%</span>
                  </div>
                </div>
                
                <div className="mt-6 p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
                  <p className="text-sm text-green-300">
                    <strong>Témoignage:</strong> "EZBI nous a évité 3 crises de trésorerie 
                    majeures cette année. Un ROI exceptionnel." - PME Métallurgie, 45 employés
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}