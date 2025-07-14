'use client';

import { useState } from 'react';

interface LoginSectionProps {
  onLogin: (user: any) => void;
  apiStatus: string;
}

export default function LoginSection({ onLogin, apiStatus }: LoginSectionProps) {
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8004/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData)
      });
      
      if (!response.ok) {
        throw new Error('Identifiants invalides');
      }
      
      const data = await response.json();
      
      if (data.access_token && data.user) {
        // Store the access token
        localStorage.setItem('access_token', data.access_token);
        onLogin(data.user);
      } else {
        alert('Erreur de connexion: Format de réponse invalide');
      }
    } catch (error) {
      alert('Erreur de connexion: ' + (error instanceof Error ? error.message : 'Backend non disponible'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="login-section" className="py-20 bg-black">
      <div className="container mx-auto px-4">
        <div className="max-w-md mx-auto bg-black border border-white/20 p-8">
          {/* EZBI Logo */}
          <div className="text-center mb-8">
            <div className="flex justify-center items-center gap-1 mb-4">
              <span className="text-4xl font-light" style={{color: '#74a6be'}}>E</span>
              <span className="text-4xl font-light" style={{color: '#74a6be'}}>Z</span>
              <span className="text-4xl font-light" style={{color: '#a7292e'}}>B</span>
              <span className="text-4xl font-light" style={{color: '#a7292e'}}>I</span>
            </div>
            <h2 className="text-2xl font-light text-white">
              Accès Analytics
            </h2>
          </div>

          {/* API Status */}
          <div className="flex items-center gap-2 mb-6">
            <div className={`w-2 h-2 rounded-full ${
              apiStatus === 'online' ? 'bg-white' : 
              apiStatus === 'offline' ? 'bg-white/30' : 
              'bg-white/60 animate-pulse'
            }`}></div>
            <span className="text-sm font-light text-white/70">
              {apiStatus === 'online' ? 'Système en ligne' : 
               apiStatus === 'offline' ? 'Hors ligne' : 
               'Vérification...'}
            </span>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-light mb-2 text-white/70">Email</label>
              <input
                type="email"
                className="w-full px-4 py-4 bg-black border border-white/30 focus:border-white/60 text-white placeholder-white/40 font-light"
                style={{backgroundColor: 'black'}}
                value={loginData.email}
                onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                placeholder="demo@ezbi.fr"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-light mb-2 text-white/70">Mot de passe</label>
              <input
                type="password"
                className="w-full px-4 py-4 bg-black border border-white/30 focus:border-white/60 text-white placeholder-white/40 font-light"
                style={{backgroundColor: 'black'}}
                value={loginData.password}
                onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                placeholder="demo123"
                required
              />
            </div>
            <button 
              type="submit" 
              disabled={loading || apiStatus === 'offline'}
              className="w-full border border-white/30 hover:border-white/60 disabled:border-white/10 text-white px-6 py-4 font-light transition-all duration-300 hover:scale-105"
              style={{backgroundColor: 'transparent'}}
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </button>
          </form>

          <div className="mt-8 border border-white/20 p-4">
            <p className="text-sm font-light text-white/70">
              <span className="text-white">Demo:</span> demo@ezbi.fr / demo123
            </p>
          </div>

          <div className="text-center mt-6">
            <a 
              href="http://localhost:8004/docs" 
              target="_blank" 
              className="border border-white/30 hover:border-white/60 text-white px-4 py-2 font-light transition-colors inline-flex items-center gap-2"
              style={{backgroundColor: 'transparent'}}
            >
              <svg className="w-4 h-4" style={{color: '#74a6be'}} fill="currentColor" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                <polyline points="14,2 14,8 20,8"/>
              </svg>
              <span>Documentation API</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}