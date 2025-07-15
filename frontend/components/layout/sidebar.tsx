'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Home, 
  FolderOpen, 
  Users, 
  Database, 
  Files, 
  Settings, 
  BookOpen,
  Activity,
  LogOut,
  Shield,
  ChevronLeft,
  ChevronRight,
  Code
} from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { ThemeToggle } from '@/components/theme-toggle';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();

  const navigation = [
    { id: 'overview', label: 'Tableau de bord', icon: Home },
    { id: 'projects', label: 'Projets', icon: FolderOpen },
    { id: 'users', label: 'Utilisateurs', icon: Users },
    { id: 'database', label: 'Base de données', icon: Database },
    { id: 'files', label: 'Fichiers', icon: Files },
    { id: 'api', label: 'API Explorer', icon: Code },
    { id: 'monitoring', label: 'Supervision', icon: Activity },
    { id: 'docs', label: 'Documentation', icon: BookOpen },
    { id: 'settings', label: 'Paramètres', icon: Settings },
  ];

  return (
    <div className={`h-screen bg-card border-r flex flex-col transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <Shield className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold">Sovera</h1>
              <Badge variant="outline" className="text-xs">
                v1.0.0
              </Badge>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className="ml-auto"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <Button
              key={item.id}
              variant={activeTab === item.id ? 'default' : 'ghost'}
              className={`w-full justify-start ${collapsed ? 'px-2' : 'px-3'}`}
              onClick={() => onTabChange(item.id)}
            >
              <Icon className="h-4 w-4" />
              {!collapsed && <span className="ml-3">{item.label}</span>}
            </Button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t space-y-4">
        <div className="flex items-center justify-between">
          <ThemeToggle />
          {!collapsed && (
            <Badge variant="secondary" className="text-xs">
              Stockage local uniquement
            </Badge>
          )}
        </div>
        
        <Separator />
        
        <div className="flex items-center space-x-3">
          <Avatar className="h-8 w-8">
            <AvatarFallback>
              {user?.email?.charAt(0)?.toUpperCase() || 'A'}
            </AvatarFallback>
          </Avatar>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.email}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
          )}
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={logout}
          className={`w-full ${collapsed ? 'px-2' : 'px-3'}`}
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span className="ml-2">Déconnexion</span>}
        </Button>
      </div>
    </div>
  );
}