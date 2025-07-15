/**
 * Dashboard homepage with project overview
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useProjectsStore, useToastStore } from '@/lib/store';
import { Overview } from '@/components/dashboard/overview';
import { ProjectOverview } from '@/components/dashboard/project-overview';
import { 
  FolderOpen, 
  HardDrive,
  TrendingUp,
  Server
} from 'lucide-react';
import { 
  Plus, 
  Database, 
  FileText, 
  Users, 
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const { projects, loadProjects, loading, error } = useProjectsStore();
  const { addToast } = useToastStore();

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    if (error) {
      addToast({
        title: 'Error',
        description: error,
        type: 'error',
      });
    }
  }, [error, addToast]);

  

  const stats = [
    {
      title: 'Total Projects',
      value: projects.length.toString(),
      change: 'All your projects',
      icon: FolderOpen,
      color: 'text-blue-600'
    },
    {
      title: 'Ready',
      value: projects.filter(p => p.provisioning_status === 'completed').length.toString(),
      change: 'Fully provisioned',
      icon: CheckCircle,
      color: 'text-green-600'
    },
    {
      title: 'Provisioning',
      value: projects.filter(p => p.provisioning_status === 'pending').length.toString(),
      change: 'Being set up',
      icon: Clock,
      color: 'text-yellow-600'
    },
    {
      title: 'Failed',
      value: projects.filter(p => p.provisioning_status === 'failed').length.toString(),
      change: 'Need attention',
      icon: XCircle,
      color: 'text-red-600'
    }
  ];

  const recentProjects = projects.map(project => ({
    name: project.name,
    status: project.provisioning_status === 'completed' ? 'Actif' : 'En développement',
    tables: 0, // This data is not available in the current project object
    users: 0, // This data is not available in the current project object
    storage: `${project.storage_limit_mb} MB`
  }));

  return (
    <div className="space-y-6">
      <Overview stats={stats} projects={recentProjects} />
      <ProjectOverview projects={projects} loading={loading} />
    </div>
  );
}