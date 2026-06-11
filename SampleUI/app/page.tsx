'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { BookOpen, BarChart3, Users, ShoppingCart, LogIn } from 'lucide-react';

export default function LandingPage() {
  const { login, isLoading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'demo' | 'features'>('demo');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  const quickDemo = async (role: 'owner' | 'employee') => {
    setError('');
    try {
      const credentials = {
        owner: { email: 'owner@sahitya.com', password: 'owner123' },
        employee: { email: 'staff@sahitya.com', password: 'staff123' },
      };
      await login(credentials[role].email, credentials[role].password);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="w-8 h-8 text-accent" />
              <h1 className="text-2xl font-bold text-primary">संस्कृत साहित्य रत्नाकर</h1>
            </div>
            <p className="text-sm text-muted-foreground">Sanskrit Sahitya Ratnakar</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Left: Features */}
          <div>
            <h2 className="text-4xl font-bold mb-6 text-pretty">
              Professional Shop Management System
            </h2>
            <p className="text-lg text-muted-foreground mb-8">
              Sanskrit Sahitya Ratnakar is a comprehensive retail management system designed specifically for Sanskrit book shops. Manage inventory, track sales and purchases, and gain business insights—all in one place.
            </p>

            <div className="space-y-4">
              <div className="flex gap-4">
                <BookOpen className="w-6 h-6 text-accent flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-1">Book Catalog Management</h3>
                  <p className="text-sm text-muted-foreground">
                    Manage your Sanskrit book collection with dual Devanagari and Roman script support
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <ShoppingCart className="w-6 h-6 text-accent flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-1">Sales & Purchases</h3>
                  <p className="text-sm text-muted-foreground">
                    Track retail and wholesale transactions with automatic receipt generation
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <BarChart3 className="w-6 h-6 text-accent flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-1">Financial Reports</h3>
                  <p className="text-sm text-muted-foreground">
                    Generate detailed P&L statements and inventory reports with Excel export
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <Users className="w-6 h-6 text-accent flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-1">Role-Based Access</h3>
                  <p className="text-sm text-muted-foreground">
                    Separate owner and employee views with customized permissions
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Login Form */}
          <div>
            <div className="bg-card rounded-lg border border-border p-8">
              <div className="flex gap-2 mb-6 bg-muted rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('demo')}
                  className={`flex-1 py-2 px-4 rounded transition-colors ${
                    activeTab === 'demo'
                      ? 'bg-accent text-accent-foreground'
                      : 'text-foreground hover:bg-background'
                  }`}
                >
                  Demo Login
                </button>
                <button
                  onClick={() => setActiveTab('features')}
                  className={`flex-1 py-2 px-4 rounded transition-colors ${
                    activeTab === 'features'
                      ? 'bg-accent text-accent-foreground'
                      : 'text-foreground hover:bg-background'
                  }`}
                >
                  Features
                </button>
              </div>

              {activeTab === 'demo' ? (
                <div>
                  <h3 className="text-xl font-semibold mb-4">Quick Demo Access</h3>
                  <p className="text-sm text-muted-foreground mb-6">
                    Try the system with pre-configured demo accounts
                  </p>

                  <div className="space-y-3 mb-6">
                    <Button
                      onClick={() => quickDemo('owner')}
                      disabled={isLoading}
                      className="w-full bg-primary hover:bg-primary/90"
                    >
                      <LogIn className="w-4 h-4 mr-2" />
                      Login as Owner
                    </Button>
                    <Button
                      onClick={() => quickDemo('employee')}
                      disabled={isLoading}
                      variant="outline"
                      className="w-full"
                    >
                      <LogIn className="w-4 h-4 mr-2" />
                      Login as Staff
                    </Button>
                  </div>

                  <div className="relative mb-6">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-border"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-2 bg-card text-muted-foreground">Or enter credentials</span>
                    </div>
                  </div>

                  <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Email</label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full px-4 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                        placeholder="owner@sahitya.com"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Password</label>
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full px-4 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                        placeholder="••••••••"
                      />
                    </div>
                    {error && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                        {error}
                      </div>
                    )}
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full bg-primary hover:bg-primary/90"
                    >
                      {isLoading ? 'Logging in...' : 'Login'}
                    </Button>
                  </form>

                  <p className="text-xs text-muted-foreground mt-4 text-center">
                    Demo credentials are for testing only
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-muted rounded-lg p-4">
                    <h4 className="font-semibold mb-3">Owner Features</h4>
                    <ul className="space-y-2 text-sm">
                      <li className="flex gap-2">
                        <span className="text-accent">✓</span>
                        <span>Full system access and configuration</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="text-accent">✓</span>
                        <span>Financial reports and P&L statements</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="text-accent">✓</span>
                        <span>User management and permissions</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="text-accent">✓</span>
                        <span>Stock adjustments and inventory control</span>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-muted rounded-lg p-4">
                    <h4 className="font-semibold mb-3">Employee Features</h4>
                    <ul className="space-y-2 text-sm">
                      <li className="flex gap-2">
                        <span className="text-accent">✓</span>
                        <span>Record sales and purchases</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="text-accent">✓</span>
                        <span>View book catalog and stock levels</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="text-accent">✓</span>
                        <span>Manage contacts (suppliers/customers)</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="text-accent">✓</span>
                        <span>Generate receipts and transaction history</span>
                      </li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center text-sm text-muted-foreground">
          <p>Sanskrit Sahitya Ratnakar © 2024. Professional book shop management system.</p>
        </div>
      </footer>
    </div>
  );
}
