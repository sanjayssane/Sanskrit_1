'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Book, Purchase, Sale, Contact, StockLedger } from './types';

interface DataContextType {
  // Data
  books: Book[];
  purchases: Purchase[];
  sales: Sale[];
  contacts: Contact[];
  stockLedger: StockLedger[];
  users: any[];

  // Book operations
  addBook: (book: Book) => void;
  updateBook: (book: Book) => void;
  deleteBook: (id: string) => void;
  getBookStock: (bookId: string) => number;

  // Purchase operations
  addPurchase: (purchase: Purchase) => void;
  getPurchases: (filters?: any) => Purchase[];

  // Sale operations
  addSale: (sale: Sale) => void;
  getSales: (filters?: any) => Sale[];

  // Contact operations
  addContact: (contact: Contact) => void;
  updateContact: (contact: Contact) => void;
  getContacts: (type?: 'supplier' | 'customer') => Contact[];

  // Stock operations
  getStockLedger: (bookId: string) => StockLedger[];
}

const DataContext = createContext<DataContextType | undefined>(undefined);

// Mock initial data
const INITIAL_BOOKS: Book[] = [
  {
    id: '1',
    titleDevanagari: 'भगवद्गीता',
    titleRoman: 'Bhagavad Gita',
    authorDevanagari: 'व्यास',
    authorRoman: 'Vyasa',
    sku: 'BG-001',
    costPrice: 250,
    salePrice: 499,
    wholesalePrice: 399,
    stock: 45,
    reorderLevel: 10,
    category: 'Philosophy',
    description: 'The sacred dialogue between Lord Krishna and Arjuna',
  },
  {
    id: '2',
    titleDevanagari: 'रामायण',
    titleRoman: 'Ramayana',
    authorDevanagari: 'वाल्मीकि',
    authorRoman: 'Valmiki',
    sku: 'RM-001',
    costPrice: 400,
    salePrice: 799,
    wholesalePrice: 650,
    stock: 28,
    reorderLevel: 8,
    category: 'Epic',
    description: 'The great epic of Lord Rama',
  },
  {
    id: '3',
    titleDevanagari: 'महाभारत',
    titleRoman: 'Mahabharata',
    authorDevanagari: 'व्यास',
    authorRoman: 'Vyasa',
    sku: 'MB-001',
    costPrice: 600,
    salePrice: 1299,
    wholesalePrice: 1050,
    stock: 12,
    reorderLevel: 5,
    category: 'Epic',
    description: 'The greatest epic of ancient India',
  },
];

export function DataProvider({ children }: { children: React.ReactNode }) {
  const [books, setBooks] = useState<Book[]>([]);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [sales, setSales] = useState<Sale[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [stockLedger, setStockLedger] = useState<StockLedger[]>([]);

  useEffect(() => {
    // Load from localStorage
    const storedBooks = localStorage.getItem('books');
    const storedPurchases = localStorage.getItem('purchases');
    const storedSales = localStorage.getItem('sales');
    const storedContacts = localStorage.getItem('contacts');
    const storedStockLedger = localStorage.getItem('stockLedger');

    if (storedBooks) setBooks(JSON.parse(storedBooks));
    else setBooks(INITIAL_BOOKS);

    if (storedPurchases) setPurchases(JSON.parse(storedPurchases));
    if (storedSales) setSales(JSON.parse(storedSales));
    if (storedContacts) setContacts(JSON.parse(storedContacts));
    if (storedStockLedger) setStockLedger(JSON.parse(storedStockLedger));
  }, []);

  // Persist to localStorage
  useEffect(() => {
    localStorage.setItem('books', JSON.stringify(books));
  }, [books]);

  useEffect(() => {
    localStorage.setItem('purchases', JSON.stringify(purchases));
  }, [purchases]);

  useEffect(() => {
    localStorage.setItem('sales', JSON.stringify(sales));
  }, [sales]);

  useEffect(() => {
    localStorage.setItem('contacts', JSON.stringify(contacts));
  }, [contacts]);

  useEffect(() => {
    localStorage.setItem('stockLedger', JSON.stringify(stockLedger));
  }, [stockLedger]);

  const addBook = (book: Book) => {
    setBooks([...books, book]);
  };

  const updateBook = (book: Book) => {
    setBooks(books.map(b => (b.id === book.id ? book : b)));
  };

  const deleteBook = (id: string) => {
    setBooks(books.filter(b => b.id !== id));
  };

  const getBookStock = (bookId: string) => {
    const book = books.find(b => b.id === bookId);
    return book?.stock || 0;
  };

  const addPurchase = (purchase: Purchase) => {
    setPurchases([...purchases, purchase]);

    // Update stock
    const book = books.find(b => b.id === purchase.bookId);
    if (book) {
      const newStock = book.stock + purchase.quantity;
      updateBook({ ...book, stock: newStock });

      // Add to stock ledger
      setStockLedger([
        ...stockLedger,
        {
          id: Date.now().toString(),
          bookId: purchase.bookId,
          transactionType: 'purchase',
          quantity: purchase.quantity,
          previousStock: book.stock,
          newStock: newStock,
          referenceId: purchase.id,
          date: purchase.date,
          createdBy: purchase.createdBy,
        },
      ]);
    }
  };

  const getPurchases = (filters?: any) => {
    let result = [...purchases];
    if (filters?.bookId) result = result.filter(p => p.bookId === filters.bookId);
    if (filters?.contactId) result = result.filter(p => p.contactId === filters.contactId);
    if (filters?.dateFrom) result = result.filter(p => new Date(p.date) >= new Date(filters.dateFrom));
    if (filters?.dateTo) result = result.filter(p => new Date(p.date) <= new Date(filters.dateTo));
    return result.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  };

  const addSale = (sale: Sale) => {
    setSales([...sales, sale]);

    // Update stock
    const book = books.find(b => b.id === sale.bookId);
    if (book) {
      if (book.stock < sale.quantity) {
        throw new Error('Insufficient stock');
      }
      const newStock = book.stock - sale.quantity;
      updateBook({ ...book, stock: newStock });

      // Add to stock ledger
      setStockLedger([
        ...stockLedger,
        {
          id: Date.now().toString(),
          bookId: sale.bookId,
          transactionType: 'sale',
          quantity: sale.quantity,
          previousStock: book.stock,
          newStock: newStock,
          referenceId: sale.id,
          date: sale.date,
          createdBy: sale.createdBy,
        },
      ]);
    }
  };

  const getSales = (filters?: any) => {
    let result = [...sales];
    if (filters?.bookId) result = result.filter(s => s.bookId === filters.bookId);
    if (filters?.contactId) result = result.filter(s => s.contactId === filters.contactId);
    if (filters?.dateFrom) result = result.filter(s => new Date(s.date) >= new Date(filters.dateFrom));
    if (filters?.dateTo) result = result.filter(s => new Date(s.date) <= new Date(filters.dateTo));
    return result.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  };

  const addContact = (contact: Contact) => {
    setContacts([...contacts, contact]);
  };

  const updateContact = (contact: Contact) => {
    setContacts(contacts.map(c => (c.id === contact.id ? contact : c)));
  };

  const getContacts = (type?: 'supplier' | 'customer') => {
    if (type) return contacts.filter(c => c.type === type);
    return contacts;
  };

  const getStockLedger = (bookId: string) => {
    return stockLedger.filter(l => l.bookId === bookId);
  };

  return (
    <DataContext.Provider
      value={{
        books,
        purchases,
        sales,
        contacts,
        stockLedger,
        users: [],
        addBook,
        updateBook,
        deleteBook,
        getBookStock,
        addPurchase,
        getPurchases,
        addSale,
        getSales,
        addContact,
        updateContact,
        getContacts,
        getStockLedger,
      }}
    >
      {children}
    </DataContext.Provider>
  );
}

export function useData() {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useData must be used within DataProvider');
  }
  return context;
}
