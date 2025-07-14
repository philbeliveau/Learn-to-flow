export default function Problems() {
  return (
    <section id="problems" className="py-20 bg-gray-900">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-8">
            Les défis des PME manufacturières
          </h2>
          <p className="text-xl text-gray-300 mb-12">
            85% des PME françaises font face à des surprises financières qui menacent leur survie
          </p>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-8">
              <div className="text-5xl mb-4">⚠️</div>
              <h3 className="text-2xl font-bold text-red-400 mb-4">Prédiction de trésorerie</h3>
              <p className="text-gray-300">
                Les outils Excel et les estimations manuelles ne suffisent plus. 
                Les délais de paiement imprévisibles et les variations de production 
                créent des surprises financières fatales.
              </p>
            </div>
            
            <div className="bg-orange-900/20 border border-orange-500/30 rounded-xl p-8">
              <div className="text-5xl mb-4">📉</div>
              <h3 className="text-2xl font-bold text-orange-400 mb-4">Visibilité limitée</h3>
              <p className="text-gray-300">
                Les données de production, ventes et finance sont isolées. 
                Impossible d'anticiper les impacts en cascade d'une commande 
                ou d'un retard de livraison.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}