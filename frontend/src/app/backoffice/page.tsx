'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, Mail, AlertCircle, Loader2, Shield, Briefcase } from 'lucide-react';

export default function BackofficeLogin() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Función para login rápido (solo para desarrollo/testing)
  const quickLogin = async (userEmail: string, userPassword: string) => {
    // Limpiar localStorage antes de intentar login
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    
    setEmail(userEmail);
    setPassword(userPassword);
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: userEmail, password: userPassword }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al iniciar sesión');
      }

      const data = await response.json();
      
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      if (data.user.role === 'admin' || data.user.role === 'superuser') {
        router.push('/dashboard');
      } else if (data.user.role === 'worker') {
        router.push('/dashboard/work');
      } else {
        throw new Error('Rol de usuario no reconocido');
      }

    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    quickLogin(email, password);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center p-4">
      <div className="relative w-full max-w-md">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4 shadow-lg shadow-blue-500/20">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Backoffice</h1>
          <p className="text-gray-400">Acceso exclusivo para el equipo</p>
        </div>

        {/* Login Card */}
        <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700 rounded-2xl p-8 shadow-2xl">
          <form onSubmit={handleLogin} className="space-y-6">
            {/* Error Alert */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              </div>
            )}

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="tu@email.com"
                  className="w-full pl-10 pr-4 py-3 bg-gray-900/50 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Contraseña
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-3 bg-gray-900/50 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3 rounded-lg font-semibold text-white transition-all flex items-center justify-center gap-2 ${
                loading
                  ? 'bg-gray-700 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 shadow-lg shadow-blue-500/20'
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Iniciando sesión...
                </>
              ) : (
                <>
                  <Lock className="w-5 h-5" />
                  Iniciar Sesión
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-700"></div>
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-2 bg-gray-800/50 text-gray-400">Acceso rápido para testing</span>
            </div>
          </div>

          {/* Quick Login Buttons */}
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => quickLogin('admin@lokigi.com', 'admin123')}
              disabled={loading}
              className="w-full flex items-center gap-3 p-4 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 hover:border-blue-500/50 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-center justify-center w-10 h-10 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-all">
                <Shield className="w-5 h-5 text-blue-400" />
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-semibold text-blue-300">Login como ADMIN</p>
                <p className="text-xs text-gray-400">admin@lokigi.com</p>
              </div>
              {loading && email === 'admin@lokigi.com' && (
                <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
              )}
            </button>

            <button
              type="button"
              onClick={() => quickLogin('worker@lokigi.com', 'worker123')}
              disabled={loading}
              className="w-full flex items-center gap-3 p-4 bg-green-500/10 hover:bg-green-500/20 border border-green-500/30 hover:border-green-500/50 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-center justify-center w-10 h-10 bg-green-500/20 rounded-lg group-hover:bg-green-500/30 transition-all">
                <Briefcase className="w-5 h-5 text-green-400" />
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-semibold text-green-300">Login como WORKER</p>
                <p className="text-xs text-gray-400">worker@lokigi.com</p>
              </div>
              {loading && email === 'worker@lokigi.com' && (
                <Loader2 className="w-5 h-5 text-green-400 animate-spin" />
              )}
            </button>
          </div>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-700"></div>
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-2 bg-gray-800/50 text-gray-400">Roles disponibles</span>
            </div>
          </div>

          {/* Role Info */}
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-blue-500/5 border border-blue-500/20 rounded-lg">
              <Shield className="w-5 h-5 text-blue-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-blue-300">Administrador</p>
                <p className="text-xs text-gray-400">Acceso total al Command Center</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 bg-green-500/5 border border-green-500/20 rounded-lg">
              <Briefcase className="w-5 h-5 text-green-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-green-300">Trabajador</p>
                <p className="text-xs text-gray-400">Acceso al Work Queue</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            ¿Problemas para acceder?{' '}
            <a href="mailto:soporte@lokigi.com" className="text-blue-400 hover:text-blue-300 transition-colors">
              Contacta con soporte
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
