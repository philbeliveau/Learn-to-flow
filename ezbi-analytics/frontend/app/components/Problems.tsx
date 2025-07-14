export default function Problems() {
  return (
    <section id="problems" className="py-20 bg-black">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-light text-white mb-16 text-center tracking-tight">
            Les 3 problèmes qui tuent les PME
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {/* Problem 1 */}
            <div className="bg-black border border-gray-700 p-8 hover:scale-105 transition-transform duration-300">
              <div className="w-16 h-16 flex items-center justify-center mb-6" style={{backgroundColor: '#a7292e'}}>
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
              <h3 className="text-2xl font-light text-white mb-4">
                Données éparpillées
              </h3>
              <p className="text-gray-400 font-light leading-relaxed">
                Vos données critiques sont dans Excel, QuickBooks, votre CRM, 
                et dans la tête de vos employés. Impossible de voir le portrait global.
              </p>
            </div>

            {/* Problem 2 */}
            <div className="bg-black border border-gray-700 p-8 hover:scale-105 transition-transform duration-300">
              <div className="w-16 h-16 flex items-center justify-center mb-6" style={{backgroundColor: '#a7292e'}}>
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                </svg>
              </div>
              <h3 className="text-2xl font-light text-white mb-4">
                Cash flow imprévisible
              </h3>
              <p className="text-gray-400 font-light leading-relaxed">
                Vous découvrez vos problèmes de trésorerie quand il est trop tard. 
                Les surprises financières vous empêchent de dormir.
              </p>
            </div>

            {/* Problem 3 */}
            <div className="bg-black border border-gray-700 p-8 hover:scale-105 transition-transform duration-300">
              <div className="w-16 h-16 flex items-center justify-center mb-6" style={{backgroundColor: '#a7292e'}}>
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M9 11H7v9h2v-9zm4 0h-2v9h2v-9zm4 0h-2v9h2v-9zm2-7H3v2h18V4zM4 6v2h16V6H4zm1 4v10h14V10H5z"/>
                </svg>
              </div>
              <h3 className="text-2xl font-light text-white mb-4">
                Pipeline de ventes opaque
              </h3>
              <p className="text-gray-400 font-light leading-relaxed">
                Vous ne savez pas vraiment quelles opportunités vont se concrétiser. 
                Vos prévisions de revenus sont des guéti-games.
              </p>
            </div>
          </div>

          {/* Bottom CTA */}
          <div className="text-center mt-16">
            <p className="text-xl font-light text-gray-300 mb-8">
              <span style={{color: '#a7292e'}}>Résultat :</span> Vous réagissez au lieu d'agir.
            </p>
            <a
              href="#services"
              className="inline-block text-white px-8 py-4 font-light transition-all hover:scale-105"
              style={{backgroundColor: '#a7292e'}}
            >
              Voir comment on règle ça
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}