'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'superuser' | 'worker';
  is_active: boolean;
}

interface AuthGuardProps {
  children: React.ReactNode;
  requiredRole?: 'superuser' | 'worker' | 'any';
}

export default function AuthGuard({ children, requiredRole = 'any' }: AuthGuardProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const userStr = localStorage.getItem('user');

      if (!token || !userStr) {
        router.push('/backoffice');
        return;
      }

      const user: User = JSON.parse(userStr);

      // Verificar rol si es requerido
      if (requiredRole !== 'any' && user.role !== requiredRole) {
        // Redirigir al dashboard correcto según el rol
        if (user.role === 'superuser') {
          router.push('/dashboard');
        } else {
          router.push('/dashboard/work');
        }
        return;
      }

      // Verificar token con el backend
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Token inválido');
      }

      setAuthenticated(true);
    } catch (error) {
      console.error('Auth error:', error);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      router.push('/backoffice');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-3" />
          <p className="text-gray-400">Verificando autenticación...</p>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return null;
  }

  return <>{children}</>;
}
