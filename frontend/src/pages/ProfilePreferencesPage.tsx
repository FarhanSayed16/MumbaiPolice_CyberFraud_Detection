import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { userService } from '@/api/client';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ArrowLeft, Mail, AlertCircle } from 'lucide-react';

export const ProfilePreferencesPage: React.FC = () => {
  const { user, refreshProfile } = useAuth();
  const [enabled, setEnabled] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setEnabled(Boolean(user?.email_notifications_enabled));
  }, [user]);

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await userService.updatePreferences(user.id, enabled);
      await refreshProfile();
      setMessage('Preferences saved.');
    } catch {
      setError('Failed to save preferences.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-xl space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/dashboard">
          <Button variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
        </Link>
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200">Notification Preferences</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">Email digests and in-app alerts</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Mail className="h-4 w-4 text-indigo-600" />
            Email notifications
          </CardTitle>
          <CardDescription>
            When enabled, SLA and assignment alerts are sent via configured SMTP
            (`EMAIL_DELIVERY_MODE=smtp`). If SMTP is not set, delivery falls back to console mock.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-slate-300"
            />
            <span className="text-sm text-slate-700 dark:text-slate-300">
              Send email digests for case assignment, high-risk alerts, and SLA breaches
            </span>
          </label>

          <div className="flex items-start gap-2 rounded-md border border-emerald-200 bg-emerald-50 dark:bg-emerald-900/40 p-3 text-xs text-emerald-900">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <span>
              Live SMTP is configured for this environment. Alerts go to your official email when
              preferences are enabled.
            </span>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          {message && <p className="text-sm text-emerald-700">{message}</p>}

          <Button onClick={handleSave} disabled={saving || !user} size="sm">
            {saving ? 'Saving…' : 'Save preferences'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
