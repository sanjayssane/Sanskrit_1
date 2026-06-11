'use client';

import { useAuth } from '@/lib/auth-context';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { BookOpen, BarChart3, ShoppingCart, Inbox, Users, LogOut, Settings } from 'lucide-react';
import { Button } from './ui/button';

export function Sidebar() {
  const { logout, user } = useAuth();
  const pathname = usePathname();

  const menuItems = [
    { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
    { href: '/dashboard/books', label: 'Books', icon: BookOpen },
    { href: '/dashboard/sales', label: 'Sales', icon: ShoppingCart },
    { href: '/dashboard/purchases', label: 'Purchases', icon: Inbox },
    { href: '/dashboard/contacts', label: 'Contacts', icon: Users },
  ];

  if (user?.role === 'owner') {
    menuItems.push(
      { href: '/dashboard/reports', label: 'Reports', icon: BarChart3 },
      { href: '/dashboard/users', label: 'Users', icon: Users }
    );
  }

  menuItems.push(
    { href: '/dashboard/inventory', label: 'Inventory', icon: Inbox }
  );

  const isActive = (href: string) => pathname === href || (href !== '/dashboard' && pathname.startsWith(href));

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-6 border-b border-border">
        <Link href="/dashboard" className="flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-accent" />
          <div className="flex-1">
            <h1 className="text-sm font-bold">संस्कृत साहित्य</h1>
            <p className="text-xs text-muted-foreground">Ratnakar</p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map(item => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                active
                  ? 'bg-accent text-accent-foreground'
                  : 'text-foreground hover:bg-muted'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border space-y-2">
        <Link
          href="/dashboard/settings"
          className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors text-foreground hover:bg-muted`}
        >
          <Settings className="w-5 h-5" />
          <span className="text-sm font-medium">Settings</span>
        </Link>
        <Button
          onClick={logout}
          variant="outline"
          className="w-full justify-start gap-3"
        >
          <LogOut className="w-5 h-5" />
          <span>Logout</span>
        </Button>
      </div>
    </aside>
  );
}
