'use client';

import { useState } from 'react';
import { useData } from '@/lib/data-context';
import { useAuth } from '@/lib/auth-context';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import { Contact } from '@/lib/types';

export default function ContactsPage() {
  const { contacts, addContact, updateContact } = useData();
  const { user } = useAuth();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [filterType, setFilterType] = useState<'supplier' | 'customer' | 'all'>('all');
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [formData, setFormData] = useState({
    nameDevanagari: '',
    nameRoman: '',
    type: 'supplier' as 'supplier' | 'customer',
    email: '',
    phone: '',
    address: '',
    gstin: '',
  });

  const filteredContacts = contacts.filter(
    c => filterType === 'all' || c.type === filterType
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (editingContact) {
      updateContact({
        ...editingContact,
        ...formData,
      });
      setEditingContact(null);
    } else {
      const newContact: Contact = {
        id: Date.now().toString(),
        type: formData.type,
        nameDevanagari: formData.nameDevanagari,
        nameRoman: formData.nameRoman,
        email: formData.email || undefined,
        phone: formData.phone || undefined,
        address: formData.address || undefined,
        gstin: formData.gstin || undefined,
      };
      addContact(newContact);
    }

    setFormData({
      nameDevanagari: '',
      nameRoman: '',
      type: 'supplier',
      email: '',
      phone: '',
      address: '',
      gstin: '',
    });
    setIsFormOpen(false);
  };

  const handleEdit = (contact: Contact) => {
    setEditingContact(contact);
    setFormData({
      nameDevanagari: contact.nameDevanagari,
      nameRoman: contact.nameRoman,
      type: contact.type,
      email: contact.email || '',
      phone: contact.phone || '',
      address: contact.address || '',
      gstin: contact.gstin || '',
    });
    setIsFormOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Contacts</h1>
          <p className="text-muted-foreground mt-1">Manage suppliers and customers</p>
        </div>
        <Button
          onClick={() => {
            setEditingContact(null);
            setFormData({
              nameDevanagari: '',
              nameRoman: '',
              type: 'supplier',
              email: '',
              phone: '',
              address: '',
              gstin: '',
            });
            setIsFormOpen(!isFormOpen);
          }}
          className="bg-primary hover:bg-primary/90"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Contact
        </Button>
      </div>

      {isFormOpen && (
        <Card className="bg-card border border-border p-6">
          <h2 className="text-lg font-semibold mb-4">
            {editingContact ? 'Edit Contact' : 'New Contact'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Type *</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                  required
                >
                  <option value="supplier">Supplier</option>
                  <option value="customer">Customer</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Name (Devanagari) *</label>
                <input
                  type="text"
                  value={formData.nameDevanagari}
                  onChange={(e) => setFormData({ ...formData, nameDevanagari: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Name (Roman) *</label>
                <input
                  type="text"
                  value={formData.nameRoman}
                  onChange={(e) => setFormData({ ...formData, nameRoman: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">GSTIN</label>
                <input
                  type="text"
                  value={formData.gstin}
                  onChange={(e) => setFormData({ ...formData, gstin: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Address</label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                  rows={2}
                />
              </div>
            </div>

            <div className="flex gap-2 justify-end">
              <Button onClick={() => setIsFormOpen(false)} variant="outline">
                Cancel
              </Button>
              <Button type="submit" className="bg-primary hover:bg-primary/90">
                {editingContact ? 'Update' : 'Create'} Contact
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Filter */}
      <div className="flex gap-2">
        {(['all', 'supplier', 'customer'] as const).map(type => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-4 py-2 rounded-lg transition-colors capitalize ${
              filterType === type
                ? 'bg-accent text-accent-foreground'
                : 'bg-muted text-foreground hover:bg-muted/80'
            }`}
          >
            {type === 'all' ? 'All' : type + 's'}
          </button>
        ))}
      </div>

      {/* Contacts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredContacts.map(contact => (
          <Card key={contact.id} className="bg-card border border-border p-4">
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold">{contact.nameDevanagari}</h3>
                <p className="text-sm text-muted-foreground">{contact.nameRoman}</p>
              </div>

              <div className="text-sm space-y-1">
                {contact.email && (
                  <p className="text-muted-foreground">
                    <span className="font-medium">Email:</span> {contact.email}
                  </p>
                )}
                {contact.phone && (
                  <p className="text-muted-foreground">
                    <span className="font-medium">Phone:</span> {contact.phone}
                  </p>
                )}
                {contact.gstin && (
                  <p className="text-muted-foreground">
                    <span className="font-medium">GSTIN:</span> {contact.gstin}
                  </p>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={() => handleEdit(contact)}
                  variant="outline"
                  className="flex-1 text-sm"
                >
                  <Edit2 className="w-4 h-4 mr-1" />
                  Edit
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {filteredContacts.length === 0 && (
        <Card className="bg-muted border border-border p-12 text-center">
          <p className="text-muted-foreground">No contacts found</p>
        </Card>
      )}
    </div>
  );
}
