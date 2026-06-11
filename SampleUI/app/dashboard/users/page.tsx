'use client';

import { useAuth } from '@/lib/auth-context';
import { Card } from '@/components/ui/card';

export default function UsersPage() {
  const { user } = useAuth();

  if (user?.role !== 'owner') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="bg-red-50 border border-red-200 p-6">
          <p className="text-red-900 font-semibold">Access Denied</p>
          <p className="text-red-700 text-sm">Only owners can manage users</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">User Management</h1>
        <p className="text-muted-foreground mt-1">Manage staff members and permissions</p>
      </div>

      <Card className="bg-card border border-border p-6">
        <h3 className="font-semibold mb-4">Current Users</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center p-3 bg-muted rounded-lg">
            <div>
              <p className="font-medium">श्री शर्मा</p>
              <p className="text-sm text-muted-foreground">owner@sahitya.com</p>
            </div>
            <span className="px-3 py-1 bg-primary text-primary-foreground rounded-full text-xs font-medium">
              Owner
            </span>
          </div>

          <div className="flex justify-between items-center p-3 bg-muted rounded-lg">
            <div>
              <p className="font-medium">राज कुमार</p>
              <p className="text-sm text-muted-foreground">staff@sahitya.com</p>
            </div>
            <span className="px-3 py-1 bg-secondary text-secondary-foreground rounded-full text-xs font-medium">
              Employee
            </span>
          </div>
        </div>
      </Card>

      <Card className="bg-muted border border-border p-6">
        <p className="text-sm text-muted-foreground">
          In a production system, you would be able to add/remove employees, manage permissions, and view activity logs here.
        </p>
      </Card>
    </div>
  );
}
