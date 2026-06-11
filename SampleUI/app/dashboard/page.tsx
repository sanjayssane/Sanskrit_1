'use client';

import { useAuth } from '@/lib/auth-context';
import { useData } from '@/lib/data-context';
import { BarChart3, BookOpen, TrendingUp, AlertTriangle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export default function DashboardPage() {
  const { user } = useAuth();
  const { books, purchases, sales } = useData();
  const router = useRouter();

  // Calculate metrics
  const lowStockBooks = books.filter(b => b.stock <= b.reorderLevel);
  const totalRevenue = sales.reduce((sum, s) => sum + s.totalPrice, 0);
  const totalCost = purchases.reduce((sum, p) => sum + p.totalPrice, 0);
  const grossProfit = totalRevenue - totalCost;
  const totalBooks = books.length;

  // Chart data for sales trends
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (6 - i));
    return date.toISOString().split('T')[0];
  });

  const salesByDay = last7Days.map(day => {
    const daySales = sales.filter(s => s.date.startsWith(day));
    return {
      date: new Date(day).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      sales: daySales.reduce((sum, s) => sum + s.quantity, 0),
      revenue: daySales.reduce((sum, s) => sum + s.totalPrice, 0),
    };
  });

  const categoryDistribution = books.reduce((acc, book) => {
    const existing = acc.find(c => c.name === book.category);
    if (existing) {
      existing.value += 1;
    } else {
      acc.push({ name: book.category, value: 1 });
    }
    return acc;
  }, [] as Array<{ name: string; value: number }>);

  const COLORS = ['#D4A574', '#8B6B47', '#6F6B63', '#4A4238', '#2C2817'];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">
          नमस्ते, {user?.name}!
        </h1>
        <p className="text-muted-foreground mt-2">Welcome to Sanskrit Sahitya Ratnakar</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Revenue</p>
              <p className="text-2xl font-bold mt-2">₹{totalRevenue.toLocaleString()}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-accent opacity-50" />
          </div>
        </Card>

        <Card className="bg-card border border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Books in Stock</p>
              <p className="text-2xl font-bold mt-2">{totalBooks}</p>
            </div>
            <BookOpen className="w-8 h-8 text-accent opacity-50" />
          </div>
        </Card>

        <Card className="bg-card border border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Gross Profit</p>
              <p className="text-2xl font-bold mt-2 text-green-700">₹{Math.max(0, grossProfit).toLocaleString()}</p>
            </div>
            <BarChart3 className="w-8 h-8 text-green-600 opacity-50" />
          </div>
        </Card>

        <Card className="bg-card border border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Low Stock Items</p>
              <p className="text-2xl font-bold mt-2">{lowStockBooks.length}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-600 opacity-50" />
          </div>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 bg-card border border-border p-6">
          <h2 className="text-lg font-semibold mb-4">Sales Trend (Last 7 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={salesByDay}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8DFD3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip 
                contentStyle={{ backgroundColor: '#FEFCF9', border: '1px solid #E8DFD3' }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="revenue" 
                stroke="#D4A574" 
                strokeWidth={2}
                dot={{ fill: '#D4A574' }}
              />
              <Line 
                type="monotone" 
                dataKey="sales" 
                stroke="#8B6B47" 
                strokeWidth={2}
                dot={{ fill: '#8B6B47' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card className="bg-card border border-border p-6">
          <h2 className="text-lg font-semibold mb-4">Categories</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => entry.name}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {categoryDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Low Stock Alert */}
      {lowStockBooks.length > 0 && (
        <Card className="bg-red-50 border border-red-200 p-6">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-red-900 mb-2">Low Stock Alert</h3>
              <p className="text-sm text-red-800 mb-4">
                {lowStockBooks.length} book(s) are below reorder level. Please consider restocking.
              </p>
              <div className="space-y-1">
                {lowStockBooks.slice(0, 3).map(book => (
                  <p key={book.id} className="text-sm text-red-700">
                    • {book.titleDevanagari} ({book.stock}/{book.reorderLevel})
                  </p>
                ))}
                {lowStockBooks.length > 3 && (
                  <p className="text-sm text-red-700">
                    • and {lowStockBooks.length - 3} more...
                  </p>
                )}
              </div>
            </div>
            <Button 
              onClick={() => router.push('/dashboard/inventory')}
              className="bg-red-600 hover:bg-red-700"
            >
              View Inventory
            </Button>
          </div>
        </Card>
      )}

      {/* Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border border-border p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Sales</h3>
          <div className="space-y-3">
            {sales.slice(0, 5).map(sale => (
              <div key={sale.id} className="flex justify-between items-center py-2 border-b border-border last:border-b-0">
                <div>
                  <p className="text-sm font-medium">
                    {books.find(b => b.id === sale.bookId)?.titleDevanagari || 'Unknown'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(sale.date).toLocaleDateString()}
                  </p>
                </div>
                <p className="font-semibold">₹{sale.totalPrice}</p>
              </div>
            ))}
            {sales.length === 0 && (
              <p className="text-sm text-muted-foreground">No sales yet</p>
            )}
          </div>
        </Card>

        <Card className="bg-card border border-border p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Purchases</h3>
          <div className="space-y-3">
            {purchases.slice(0, 5).map(purchase => (
              <div key={purchase.id} className="flex justify-between items-center py-2 border-b border-border last:border-b-0">
                <div>
                  <p className="text-sm font-medium">
                    {books.find(b => b.id === purchase.bookId)?.titleDevanagari || 'Unknown'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(purchase.date).toLocaleDateString()}
                  </p>
                </div>
                <p className="font-semibold">₹{purchase.totalPrice}</p>
              </div>
            ))}
            {purchases.length === 0 && (
              <p className="text-sm text-muted-foreground">No purchases yet</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
