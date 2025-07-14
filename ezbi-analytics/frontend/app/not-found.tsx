export default function NotFound() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="text-center">
        <div className="text-8xl mb-8">🏭</div>
        <h1 className="text-6xl font-bold mb-4">404</h1>
        <h2 className="text-2xl text-gray-300 mb-8">Page non trouvée</h2>
        <p className="text-gray-400 mb-8 max-w-md mx-auto">
          La page que vous recherchez n'existe pas ou a été déplacée.
        </p>
        <a 
          href="/"
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg font-medium transition-colors inline-block"
        >
          Retour à l'accueil
        </a>
      </div>
    </div>
  );
}