'use client';

import { useAuth } from '@/lib/auth-context';
import { Bell, User, HelpCircle } from 'lucide-react';

export function Header() {
  const { user } = useAuth();

  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">
            Sanskrit Sahitya Ratnakar
          </h2>
          <p className="text-sm text-muted-foreground">Book Shop Management System</p>
        </div>

        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-muted rounded-lg transition-colors">
            <HelpCircle className="w-5 h-5 text-muted-foreground" />
          </button>
          <button className="p-2 hover:bg-muted rounded-lg transition-colors relative">
            <Bell className="w-5 h-5 text-muted-foreground" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
          <div className="flex items-center gap-2 pl-4 border-l border-border">
            <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
              <User className="w-5 h-5 text-accent-foreground" />
            </div>
            <div className="text-sm">
              <p className="font-medium text-foreground">{user?.name}</p>
              <p className="text-xs text-muted-foreground capitalize">{user?.role}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
