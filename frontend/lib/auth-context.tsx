'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import api from './api';

interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  loginWithMagicLink: (email: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté au chargement
    const initAuth = async () => {
      // Vérifier si on est côté client
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('sovera-token');
        if (token) {
          api.setToken(token);
          const response = await api.getCurrentUser();
          if (response.success && response.data) {
            setUser(response.data);
          } else {
            // Token invalide, le supprimer
            localStorage.removeItem('sovera-token');
            api.setToken(null);
          }
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await api.login(email, password);
    
    if (response.success && response.data) {
      const { access_token } = response.data;
      api.setToken(access_token);
      
      // Récupérer les informations utilisateur
      const userResponse = await api.getCurrentUser();
      if (userResponse.success && userResponse.data) {
        setUser(userResponse.data);
      } else {
        throw new Error('Impossible de récupérer les informations utilisateur');
      }
    } else {
      let errorMessage = 'Erreur de connexion. Veuillez vérifier vos identifiants.';
      if (response.error) {
        errorMessage = response.error;
      }
      throw new Error(errorMessage);
    }
  };

  const loginWithMagicLink = async (email: string) => {
    // Magic link n'est pas implémenté dans le backend actuellement
    throw new Error('Magic link non implémenté');
  };

  const register = async (email: string, password: string, name?: string) => {
    const response = await api.register(email, password);
    
    if (response.success && response.data) {
      // Inscription réussie - l'utilisateur doit maintenant se connecter manuellement
      // Ne pas se connecter automatiquement
    } else {
      let errorMessage = 'Erreur lors de l\'inscription. Veuillez réessayer.';
      if (response.error) {
        errorMessage = response.error;
      }
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    setUser(null);
    api.setToken(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      loginWithMagicLink,
      register,
      logout,
      loading
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}