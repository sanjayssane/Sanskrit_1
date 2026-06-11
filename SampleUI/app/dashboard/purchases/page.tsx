'use client';

import { useState } from 'react';
import { useData } from '@/lib/data-context';
import { useAuth } from '@/lib/auth-context';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { Purchase } from '@/lib/types';

export default function PurchasesPage() {
  const { purchases, books, contacts, addPurchase } = useData();
  const { user } = useAuth();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formData, setFormData] = useState({
    bookId: '',
    quantity: '',
    unitPrice: '',
    contactId: '',
    gstPercent: '5',
    invoiceNumber: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const book = books.find(b => b.id === formData.bookId);
    if (!book) {
      alert('Please select a book');
      return;
    }

    const quantity = parseInt(formData.quantity);
    const unitPrice = parseFloat(formData.unitPrice);
    const totalPrice = unitPrice * quantity;
    const gstPercent = parseInt(formData.gstPercent);
    const gstAmount = totalPrice * (gstPercent / 100);

    const newPurchase: Purchase = {
      id: Date.now().toString(),
      bookId: formData.bookId,
      quantity,
      unitPrice,
      totalPrice,
      gstPercent,
      gstAmount,
      date: new Date().toISOString(),
      createdBy: user?.id || '',
      contactId: formData.contactId || undefined,
      invoiceNumber: formData.invoiceNumber || undefined,
    };

    try {
      addPurchase(newPurchase);
      setFormData({
        bookId: '',
        quantity: '',
        unitPrice: '',
        contactId: '',
        gstPercent: '5',
        invoiceNumber: '',
      });
      setIsFormOpen(false);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to add purchase');
    }
  };

  const totalPurchased = purchases.reduce((sum, p) => sum + p.totalPrice, 0);
  const totalGst = purchases.reduce((sum, p) => sum + p.gstAmount, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Purchases</h1>
          <p className="text-muted-foreground mt-1">Track book purchases from suppliers</p>
        </div>
        <Button
          onClick={() => setIsFormOpen(!isFormOpen)}
          className="bg-primary hover:bg-primary/90"
        >
          <Plus className="w-4 h-4 mr-2" />
          Record Purchase
        </Button>
      </div>

      {isFormOpen && (
        <Card className="bg-card border border-border p-6">
          <h2 className="text-lg font-semibold mb-4">New Purchase</h2>
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
                      {book.titleDevanagari}
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
                <label className="block text-sm font-medium mb-1">Unit Price (₹) *</label>
                <input
                  type="number"
                  value={formData.unitPrice}
                  onChange={(e) => setFormData({ ...formData, unitPrice: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                  required
                  step="0.01"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">GST %</label>
                <input
                  type="number"
                  value={formData.gstPercent}
                  onChange={(e) => setFormData({ ...formData, gstPercent: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                  step="0.01"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Supplier</label>
                <select
                  value={formData.contactId}
                  onChange={(e) => setFormData({ ...formData, contactId: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="">Select supplier</option>
                  {contacts.filter(c => c.type === 'supplier').map(contact => (
                    <option key={contact.id} value={contact.id}>
                      {contact.nameDevanagari}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Invoice Number</label>
                <input
                  type="text"
                  value={formData.invoiceNumber}
                  onChange={(e) => setFormData({ ...formData, invoiceNumber: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
            </div>

            <div className="flex gap-2 justify-end">
              <Button onClick={() => setIsFormOpen(false)} variant="outline">
                Cancel
              </Button>
              <Button type="submit" className="bg-primary hover:bg-primary/90">
                Record Purchase
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Total Purchased</p>
          <p className="text-2xl font-bold">₹{totalPurchased.toLocaleString()}</p>
        </Card>
        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Total GST</p>
          <p className="text-2xl font-bold">₹{totalGst.toLocaleString()}</p>
        </Card>
        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Total Transactions</p>
          <p className="text-2xl font-bold">{purchases.length}</p>
        </Card>
      </div>

      {/* Purchases List */}
      <Card className="bg-card border border-border overflow-hidden">
        <table className="w-full">
          <thead className="bg-muted border-b border-border">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold">Date</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Book</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Qty</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Unit Price</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Total</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">GST</th>
            </tr>
          </thead>
          <tbody>
            {purchases.map((purchase, idx) => {
              const book = books.find(b => b.id === purchase.bookId);
              return (
                <tr key={purchase.id} className={idx % 2 ? 'bg-background' : ''}>
                  <td className="px-6 py-3 text-sm">{new Date(purchase.date).toLocaleDateString()}</td>
                  <td className="px-6 py-3 text-sm font-medium">{book?.titleDevanagari}</td>
                  <td className="px-6 py-3 text-sm">{purchase.quantity}</td>
                  <td className="px-6 py-3 text-sm">₹{purchase.unitPrice}</td>
                  <td className="px-6 py-3 text-sm font-semibold">₹{purchase.totalPrice}</td>
                  <td className="px-6 py-3 text-sm">₹{purchase.gstAmount.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {purchases.length === 0 && (
          <div className="p-12 text-center text-muted-foreground">
            No purchases recorded yet
          </div>
        )}
      </Card>
    </div>
  );
}
