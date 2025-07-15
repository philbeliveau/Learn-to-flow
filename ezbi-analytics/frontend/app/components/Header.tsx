'use client';

export default function Header() {
  const scrollToLogin = () => {
    const loginSection = document.getElementById('login-section');
    if (loginSection) {
      loginSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="bg-black border-b border-gray-800 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <span className="text-3xl font-light" style={{color: '#74a6be'}}>E</span>
              <span className="text-3xl font-light" style={{color: '#74a6be'}}>Z</span>
              <span className="text-3xl font-light" style={{color: '#a7292e'}}>B</span>
              <span className="text-3xl font-light" style={{color: '#a7292e'}}>I</span>
            </div>
            <div className="ml-2">
              <div className="text-lg font-light text-white">Analytics</div>
              <div className="text-xs font-light text-gray-400">Intelligence d'affaires pour PME</div>
            </div>
          </div>
          
          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <a href="#problems" className="text-gray-300 hover:text-white font-light transition-colors">
              Problèmes
            </a>
            <a href="#services" className="text-gray-300 hover:text-white font-light transition-colors">
              Solutions
            </a>
            <a href="#pricing" className="text-gray-300 hover:text-white font-light transition-colors">
              Prix
            </a>
            <a href="#contact" className="text-gray-300 hover:text-white font-light transition-colors">
              Contact
            </a>
            <button 
              onClick={scrollToLogin}
              className="text-white px-6 py-2 font-light transition-all hover:scale-105"
              style={{backgroundColor: '#a7292e'}}
              onMouseEnter={(e) => (e.target as HTMLButtonElement).style.backgroundColor = '#8a1f24'}
              onMouseLeave={(e) => (e.target as HTMLButtonElement).style.backgroundColor = '#a7292e'}
            >
              Connexion
            </button>
            <a
              href="/services/intelligence-complete"
              className="text-white px-4 py-2 border border-gray-600 hover:border-white font-light transition-all hover:scale-105"
            >
              Services
            </a>
          </nav>
          
          {/* Mobile Menu Button */}
          <button className="md:hidden text-white">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}