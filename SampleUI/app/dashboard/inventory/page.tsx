'use client';

import { useData } from '@/lib/data-context';
import { Card } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

export default function InventoryPage() {
  const { books, stockLedger } = useData();

  const lowStockBooks = books.filter(b => b.stock <= b.reorderLevel);
  const outOfStockBooks = books.filter(b => b.stock === 0);
  const totalStock = books.reduce((sum, b) => sum + b.stock, 0);
  const inventoryValue = books.reduce((sum, b) => sum + (b.stock * b.costPrice), 0);

  const stockByCategory = books.reduce((acc, book) => {
    const existing = acc.find(c => c.name === book.category);
    if (existing) {
      existing.stock += book.stock;
      existing.value += book.stock * book.costPrice;
    } else {
      acc.push({
        name: book.category,
        stock: book.stock,
        value: book.stock * book.costPrice,
      });
    }
    return acc;
  }, [] as Array<{ name: string; stock: number; value: number }>);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Inventory Management</h1>
        <p className="text-muted-foreground mt-1">View and manage your stock levels</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Total Items</p>
          <p className="text-2xl font-bold">{totalStock}</p>
        </Card>

        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Inventory Value</p>
          <p className="text-2xl font-bold">₹{inventoryValue.toLocaleString()}</p>
        </Card>

        <Card className="bg-yellow-50 border border-yellow-200 p-4">
          <p className="text-sm text-yellow-800 mb-1">Low Stock</p>
          <p className="text-2xl font-bold text-yellow-900">{lowStockBooks.length}</p>
        </Card>

        <Card className="bg-red-50 border border-red-200 p-4">
          <p className="text-sm text-red-800 mb-1">Out of Stock</p>
          <p className="text-2xl font-bold text-red-900">{outOfStockBooks.length}</p>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border border-border p-6">
          <h2 className="text-lg font-semibold mb-4">Stock by Category</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stockByCategory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8DFD3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip contentStyle={{ backgroundColor: '#FEFCF9', border: '1px solid #E8DFD3' }} />
              <Bar dataKey="stock" fill="#D4A574" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card className="bg-card border border-border p-6">
          <h2 className="text-lg font-semibold mb-4">Inventory Value by Category</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stockByCategory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8DFD3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip contentStyle={{ backgroundColor: '#FEFCF9', border: '1px solid #E8DFD3' }} />
              <Line type="monotone" dataKey="value" stroke="#8B6B47" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Low Stock Alert */}
      {lowStockBooks.length > 0 && (
        <Card className="bg-yellow-50 border border-yellow-200 p-6">
          <h3 className="font-semibold text-yellow-900 mb-3">Low Stock Items</h3>
          <div className="space-y-2">
            {lowStockBooks.map(book => (
              <div key={book.id} className="flex justify-between items-center py-2 border-b border-yellow-200 last:border-b-0">
                <div>
                  <p className="font-medium text-yellow-900">{book.titleDevanagari}</p>
                  <p className="text-sm text-yellow-800">Reorder Level: {book.reorderLevel}</p>
                </div>
                <p className="text-lg font-semibold text-yellow-900">
                  {book.stock}/{book.reorderLevel}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Out of Stock Alert */}
      {outOfStockBooks.length > 0 && (
        <Card className="bg-red-50 border border-red-200 p-6">
          <h3 className="font-semibold text-red-900 mb-3">Out of Stock Items</h3>
          <div className="space-y-2">
            {outOfStockBooks.map(book => (
              <div key={book.id} className="flex justify-between items-center py-2 border-b border-red-200 last:border-b-0">
                <p className="font-medium text-red-900">{book.titleDevanagari}</p>
                <span className="px-3 py-1 bg-red-200 text-red-900 rounded-full text-sm font-medium">
                  No Stock
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* All Books Inventory */}
      <Card className="bg-card border border-border overflow-hidden">
        <div className="p-6 border-b border-border">
          <h3 className="font-semibold">All Books</h3>
        </div>
        <table className="w-full">
          <thead className="bg-muted border-b border-border">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold">Book</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Category</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Cost Price</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Stock</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Reorder</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Value</th>
            </tr>
          </thead>
          <tbody>
            {books.map((book, idx) => (
              <tr key={book.id} className={idx % 2 ? 'bg-background' : ''}>
                <td className="px-6 py-3 text-sm font-medium">{book.titleDevanagari}</td>
                <td className="px-6 py-3 text-sm">{book.category}</td>
                <td className="px-6 py-3 text-sm text-right">₹{book.costPrice}</td>
                <td className={`px-6 py-3 text-sm text-right font-semibold ${
                  book.stock === 0 ? 'text-red-600' : book.stock <= book.reorderLevel ? 'text-yellow-600' : ''
                }`}>
                  {book.stock}
                </td>
                <td className="px-6 py-3 text-sm text-right">{book.reorderLevel}</td>
                <td className="px-6 py-3 text-sm text-right font-semibold">
                  ₹{(book.stock * book.costPrice).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
