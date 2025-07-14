export default function Header() {
  return (
    <header className="bg-black/90 backdrop-blur-lg border-b border-white/10 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-white">🏭 EZBI Analytics</h1>
            <div className="text-sm text-gray-400">
              Intelligence Manufacturière
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <a href="#services" className="text-gray-300 hover:text-white transition-colors">
              Services
            </a>
            <a href="#about" className="text-gray-300 hover:text-white transition-colors">
              À propos
            </a>
            <a href="#contact" className="text-gray-300 hover:text-white transition-colors">
              Contact
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}