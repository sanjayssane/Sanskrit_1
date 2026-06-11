'use client';

import { Book } from '@/lib/types';
import { Button } from './ui/button';

interface BookFormProps {
  book?: Book;
  onSubmit: (data: any) => void;
  onCancel: () => void;
}

export function BookForm({ book, onSubmit, onCancel }: BookFormProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    onSubmit({
      titleDevanagari: formData.get('titleDevanagari'),
      titleRoman: formData.get('titleRoman'),
      authorDevanagari: formData.get('authorDevanagari'),
      authorRoman: formData.get('authorRoman'),
      sku: formData.get('sku'),
      costPrice: parseFloat(formData.get('costPrice') as string),
      salePrice: parseFloat(formData.get('salePrice') as string),
      wholesalePrice: formData.get('wholesalePrice') ? parseFloat(formData.get('wholesalePrice') as string) : undefined,
      stock: parseInt(formData.get('stock') as string),
      reorderLevel: parseInt(formData.get('reorderLevel') as string),
      category: formData.get('category'),
      description: formData.get('description'),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold mb-4">
        {book ? 'Edit Book' : 'Add New Book'}
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Title (Devanagari)</label>
          <input
            type="text"
            name="titleDevanagari"
            defaultValue={book?.titleDevanagari || ''}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Title (Roman)</label>
          <input
            type="text"
            name="titleRoman"
            defaultValue={book?.titleRoman || ''}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Author (Devanagari)</label>
          <input
            type="text"
            name="authorDevanagari"
            defaultValue={book?.authorDevanagari || ''}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Author (Roman)</label>
          <input
            type="text"
            name="authorRoman"
            defaultValue={book?.authorRoman || ''}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">SKU</label>
          <input
            type="text"
            name="sku"
            defaultValue={book?.sku || ''}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Category</label>
          <input
            type="text"
            name="category"
            defaultValue={book?.category || ''}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Cost Price (₹)</label>
          <input
            type="number"
            name="costPrice"
            defaultValue={book?.costPrice || ''}
            step="0.01"
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Sale Price (₹)</label>
          <input
            type="number"
            name="salePrice"
            defaultValue={book?.salePrice || ''}
            step="0.01"
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Wholesale Price (₹)</label>
          <input
            type="number"
            name="wholesalePrice"
            defaultValue={book?.wholesalePrice || ''}
            step="0.01"
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Current Stock</label>
          <input
            type="number"
            name="stock"
            defaultValue={book?.stock || '0'}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Reorder Level</label>
          <input
            type="number"
            name="reorderLevel"
            defaultValue={book?.reorderLevel || '10'}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            required
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            name="description"
            defaultValue={book?.description || ''}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            rows={3}
          />
        </div>
      </div>

      <div className="flex gap-2 justify-end">
        <Button onClick={onCancel} variant="outline">
          Cancel
        </Button>
        <Button type="submit" className="bg-primary hover:bg-primary/90">
          {book ? 'Update' : 'Create'} Book
        </Button>
      </div>
    </form>
  );
}
