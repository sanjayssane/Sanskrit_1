export type UserRole = 'owner' | 'employee';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  active: boolean;
  createdAt: string;
}

export interface Book {
  id: string;
  titleDevanagari: string;
  titleRoman: string;
  authorDevanagari: string;
  authorRoman: string;
  sku: string;
  costPrice: number;
  salePrice: number;
  wholesalePrice?: number;
  stock: number;
  reorderLevel: number;
  category: string;
  description: string;
}

export interface Contact {
  id: string;
  type: 'supplier' | 'customer';
  nameDevanagari: string;
  nameRoman: string;
  email?: string;
  phone?: string;
  address?: string;
  gstin?: string;
}

export interface Purchase {
  id: string;
  contactId: string;
  bookId: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  invoiceNumber?: string;
  gstPercent: number;
  gstAmount: number;
  date: string;
  createdBy: string;
  notes?: string;
}

export interface Sale {
  id: string;
  contactId?: string;
  bookId: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  receiptNumber?: string;
  saleType: 'retail' | 'wholesale';
  gstPercent: number;
  gstAmount: number;
  paymentMethod: 'cash' | 'upi' | 'card' | 'cheque';
  date: string;
  createdBy: string;
  notes?: string;
}

export interface StockLedger {
  id: string;
  bookId: string;
  transactionType: 'purchase' | 'sale' | 'adjustment';
  quantity: number;
  previousStock: number;
  newStock: number;
  referenceId?: string;
  date: string;
  createdBy: string;
  notes?: string;
}

export interface SalesPurchaseStatement {
  bookId: string;
  titleDevanagari: string;
  titleRoman: string;
  purchases: {
    quantity: number;
    totalPrice: number;
  };
  sales: {
    quantity: number;
    totalPrice: number;
  };
  profit: number;
  margin: number;
}
