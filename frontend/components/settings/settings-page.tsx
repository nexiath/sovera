'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Settings, 
  Server, 
  Database, 
  Shield, 
  Download,
  Upload,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';

export function SettingsPage() {
  const [instanceSettings, setInstanceSettings] = useState({
    name: 'Sovera Production',
    url: 'https://sovera.mondomaine.fr',
    port: 8000,
    allowSignup: true,
    emailConfirmation: false,
    maxFileSize: 10,
    backupEnabled: true,
    backupSchedule: 'daily'
  });

  const handleSave = () => {
    toast.success('Paramètres sauvegardés');
  };

  const handleBackup = () => {
    toast.success('Sauvegarde lancée');
  };

  const handleRestore = () => {
    toast.success('Restauration lancée');
  };

  const handleRestart = () => {
    toast.success('Redémarrage du système');
  };

  const exportData = () => {
    const data = {
      users: [],
      projects: [],
      settings: instanceSettings,
      exported_at: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sovera-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    
    toast.success('Données exportées');
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Paramètres</h1>
          <p className="text-muted-foreground mt-1">
            Configurez votre instance Sovera
          </p>
        </div>
        <Button onClick={handleSave}>
          Sauvegarder les modifications
        </Button>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList>
          <TabsTrigger value="general">Général</TabsTrigger>
          <TabsTrigger value="database">Base de données</TabsTrigger>
          <TabsTrigger value="security">Sécurité</TabsTrigger>
          <TabsTrigger value="backup">Sauvegarde</TabsTrigger>
          <TabsTrigger value="system">Système</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="h-5 w-5" />
                <span>Configuration générale</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="instance-name">Nom de l'instance</Label>
                  <Input
                    id="instance-name"
                    value={instanceSettings.name}
                    onChange={(e) => setInstanceSettings({...instanceSettings, name: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="instance-url">URL publique</Label>
                  <Input
                    id="instance-url"
                    value={instanceSettings.url}
                    onChange={(e) => setInstanceSettings({...instanceSettings, url: e.target.value})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="port">Port</Label>
                <Input
                  id="port"
                  type="number"
                  value={instanceSettings.port}
                  onChange={(e) => setInstanceSettings({...instanceSettings, port: parseInt(e.target.value)})}
                  className="w-32"
                />
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Autoriser les inscriptions</Label>
                    <p className="text-sm text-muted-foreground">
                      Permettre aux nouveaux utilisateurs de s'inscrire
                    </p>
                  </div>
                  <Switch
                    checked={instanceSettings.allowSignup}
                    onCheckedChange={(checked) => setInstanceSettings({...instanceSettings, allowSignup: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Confirmation par email</Label>
                    <p className="text-sm text-muted-foreground">
                      Exiger une confirmation par email pour les nouveaux comptes
                    </p>
                  </div>
                  <Switch
                    checked={instanceSettings.emailConfirmation}
                    onCheckedChange={(checked) => setInstanceSettings({...instanceSettings, emailConfirmation: checked})}
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="max-file-size">Taille maximale des fichiers (MB)</Label>
                <Input
                  id="max-file-size"
                  type="number"
                  value={instanceSettings.maxFileSize}
                  onChange={(e) => setInstanceSettings({...instanceSettings, maxFileSize: parseInt(e.target.value)})}
                  className="w-32"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="database" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Database className="h-5 w-5" />
                <span>Configuration PostgreSQL</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Hôte</Label>
                  <Input value="localhost" readOnly />
                </div>
                <div className="space-y-2">
                  <Label>Port</Label>
                  <Input value="5432" readOnly />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Base de données</Label>
                <Input value="sovera" readOnly />
              </div>

              <div className="space-y-2">
                <Label>Statut de la connexion</Label>
                <div className="flex items-center space-x-2">
                  <Badge variant="default">Connecté</Badge>
                  <span className="text-sm text-muted-foreground">
                    Dernière vérification: il y a 2 minutes
                  </span>
                </div>
              </div>

              <Separator />

              <Button onClick={() => toast.success('Connexion testée')}>
                Tester la connexion
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>Sécurité</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-yellow-50 dark:bg-yellow-900/10 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-600" />
                  <h4 className="font-medium">Conformité RGPD</h4>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Toutes les données sont stockées localement. Aucune donnée n'est transmise à des tiers.
                </p>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Durée de validité des tokens JWT (heures)</Label>
                  <Input type="number" value="24" className="w-32" />
                </div>

                <div className="space-y-2">
                  <Label>Tentatives de connexion autorisées</Label>
                  <Input type="number" value="5" className="w-32" />
                </div>

                <div className="space-y-2">
                  <Label>Durée de blocage après échec (minutes)</Label>
                  <Input type="number" value="15" className="w-32" />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <Button variant="outline" className="w-full">
                  Régénérer les clés JWT
                </Button>
                <Button 
                  variant="outline" 
                  onClick={exportData}
                  className="w-full"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Exporter mes données (JSON)
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="backup" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Sauvegarde et restauration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Sauvegardes automatiques</Label>
                  <p className="text-sm text-muted-foreground">
                    Activer les sauvegardes automatiques
                  </p>
                </div>
                <Switch
                  checked={instanceSettings.backupEnabled}
                  onCheckedChange={(checked) => setInstanceSettings({...instanceSettings, backupEnabled: checked})}
                />
              </div>

              <div className="space-y-2">
                <Label>Fréquence des sauvegardes</Label>
                <select 
                  value={instanceSettings.backupSchedule}
                  onChange={(e) => setInstanceSettings({...instanceSettings, backupSchedule: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="hourly">Toutes les heures</option>
                  <option value="daily">Quotidienne</option>
                  <option value="weekly">Hebdomadaire</option>
                  <option value="monthly">Mensuelle</option>
                </select>
              </div>

              <Separator />

              <div className="space-y-2">
                <h4 className="font-medium">Actions manuelles</h4>
                <div className="flex space-x-2">
                  <Button onClick={handleBackup} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Créer une sauvegarde
                  </Button>
                  <Button onClick={handleRestore} variant="outline">
                    <Upload className="h-4 w-4 mr-2" />
                    Restaurer
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Server className="h-5 w-5" />
                <span>Système</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Version</Label>
                  <div className="flex items-center space-x-2">
                    <Badge>v1.0.0</Badge>
                    <span className="text-sm text-muted-foreground">
                      Dernière mise à jour
                    </span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Uptime</Label>
                  <span className="text-sm">12h 34m 56s</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Stockage disponible</Label>
                <div className="flex items-center space-x-2">
                  <span className="text-sm">8.1 GB / 10 GB</span>
                  <Badge variant="secondary">81%</Badge>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <h4 className="font-medium">Actions système</h4>
                <div className="flex space-x-2">
                  <Button onClick={handleRestart} variant="outline">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Redémarrer
                  </Button>
                  <Button variant="outline">
                    Vérifier les mises à jour
                  </Button>
                </div>
              </div>

              <div className="bg-red-50 dark:bg-red-900/10 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  <h4 className="font-medium">Zone dangereuse</h4>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Ces actions sont irréversibles. Assurez-vous d'avoir une sauvegarde récente.
                </p>
                <Button variant="destructive" className="mt-3">
                  Réinitialiser l'instance
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}