'use client';

import { useAuth } from '@/lib/auth-context';
import { AuthPage } from '@/components/auth/auth-page';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Overview } from '@/components/dashboard/overview';

export default function Home() {
  const { user } = useAuth();
  const router = useRouter();

  if (!user) {
    return <AuthPage />;
  }

  // Redirect to dashboard if user is logged in
  router.push('/dashboard');
  return null; // Or a loading spinner, etc.
}