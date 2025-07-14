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
    <section id="login-section" className="py-20 bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-800">
      <div className="container mx-auto px-4">
        <div className="max-w-md mx-auto bg-white/10 backdrop-blur-lg rounded-xl p-8 border border-white/20">
          {/* API Status */}
          <div className="flex items-center gap-2 mb-6">
            <div className={`w-3 h-3 rounded-full ${
              apiStatus === 'online' ? 'bg-green-500' : 
              apiStatus === 'offline' ? 'bg-red-500' : 
              'bg-yellow-500 animate-pulse'
            }`}></div>
            <span className="text-sm font-medium text-white">
              API: {apiStatus === 'online' ? 'En ligne' : 
                   apiStatus === 'offline' ? 'Hors ligne' : 
                   'Vérification...'}
            </span>
          </div>

          <h2 className="text-2xl font-bold text-center mb-6 text-white">
            Accès Plateforme EZBI
          </h2>
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-white/90">Email</label>
              <input
                type="email"
                className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-white/60"
                value={loginData.email}
                onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                placeholder="demo@ezbi.fr"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-white/90">Mot de passe</label>
              <input
                type="password"
                className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-white/60"
                value={loginData.password}
                onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                placeholder="demo123"
                required
              />
            </div>
            <button 
              type="submit" 
              disabled={loading || apiStatus === 'offline'}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 transform hover:scale-105"
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </button>
          </form>

          <div className="mt-6 p-4 bg-blue-500/20 rounded-lg border border-blue-400/30">
            <p className="text-sm text-blue-200">
              <strong>Demo:</strong> demo@ezbi.fr / demo123
            </p>
          </div>

          <div className="text-center mt-6">
            <a 
              href="http://localhost:8003/docs" 
              target="_blank" 
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors inline-block text-sm"
            >
              📚 Documentation API
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}