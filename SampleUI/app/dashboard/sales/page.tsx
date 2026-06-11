'use client';

import { useState } from 'react';
import { useData } from '@/lib/data-context';
import { useAuth } from '@/lib/auth-context';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Download, Filter } from 'lucide-react';
import { Sale } from '@/lib/types';

export default function SalesPage() {
  const { sales, books, contacts, addSale } = useData();
  const { user } = useAuth();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [filterType, setFilterType] = useState<'retail' | 'wholesale' | 'all'>('all');
  const [formData, setFormData] = useState({
    bookId: '',
    quantity: '',
    saleType: 'retail' as 'retail' | 'wholesale',
    paymentMethod: 'cash' as 'cash' | 'upi' | 'card' | 'cheque',
    contactId: '',
  });

  const filteredSales = sales.filter(
    s => filterType === 'all' || s.saleType === filterType
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const book = books.find(b => b.id === formData.bookId);
    if (!book) {
      alert('Please select a book');
      return;
    }

    const quantity = parseInt(formData.quantity);
    if (book.stock < quantity) {
      alert('Insufficient stock');
      return;
    }

    const unitPrice = formData.saleType === 'retail' ? book.salePrice : (book.wholesalePrice || book.salePrice);
    const totalPrice = unitPrice * quantity;
    const gstPercent = 5;
    const gstAmount = totalPrice * (gstPercent / 100);

    const newSale: Sale = {
      id: Date.now().toString(),
      bookId: formData.bookId,
      quantity,
      unitPrice,
      totalPrice,
      saleType: formData.saleType,
      gstPercent,
      gstAmount,
      paymentMethod: formData.paymentMethod,
      date: new Date().toISOString(),
      createdBy: user?.id || '',
      contactId: formData.contactId || undefined,
    };

    try {
      addSale(newSale);
      setFormData({
        bookId: '',
        quantity: '',
        saleType: 'retail',
        paymentMethod: 'cash',
        contactId: '',
      });
      setIsFormOpen(false);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to add sale');
    }
  };

  const totalRevenue = filteredSales.reduce((sum, s) => sum + s.totalPrice, 0);
  const totalGst = filteredSales.reduce((sum, s) => sum + s.gstAmount, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Sales</h1>
          <p className="text-muted-foreground mt-1">Record and track book sales</p>
        </div>
        <Button
          onClick={() => setIsFormOpen(!isFormOpen)}
          className="bg-primary hover:bg-primary/90"
        >
          <Plus className="w-4 h-4 mr-2" />
          Record Sale
        </Button>
      </div>

      {isFormOpen && (
        <Card className="bg-card border border-border p-6">
          <h2 className="text-lg font-semibold mb-4">New Sale</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Book *</label>
                <select
                  value={formData.bookId}
                  onChange={(e) => setFormData({ ...formData, bookId: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                  required
                >
                  <option value="">Select a book</option>
                  {books.map(book => (
                    <option key={book.id} value={book.id}>
                      {book.titleDevanagari} (Stock: {book.stock})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Quantity *</label>
                <input
                  type="number"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                  required
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Sale Type</label>
                <select
                  value={formData.saleType}
                  onChange={(e) => setFormData({ ...formData, saleType: e.target.value as any })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="retail">Retail</option>
                  <option value="wholesale">Wholesale</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Payment Method</label>
                <select
                  value={formData.paymentMethod}
                  onChange={(e) => setFormData({ ...formData, paymentMethod: e.target.value as any })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="cash">Cash</option>
                  <option value="upi">UPI</option>
                  <option value="card">Card</option>
                  <option value="cheque">Cheque</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Customer (Optional)</label>
                <select
                  value={formData.contactId}
                  onChange={(e) => setFormData({ ...formData, contactId: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="">Walk-in customer</option>
                  {contacts.filter(c => c.type === 'customer').map(contact => (
                    <option key={contact.id} value={contact.id}>
                      {contact.nameDevanagari}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-2 justify-end">
              <Button onClick={() => setIsFormOpen(false)} variant="outline">
                Cancel
              </Button>
              <Button type="submit" className="bg-primary hover:bg-primary/90">
                Record Sale
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Total Sales</p>
          <p className="text-2xl font-bold">₹{totalRevenue.toLocaleString()}</p>
        </Card>
        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Total GST</p>
          <p className="text-2xl font-bold">₹{totalGst.toLocaleString()}</p>
        </Card>
        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Total Transactions</p>
          <p className="text-2xl font-bold">{filteredSales.length}</p>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-card border border-border p-4">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-muted-foreground" />
          <div className="flex gap-2">
            {(['all', 'retail', 'wholesale'] as const).map(type => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`px-4 py-2 rounded-lg transition-colors capitalize ${
                  filterType === type
                    ? 'bg-accent text-accent-foreground'
                    : 'bg-muted text-foreground hover:bg-muted/80'
                }`}
              >
                {type === 'all' ? 'All Sales' : type}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Sales List */}
      <Card className="bg-card border border-border overflow-hidden">
        <table className="w-full">
          <thead className="bg-muted border-b border-border">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold">Date</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Book</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Qty</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Type</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Amount</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Payment</th>
            </tr>
          </thead>
          <tbody>
            {filteredSales.map((sale, idx) => {
              const book = books.find(b => b.id === sale.bookId);
              return (
                <tr key={sale.id} className={idx % 2 ? 'bg-background' : ''}>
                  <td className="px-6 py-3 text-sm">{new Date(sale.date).toLocaleDateString()}</td>
                  <td className="px-6 py-3 text-sm font-medium">{book?.titleDevanagari}</td>
                  <td className="px-6 py-3 text-sm">{sale.quantity}</td>
                  <td className="px-6 py-3 text-sm capitalize">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      sale.saleType === 'retail' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {sale.saleType}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-sm font-semibold">₹{sale.totalPrice}</td>
                  <td className="px-6 py-3 text-sm capitalize">{sale.paymentMethod}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filteredSales.length === 0 && (
          <div className="p-12 text-center text-muted-foreground">
            No sales recorded yet
          </div>
        )}
      </Card>
    </div>
  );
}
