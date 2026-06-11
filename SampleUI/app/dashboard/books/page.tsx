'use client';

import { useState } from 'react';
import { useData } from '@/lib/data-context';
import { useAuth } from '@/lib/auth-context';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Edit2, Trash2, Search } from 'lucide-react';
import { BookForm } from '@/components/book-form';
import { Book } from '@/lib/types';

export default function BooksPage() {
  const { books, addBook, updateBook, deleteBook } = useData();
  const { user } = useAuth();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const canEdit = user?.role === 'owner';

  const filteredBooks = books.filter(
    book =>
      book.titleDevanagari.includes(searchTerm) ||
      book.titleRoman.toLowerCase().includes(searchTerm.toLowerCase()) ||
      book.sku.includes(searchTerm)
  );

  const handleAddBook = (bookData: any) => {
    const newBook: Book = {
      id: Date.now().toString(),
      ...bookData,
    };
    addBook(newBook);
    setIsFormOpen(false);
  };

  const handleUpdateBook = (bookData: any) => {
    if (editingBook) {
      updateBook({ ...editingBook, ...bookData });
      setEditingBook(null);
    }
  };

  const handleDeleteBook = (id: string) => {
    if (confirm('Are you sure you want to delete this book?')) {
      deleteBook(id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Books Catalog</h1>
          <p className="text-muted-foreground mt-1">Manage your Sanskrit book collection</p>
        </div>
        {canEdit && (
          <Button
            onClick={() => {
              setEditingBook(null);
              setIsFormOpen(true);
            }}
            className="bg-primary hover:bg-primary/90"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Book
          </Button>
        )}
      </div>

      {isFormOpen && (
        <Card className="bg-card border border-border p-6">
          <BookForm
            book={editingBook || undefined}
            onSubmit={editingBook ? handleUpdateBook : handleAddBook}
            onCancel={() => {
              setIsFormOpen(false);
              setEditingBook(null);
            }}
          />
        </Card>
      )}

      <Card className="bg-card border border-border p-4">
        <div className="flex gap-2">
          <Search className="w-5 h-5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by title, author, or SKU..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 bg-background border-0 focus:outline-none text-foreground placeholder-muted-foreground"
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredBooks.map(book => (
          <Card key={book.id} className="bg-card border border-border p-4">
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold text-foreground">{book.titleDevanagari}</h3>
                <p className="text-sm text-muted-foreground">{book.titleRoman}</p>
              </div>

              <div className="text-sm space-y-1">
                <p className="text-muted-foreground">
                  <span className="font-medium">SKU:</span> {book.sku}
                </p>
                <p className="text-muted-foreground">
                  <span className="font-medium">Author:</span> {book.authorDevanagari}
                </p>
                <p className="text-muted-foreground">
                  <span className="font-medium">Category:</span> {book.category}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 py-2 border-y border-border text-center">
                <div>
                  <p className="text-xs text-muted-foreground">Cost</p>
                  <p className="font-semibold">₹{book.costPrice}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Sale</p>
                  <p className="font-semibold">₹{book.salePrice}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Stock</p>
                  <p className={`font-semibold ${book.stock <= book.reorderLevel ? 'text-red-600' : ''}`}>
                    {book.stock}
                  </p>
                </div>
              </div>

              {canEdit && (
                <div className="flex gap-2">
                  <Button
                    onClick={() => {
                      setEditingBook(book);
                      setIsFormOpen(true);
                    }}
                    variant="outline"
                    className="flex-1 text-sm"
                  >
                    <Edit2 className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    onClick={() => handleDeleteBook(book.id)}
                    variant="outline"
                    className="flex-1 text-sm text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Delete
                  </Button>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>

      {filteredBooks.length === 0 && (
        <Card className="bg-muted border border-border p-12 text-center">
          <p className="text-muted-foreground">No books found. {canEdit && 'Add your first book to get started.'}</p>
        </Card>
      )}
    </div>
  );
}
