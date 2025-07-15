'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { 
  Plus, 
  FolderOpen, 
  Key, 
  Copy, 
  Settings, 
  Trash2,
  Users,
  Database,
  HardDrive,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';
import { ProjectConfigDialog } from './project-config-dialog';

interface Project {
  id: number;
  name: string;
  description?: string;
  api_key: string;
  owner_id: number;
  created_at: string;
  max_items?: number;
  storage_limit_mb?: number;
  api_rate_limit?: number;
  webhook_url?: string;
  is_public: boolean;
  auto_backup: boolean;
  backup_retention_days?: number;
}

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const [newProject, setNewProject] = useState({
    name: '',
    description: ''
  });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await api.getProjects();
      if (response.success && response.data) {
        setProjects(response.data);
      } else {
        toast.error('Erreur lors du chargement des projets');
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des projets');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async () => {
    if (!newProject.name.trim()) {
      toast.error('Le nom du projet est requis');
      return;
    }

    setCreating(true);
    try {
      const response = await api.createProject(newProject.name, newProject.description);
      if (response.success && response.data) {
        setProjects([...projects, response.data]);
        setNewProject({ name: '', description: '' });
        setDialogOpen(false);
        toast.success('Projet créé avec succès');
      } else {
        toast.error(response.error || 'Erreur lors de la création du projet');
      }
    } catch (error) {
      toast.error('Erreur lors de la création du projet');
    } finally {
      setCreating(false);
    }
  };

  const copyApiKey = (apiKey: string) => {
    navigator.clipboard.writeText(apiKey);
    toast.success('Clé API copiée');
  };

  const openConfigDialog = (project: Project) => {
    setSelectedProject(project);
    setConfigDialogOpen(true);
  };

  const handleProjectUpdate = (updatedProject: Project) => {
    setProjects(projects.map(p => p.id === updatedProject.id ? updatedProject : p));
  };

  const deleteProject = async (id: number) => {
    try {
      const response = await api.deleteProject(id);
      if (response.success) {
        setProjects(projects.filter(p => p.id !== id));
        toast.success('Projet supprimé');
      } else {
        toast.error(response.error || 'Erreur lors de la suppression');
      }
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Projets</h1>
          <p className="text-muted-foreground mt-1">
            Gérez vos projets et leurs configurations
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Nouveau projet
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Créer un nouveau projet</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nom du projet</Label>
                <Input
                  id="name"
                  value={newProject.name}
                  onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                  placeholder="Mon nouveau projet"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newProject.description}
                  onChange={(e) => setNewProject({...newProject, description: e.target.value})}
                  placeholder="Description du projet..."
                />
              </div>
              <Button onClick={handleCreateProject} className="w-full" disabled={creating}>
                {creating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Création...
                  </>
                ) : (
                  'Créer le projet'
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-8">
          <FolderOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Aucun projet</h3>
          <p className="text-muted-foreground">Créez votre premier projet pour commencer</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Card key={project.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FolderOpen className="h-8 w-8 text-blue-600" />
                    <div>
                      <CardTitle className="text-lg">{project.name}</CardTitle>
                      <p className="text-sm text-muted-foreground">{project.description || 'Aucune description'}</p>
                    </div>
                  </div>
                  <Badge variant="default">
                    Actif
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="flex items-center justify-center space-x-1">
                      <Database className="h-4 w-4 text-purple-600" />
                      <span className="text-sm font-medium">0</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Tables</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center space-x-1">
                      <Users className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium">0</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Utilisateurs</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center space-x-1">
                      <HardDrive className="h-4 w-4 text-orange-600" />
                      <span className="text-sm font-medium">0 MB</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Stockage</p>
                  </div>
                </div>

                {/* API Key */}
                <div className="bg-muted p-3 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Key className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Clé API</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyApiKey(project.api_key)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 font-mono">
                    {project.api_key}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => openConfigDialog(project)}
                  >
                    <Settings className="h-4 w-4 mr-2" />
                    Configurer
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => deleteProject(project.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>

                {/* Metadata */}
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>Créé le {new Date(project.created_at).toLocaleDateString('fr-FR')}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {selectedProject && (
        <ProjectConfigDialog
          project={selectedProject}
          open={configDialogOpen}
          onOpenChange={setConfigDialogOpen}
          onProjectUpdate={handleProjectUpdate}
        />
      )}
    </div>
  );
}