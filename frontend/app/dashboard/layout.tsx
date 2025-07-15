/**
 * Dashboard layout with project selection and navigation
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore, useProjectsStore, useToastStore } from '@/lib/store';
import { Project } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Bell, 
  Database, 
  FileText, 
  Settings, 
  Users, 
  LogOut, 
  Plus,
  Home,
  Activity
} from 'lucide-react';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  
  const { user, logout, isAuthenticated } = useAuthStore();
  const { projects, current_project, loadProjects, setCurrentProject, loadUserMembership, membership } = useProjectsStore();
  const { addToast } = useToastStore();

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isAuthenticated, router]);

  // Load projects on mount
  useEffect(() => {
    if (isAuthenticated) {
      loadProjects();
    }
  }, [isAuthenticated, loadProjects]);

  // Extract project ID from URL
  useEffect(() => {
    const match = pathname.match(/\/dashboard\/projects\/(\d+)/);
    if (match) {
      const projectId = parseInt(match[1]);
      setSelectedProjectId(projectId);
      
      // Find and set current project
      const project = projects.find(p => p.id === projectId);
      if (project) {
        setCurrentProject(project);
        loadUserMembership(projectId);
      }
    } else {
      setSelectedProjectId(null);
    }
  }, [pathname, projects, setCurrentProject, loadUserMembership]);

  const handleProjectChange = (projectId: string) => {
    const id = parseInt(projectId);
    const project = projects.find(p => p.id === id);
    if (project) {
      setCurrentProject(project);
      router.push(`/dashboard/projects/${id}`);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };

  const navigation = [
    { name: 'Overview', href: '/dashboard', icon: Home, current: pathname === '/dashboard' },
    { name: 'Activity', href: '/dashboard/activity', icon: Activity, current: pathname === '/dashboard/activity' },
  ];

  const projectNavigation = selectedProjectId ? [
    { name: 'Tables', href: `/dashboard/projects/${selectedProjectId}/tables`, icon: Database },
    { name: 'Files', href: `/dashboard/projects/${selectedProjectId}/files`, icon: FileText },
    { name: 'Members', href: `/dashboard/projects/${selectedProjectId}/members`, icon: Users },
    { name: 'Settings', href: `/dashboard/projects/${selectedProjectId}/settings`, icon: Settings },
  ] : [];

  const getProjectStatusBadge = (project: Project) => {
    switch (project.provisioning_status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-100 text-green-800">Ready</Badge>;
      case 'pending':
        return <Badge variant="secondary">Provisioning</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold">Sovera</h1>
            <Separator orientation="vertical" className="h-6" />
            
            {/* Project Selector */}
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">Project:</span>
              <Select value={selectedProjectId?.toString() || ''} onValueChange={handleProjectChange}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select a project" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={project.id.toString()}>
                      <div className="flex items-center justify-between w-full">
                        <span>{project.name}</span>
                        {getProjectStatusBadge(project)}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => router.push('/dashboard/projects/new')}
              >
                <Plus className="h-4 w-4 mr-1" />
                New Project
              </Button>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* User Role Badge */}
            {membership && current_project && (
              <Badge variant="outline" className="capitalize">
                {membership.role}
              </Badge>
            )}
            
            {/* Notifications */}
            <Button variant="ghost" size="sm">
              <Bell className="h-4 w-4" />
            </Button>
            
            {/* User Menu */}
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">{user?.email}</span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-73px)]">
        {/* Sidebar */}
        <aside className="w-64 border-r bg-white">
          <nav className="h-full overflow-y-auto p-4">
            {/* Main Navigation */}
            <div className="space-y-2">
              {navigation.map((item) => (
                <Button
                  key={item.name}
                  variant={item.current ? "default" : "ghost"}
                  className="w-full justify-start"
                  onClick={() => router.push(item.href)}
                >
                  <item.icon className="h-4 w-4 mr-2" />
                  {item.name}
                </Button>
              ))}
            </div>

            {/* Project Navigation */}
            {selectedProjectId && current_project && (
              <>
                <Separator className="my-4" />
                <div className="space-y-2">
                  <div className="px-2 py-1">
                    <h3 className="text-sm font-medium text-gray-500">
                      {current_project.name}
                    </h3>
                  </div>
                  {projectNavigation.map((item) => (
                    <Button
                      key={item.name}
                      variant={pathname === item.href ? "default" : "ghost"}
                      className="w-full justify-start"
                      onClick={() => router.push(item.href)}
                    >
                      <item.icon className="h-4 w-4 mr-2" />
                      {item.name}
                    </Button>
                  ))}
                </div>
              </>
            )}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}