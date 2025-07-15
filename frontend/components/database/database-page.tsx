'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { 
  Database, 
  Table, 
  Plus, 
  Search,
  Edit,
  Trash2,
  Eye,
  Filter,
  ArrowUpDown,
  Loader2
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
}

interface Item {
  id: number;
  label: string;
  content: string;
  project_id: number;
  created_at: string;
}

export function DatabasePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Item | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const [newItem, setNewItem] = useState({
    label: '',
    content: ''
  });

  const [editItem, setEditItem] = useState({
    label: '',
    content: ''
  });

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadItems(selectedProject.id);
    }
  }, [selectedProject]);

  const loadProjects = async () => {
    try {
      const response = await api.getProjects();
      if (response.success && response.data) {
        setProjects(response.data);
        if (response.data.length > 0) {
          setSelectedProject(response.data[0]);
        }
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des projets');
    } finally {
      setLoading(false);
    }
  };

  const loadItems = async (projectId: number) => {
    setItemsLoading(true);
    try {
      const response = await api.getItems(projectId, {
        search: searchTerm || undefined,
        limit: 100
      });
      if (response.success && response.data) {
        setItems(response.data);
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des données');
    } finally {
      setItemsLoading(false);
    }
  };

  const handleCreateItem = async () => {
    if (!selectedProject || !newItem.label.trim() || !newItem.content.trim()) {
      toast.error('Tous les champs sont requis');
      return;
    }

    setCreating(true);
    try {
      const response = await api.createItem(selectedProject.id, newItem.label, newItem.content);
      if (response.success && response.data) {
        setItems([...items, response.data]);
        setNewItem({ label: '', content: '' });
        setDialogOpen(false);
        toast.success('Élément créé avec succès');
      } else {
        toast.error(response.error || 'Erreur lors de la création');
      }
    } catch (error) {
      toast.error('Erreur lors de la création');
    } finally {
      setCreating(false);
    }
  };

  const handleEditItem = async () => {
    if (!selectedProject || !editingItem || !editItem.label.trim() || !editItem.content.trim()) {
      toast.error('Tous les champs sont requis');
      return;
    }

    try {
      const response = await api.updateItem(selectedProject.id, editingItem.id, editItem.label, editItem.content);
      if (response.success && response.data) {
        setItems(items.map(item => item.id === editingItem.id ? response.data : item));
        setEditDialogOpen(false);
        setEditingItem(null);
        toast.success('Élément mis à jour avec succès');
      } else {
        toast.error(response.error || 'Erreur lors de la mise à jour');
      }
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    if (!selectedProject) return;

    try {
      const response = await api.deleteItem(selectedProject.id, itemId);
      if (response.success) {
        setItems(items.filter(item => item.id !== itemId));
        toast.success('Élément supprimé');
      } else {
        toast.error(response.error || 'Erreur lors de la suppression');
      }
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const openEditDialog = (item: Item) => {
    setEditingItem(item);
    setEditItem({
      label: item.label,
      content: item.content
    });
    setEditDialogOpen(true);
  };

  const filteredItems = items.filter(item => 
    item.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Base de données</h1>
          <p className="text-muted-foreground mt-1">
            Gérez vos données par projet
          </p>
        </div>
        <div className="flex space-x-2">
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button disabled={!selectedProject}>
                <Plus className="h-4 w-4 mr-2" />
                Nouvel élément
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Créer un nouvel élément</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="label">Label</Label>
                  <Input
                    id="label"
                    value={newItem.label}
                    onChange={(e) => setNewItem({...newItem, label: e.target.value})}
                    placeholder="Nom de l'élément"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="content">Contenu</Label>
                  <Textarea
                    id="content"
                    value={newItem.content}
                    onChange={(e) => setNewItem({...newItem, content: e.target.value})}
                    placeholder="Contenu de l'élément..."
                    rows={4}
                  />
                </div>
                <Button onClick={handleCreateItem} className="w-full" disabled={creating}>
                  {creating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Création...
                    </>
                  ) : (
                    'Créer l\'élément'
                  )}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Project Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Sélectionner un projet</CardTitle>
        </CardHeader>
        <CardContent>
          <Select 
            value={selectedProject?.id.toString()} 
            onValueChange={(value) => {
              const project = projects.find(p => p.id.toString() === value);
              setSelectedProject(project || null);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Sélectionner un projet" />
            </SelectTrigger>
            <SelectContent>
              {projects.map((project) => (
                <SelectItem key={project.id} value={project.id.toString()}>
                  {project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {selectedProject && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Données du projet: {selectedProject.name}</CardTitle>
              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Rechercher..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {itemsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : filteredItems.length === 0 ? (
              <div className="text-center py-8">
                <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Aucune donnée</h3>
                <p className="text-muted-foreground">
                  {items.length === 0 ? 'Créez votre premier élément' : 'Aucun résultat pour votre recherche'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium">ID</th>
                      <th className="text-left p-3 font-medium">Label</th>
                      <th className="text-left p-3 font-medium">Contenu</th>
                      <th className="text-left p-3 font-medium">Créé le</th>
                      <th className="text-left p-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredItems.map((item) => (
                      <tr key={item.id} className="border-b hover:bg-muted/50">
                        <td className="p-3">{item.id}</td>
                        <td className="p-3 font-medium">{item.label}</td>
                        <td className="p-3">
                          <div className="max-w-xs truncate">{item.content}</div>
                        </td>
                        <td className="p-3">
                          {new Date(item.created_at).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="p-3">
                          <div className="flex space-x-1">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => openEditDialog(item)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="text-red-600"
                              onClick={() => handleDeleteItem(item.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier l'élément</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit-label">Label</Label>
              <Input
                id="edit-label"
                value={editItem.label}
                onChange={(e) => setEditItem({...editItem, label: e.target.value})}
                placeholder="Nom de l'élément"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-content">Contenu</Label>
              <Textarea
                id="edit-content"
                value={editItem.content}
                onChange={(e) => setEditItem({...editItem, content: e.target.value})}
                placeholder="Contenu de l'élément..."
                rows={4}
              />
            </div>
            <div className="flex space-x-2">
              <Button onClick={handleEditItem} className="flex-1">
                Sauvegarder
              </Button>
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                Annuler
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}