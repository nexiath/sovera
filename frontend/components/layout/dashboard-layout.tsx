'use client';

import { useState } from 'react';
import { Sidebar } from './sidebar';
import { ProjectsPage } from '@/components/projects/projects-page';
import { UsersPage } from '@/components/users/users-page';
import { DatabasePage } from '@/components/database/database-page';
import { FilesPage } from '@/components/files/files-page';
import { APIPage } from '@/components/api/api-page';
import { MonitoringPage } from '@/components/monitoring/monitoring-page';
import { DocsPage } from '@/components/docs/docs-page';
import { SettingsPage } from '@/components/settings/settings-page';

interface DashboardLayoutProps {
  children?: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [activeTab, setActiveTab] = useState('overview');

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return children;
      case 'projects':
        return <ProjectsPage />;
      case 'users':
        return <UsersPage />;
      case 'database':
        return <DatabasePage />;
      case 'files':
        return <FilesPage />;
      case 'api':
        return <APIPage />;
      case 'monitoring':
        return <MonitoringPage />;
      case 'docs':
        return <DocsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return children;
    }
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-auto">
        {renderContent()}
      </main>
    </div>
  );
}