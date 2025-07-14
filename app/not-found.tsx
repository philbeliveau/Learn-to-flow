import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-light mb-4">404</h1>
        <h2 className="text-2xl font-light mb-8">Page non trouvée</h2>
        <Link 
          href="/" 
          className="inline-flex items-center px-8 py-3 text-white transition-colors font-light rounded"
          style={{ backgroundColor: '#a7292e' }}
        >
          Retour à l'accueil
        </Link>
      </div>
    </div>
  );
}