'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from './types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEMO_USERS = [
  {
    id: '1',
    email: 'owner@sahitya.com',
    name: 'श्री शर्मा',
    role: 'owner' as UserRole,
    password: 'owner123',
  },
  {
    id: '2',
    email: 'staff@sahitya.com',
    name: 'राज कुमार',
    role: 'employee' as UserRole,
    password: 'staff123',
  },
];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const storedUser = localStorage.getItem('currentUser');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const demoUser = DEMO_USERS.find(u => u.email === email && u.password === password);
    
    if (demoUser) {
      const user: User = {
        id: demoUser.id,
        email: demoUser.email,
        name: demoUser.name,
        role: demoUser.role,
        active: true,
        createdAt: new Date().toISOString(),
      };
      setUser(user);
      localStorage.setItem('currentUser', JSON.stringify(user));
    } else {
      throw new Error('Invalid email or password');
    }
    setIsLoading(false);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('currentUser');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
