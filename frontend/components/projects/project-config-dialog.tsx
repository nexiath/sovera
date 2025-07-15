'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Settings, 
  Database, 
  Shield, 
  Webhook, 
  Archive,
  Loader2,
  Save,
  AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

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

interface ProjectConfigDialogProps {
  project: Project;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectUpdate: (updatedProject: Project) => void;
}

export function ProjectConfigDialog({ project, open, onOpenChange, onProjectUpdate }: ProjectConfigDialogProps) {
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState({
    name: project.name,
    description: project.description || '',
    max_items: project.max_items || 1000,
    storage_limit_mb: project.storage_limit_mb || 100,
    api_rate_limit: project.api_rate_limit || 1000,
    webhook_url: project.webhook_url || '',
    is_public: project.is_public,
    auto_backup: project.auto_backup,
    backup_retention_days: project.backup_retention_days || 30,
  });

  const handleSave = async () => {
    setLoading(true);
    try {
      const response = await api.updateProject(project.id, config);
      if (response.success && response.data) {
        onProjectUpdate(response.data);
        onOpenChange(false);
        toast.success('Configuration sauvegardée');
      } else {
        toast.error(response.error || 'Erreur lors de la sauvegarde');
      }
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  const resetConfig = () => {
    setConfig({
      name: project.name,
      description: project.description || '',
      max_items: project.max_items || 1000,
      storage_limit_mb: project.storage_limit_mb || 100,
      api_rate_limit: project.api_rate_limit || 1000,
      webhook_url: project.webhook_url || '',
      is_public: project.is_public,
      auto_backup: project.auto_backup,
      backup_retention_days: project.backup_retention_days || 30,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Configuration du projet</span>
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="general" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="general">Général</TabsTrigger>
            <TabsTrigger value="limits">Limites</TabsTrigger>
            <TabsTrigger value="security">Sécurité</TabsTrigger>
            <TabsTrigger value="webhooks">Webhooks</TabsTrigger>
            <TabsTrigger value="backup">Sauvegarde</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="h-4 w-4" />
                  <span>Informations générales</span>
                </CardTitle>
                <CardDescription>
                  Configurez les informations de base de votre projet
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nom du projet</Label>
                  <Input
                    id="name"
                    value={config.name}
                    onChange={(e) => setConfig({...config, name: e.target.value})}
                    placeholder="Nom du projet"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={config.description}
                    onChange={(e) => setConfig({...config, description: e.target.value})}
                    placeholder="Description du projet..."
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="limits" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="h-4 w-4" />
                  <span>Limites et quotas</span>
                </CardTitle>
                <CardDescription>
                  Définissez les limites d'utilisation de votre projet
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="max_items">Nombre maximum d'éléments</Label>
                    <Input
                      id="max_items"
                      type="number"
                      value={config.max_items}
                      onChange={(e) => setConfig({...config, max_items: parseInt(e.target.value)})}
                      min="1"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="storage_limit">Limite de stockage (MB)</Label>
                    <Input
                      id="storage_limit"
                      type="number"
                      value={config.storage_limit_mb}
                      onChange={(e) => setConfig({...config, storage_limit_mb: parseInt(e.target.value)})}
                      min="1"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="api_rate_limit">Limite API (appels/heure)</Label>
                    <Input
                      id="api_rate_limit"
                      type="number"
                      value={config.api_rate_limit}
                      onChange={(e) => setConfig({...config, api_rate_limit: parseInt(e.target.value)})}
                      min="1"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Shield className="h-4 w-4" />
                  <span>Paramètres de sécurité</span>
                </CardTitle>
                <CardDescription>
                  Configurez les options de sécurité et d'accès
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Projet public</Label>
                    <p className="text-sm text-muted-foreground">
                      Permettre l'accès public aux données du projet
                    </p>
                  </div>
                  <Switch
                    checked={config.is_public}
                    onCheckedChange={(checked) => setConfig({...config, is_public: checked})}
                  />
                </div>
                {config.is_public && (
                  <div className="flex items-start space-x-2 p-3 rounded-lg bg-yellow-50 border border-yellow-200">
                    <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
                    <div className="text-sm text-yellow-700">
                      <p className="font-medium">Attention !</p>
                      <p>En rendant votre projet public, toutes les données seront accessibles sans authentification.</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="webhooks" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Webhook className="h-4 w-4" />
                  <span>Webhooks</span>
                </CardTitle>
                <CardDescription>
                  Configurez les notifications webhook pour les événements du projet
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="webhook_url">URL de webhook</Label>
                  <Input
                    id="webhook_url"
                    value={config.webhook_url}
                    onChange={(e) => setConfig({...config, webhook_url: e.target.value})}
                    placeholder="https://example.com/webhook"
                    type="url"
                  />
                  <p className="text-sm text-muted-foreground">
                    Les événements seront envoyés en POST vers cette URL
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="backup" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Archive className="h-4 w-4" />
                  <span>Sauvegarde automatique</span>
                </CardTitle>
                <CardDescription>
                  Configurez les options de sauvegarde automatique
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Sauvegarde automatique</Label>
                    <p className="text-sm text-muted-foreground">
                      Créer automatiquement des sauvegardes quotidiennes
                    </p>
                  </div>
                  <Switch
                    checked={config.auto_backup}
                    onCheckedChange={(checked) => setConfig({...config, auto_backup: checked})}
                  />
                </div>
                {config.auto_backup && (
                  <div className="space-y-2">
                    <Label htmlFor="backup_retention">Rétention (jours)</Label>
                    <Input
                      id="backup_retention"
                      type="number"
                      value={config.backup_retention_days}
                      onChange={(e) => setConfig({...config, backup_retention_days: parseInt(e.target.value)})}
                      min="1"
                      max="365"
                    />
                    <p className="text-sm text-muted-foreground">
                      Nombre de jours à conserver les sauvegardes
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex justify-between pt-4 border-t">
          <Button variant="outline" onClick={resetConfig}>
            Réinitialiser
          </Button>
          <div className="space-x-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button onClick={handleSave} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sauvegarde...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Sauvegarder
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}