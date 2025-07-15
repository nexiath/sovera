'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  FolderOpen, 
  Users, 
  Database, 
  HardDrive, 
  Activity, 
  TrendingUp,
  Server,
  Clock
} from 'lucide-react';

interface OverviewProps {
  stats: {
    title: string;
    value: string;
    change: string;
    icon: React.ElementType;
    color: string;
  }[];
  projects: {
    name: string;
    status: string;
    tables: number;
    users: number;
    storage: string;
  }[];
}

export function Overview({ stats, projects }: OverviewProps) {

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tableau de bord</h1>
          <p className="text-muted-foreground mt-1">
            Vue d'overview de votre instance Sovera
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-green-500" />
          <span className="text-sm font-medium">Système opérationnel</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stat.change}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Projects Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Projets récents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {projects.map((project) => (
              <div key={project.name} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <FolderOpen className="h-8 w-8 text-blue-600" />
                  <div>
                    <h4 className="font-medium">{project.name}</h4>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>{project.tables} tables</span>
                      <span>{project.users} utilisateurs</span>
                      <span>{project.storage}</span>
                    </div>
                  </div>
                </div>
                <Badge variant={project.status === 'Actif' ? 'default' : 'secondary'}>
                  {project.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}