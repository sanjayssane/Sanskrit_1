'use client';

import { useAuth } from '@/lib/auth-context';
import { Card } from '@/components/ui/card';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your profile and preferences</p>
      </div>

      <Card className="bg-card border border-border p-6">
        <h2 className="text-lg font-semibold mb-4">Profile Information</h2>
        <div className="space-y-3">
          <div>
            <p className="text-sm text-muted-foreground">Name</p>
            <p className="font-semibold">{user?.name}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Email</p>
            <p className="font-semibold">{user?.email}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Role</p>
            <p className="font-semibold capitalize">{user?.role}</p>
          </div>
        </div>
      </Card>

      <Card className="bg-muted border border-border p-6">
        <h2 className="text-lg font-semibold mb-2">Information</h2>
        <p className="text-sm text-muted-foreground">
          This is a demo system. All data is stored in your browser's local storage and will be reset on logout.
        </p>
      </Card>
    </div>
  );
}
