'use client';

import { useData } from '@/lib/data-context';
import { useAuth } from '@/lib/auth-context';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { useState } from 'react';

export default function ReportsPage() {
  const { books, purchases, sales } = useData();
  const { user } = useAuth();
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  if (user?.role !== 'owner') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="bg-red-50 border border-red-200 p-6">
          <p className="text-red-900 font-semibold">Access Denied</p>
          <p className="text-red-700 text-sm">Only owners can access reports</p>
        </Card>
      </div>
    );
  }

  // Filter data by date range
  const filteredSales = sales.filter(s => {
    if (dateFrom && new Date(s.date) < new Date(dateFrom)) return false;
    if (dateTo && new Date(s.date) > new Date(dateTo)) return false;
    return true;
  });

  const filteredPurchases = purchases.filter(p => {
    if (dateFrom && new Date(p.date) < new Date(dateFrom)) return false;
    if (dateTo && new Date(p.date) > new Date(dateTo)) return false;
    return true;
  });

  // Calculate metrics
  const totalSalesRevenue = filteredSales.reduce((sum, s) => sum + s.totalPrice, 0);
  const totalSalesGst = filteredSales.reduce((sum, s) => sum + s.gstAmount, 0);
  const totalPurchasesCost = filteredPurchases.reduce((sum, p) => sum + p.totalPrice, 0);
  const totalPurchasesGst = filteredPurchases.reduce((sum, p) => sum + p.gstAmount, 0);
  const grossProfit = totalSalesRevenue - totalPurchasesCost;
  const netProfit = grossProfit - totalSalesGst + totalPurchasesGst;

  // Book-wise P&L
  const bookProfitLoss = books.map(book => {
    const bookSales = filteredSales.filter(s => s.bookId === book.id);
    const bookPurchases = filteredPurchases.filter(p => p.bookId === book.id);

    const salesValue = bookSales.reduce((sum, s) => sum + s.totalPrice, 0);
    const purchaseValue = bookPurchases.reduce((sum, p) => sum + p.totalPrice, 0);
    const profit = salesValue - purchaseValue;
    const margin = salesValue > 0 ? ((profit / salesValue) * 100).toFixed(2) : '0';

    return {
      book,
      salesQty: bookSales.reduce((sum, s) => sum + s.quantity, 0),
      salesValue,
      purchaseQty: bookPurchases.reduce((sum, p) => sum + p.quantity, 0),
      purchaseValue,
      profit,
      margin: parseFloat(margin),
    };
  }).filter(b => b.salesValue > 0 || b.purchaseValue > 0);

  const handleDownloadCSV = () => {
    const headers = ['Book', 'Sold Units', 'Sales Value', 'Purchased Units', 'Purchase Cost', 'Profit', 'Margin %'];
    const rows = bookProfitLoss.map(b => [
      b.book.titleDevanagari,
      b.salesQty,
      b.salesValue,
      b.purchaseQty,
      b.purchaseValue,
      b.profit,
      b.margin,
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(',')),
      '',
      ['Total', '', totalSalesRevenue, '', totalPurchasesCost, grossProfit, ''].join(','),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sales-purchase-report-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Financial Reports</h1>
        <p className="text-muted-foreground mt-1">Owner-only: View profit & loss, and financial metrics</p>
      </div>

      {/* Date Range Filter */}
      <Card className="bg-card border border-border p-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm font-medium mb-2">From Date</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">To Date</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <Button
            onClick={() => {
              setDateFrom('');
              setDateTo('');
            }}
            variant="outline"
          >
            Reset
          </Button>
        </div>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Total Sales Revenue</p>
          <p className="text-2xl font-bold text-green-700">₹{totalSalesRevenue.toLocaleString()}</p>
          <p className="text-xs text-muted-foreground mt-2">From {filteredSales.length} transactions</p>
        </Card>

        <Card className="bg-card border border-border p-4">
          <p className="text-sm text-muted-foreground mb-1">Total Purchase Cost</p>
          <p className="text-2xl font-bold text-red-700">₹{totalPurchasesCost.toLocaleString()}</p>
          <p className="text-xs text-muted-foreground mt-2">From {filteredPurchases.length} transactions</p>
        </Card>

        <Card className="bg-green-50 border border-green-200 p-4">
          <p className="text-sm text-green-800 mb-1">Gross Profit</p>
          <p className="text-2xl font-bold text-green-900">₹{grossProfit.toLocaleString()}</p>
          <p className="text-xs text-green-700 mt-2">
            {totalSalesRevenue > 0 ? `${((grossProfit / totalSalesRevenue) * 100).toFixed(1)}%` : '0%'} margin
          </p>
        </Card>

        <Card className="bg-blue-50 border border-blue-200 p-4">
          <p className="text-sm text-blue-800 mb-1">Net Profit</p>
          <p className="text-2xl font-bold text-blue-900">₹{netProfit.toLocaleString()}</p>
          <p className="text-xs text-blue-700 mt-2">After GST adjustments</p>
        </Card>
      </div>

      {/* Sales vs Purchase Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border border-border p-6">
          <h3 className="font-semibold mb-4">Sales Summary</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Revenue</span>
              <span className="font-semibold">₹{totalSalesRevenue.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">GST Collected</span>
              <span className="font-semibold">₹{totalSalesGst.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Number of Transactions</span>
              <span className="font-semibold">{filteredSales.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Average Transaction</span>
              <span className="font-semibold">
                ₹{filteredSales.length > 0 ? (totalSalesRevenue / filteredSales.length).toFixed(2) : '0'}
              </span>
            </div>
          </div>
        </Card>

        <Card className="bg-card border border-border p-6">
          <h3 className="font-semibold mb-4">Purchase Summary</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Cost</span>
              <span className="font-semibold">₹{totalPurchasesCost.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">GST Paid</span>
              <span className="font-semibold">₹{totalPurchasesGst.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Number of Transactions</span>
              <span className="font-semibold">{filteredPurchases.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Average Transaction</span>
              <span className="font-semibold">
                ₹{filteredPurchases.length > 0 ? (totalPurchasesCost / filteredPurchases.length).toFixed(2) : '0'}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Book-wise P&L */}
      <Card className="bg-card border border-border overflow-hidden">
        <div className="p-6 border-b border-border flex justify-between items-center">
          <h3 className="font-semibold">Book-wise Profit & Loss</h3>
          <Button onClick={handleDownloadCSV} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
        <table className="w-full">
          <thead className="bg-muted border-b border-border">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold">Book</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Sold</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Sales Value</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Bought</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Cost</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Profit</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Margin %</th>
            </tr>
          </thead>
          <tbody>
            {bookProfitLoss.map((item, idx) => (
              <tr key={item.book.id} className={idx % 2 ? 'bg-background' : ''}>
                <td className="px-6 py-3 text-sm font-medium">{item.book.titleDevanagari}</td>
                <td className="px-6 py-3 text-sm text-right">{item.salesQty}</td>
                <td className="px-6 py-3 text-sm text-right">₹{item.salesValue}</td>
                <td className="px-6 py-3 text-sm text-right">{item.purchaseQty}</td>
                <td className="px-6 py-3 text-sm text-right">₹{item.purchaseValue}</td>
                <td className={`px-6 py-3 text-sm text-right font-semibold ${
                  item.profit >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ₹{item.profit}
                </td>
                <td className="px-6 py-3 text-sm text-right font-semibold">{item.margin.toFixed(1)}%</td>
              </tr>
            ))}
            <tr className="bg-muted border-t border-border font-semibold">
              <td className="px-6 py-3">TOTAL</td>
              <td className="px-6 py-3 text-right"></td>
              <td className="px-6 py-3 text-right">₹{totalSalesRevenue}</td>
              <td className="px-6 py-3 text-right"></td>
              <td className="px-6 py-3 text-right">₹{totalPurchasesCost}</td>
              <td className="px-6 py-3 text-right text-green-600">₹{grossProfit}</td>
              <td className="px-6 py-3 text-right">
                {totalSalesRevenue > 0 ? `${((grossProfit / totalSalesRevenue) * 100).toFixed(1)}%` : '0%'}
              </td>
            </tr>
          </tbody>
        </table>
      </Card>
    </div>
  );
}
