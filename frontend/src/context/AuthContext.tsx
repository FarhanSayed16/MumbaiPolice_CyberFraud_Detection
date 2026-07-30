import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService, type UserProfile, type LoginCredentials, type RoleType } from '@/api/client';

interface AuthContextType {
  user: UserProfile | null;
  role: RoleType | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  seedInitialUsers: () => Promise<any>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshProfile = async () => {
    try {
      const profile = await authService.getCurrentUser();
      setUser(profile);
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshProfile();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const profile = await authService.login(credentials);
    setUser(profile);
  };

  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  };

  const seedInitialUsers = async () => {
    return await authService.seedInitialUsers();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || null,
        loading,
        isAuthenticated: !!user,
        login,
        logout,
        seedInitialUsers,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
