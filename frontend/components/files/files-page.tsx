'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Upload, 
  Search, 
  FolderOpen, 
  File, 
  Image, 
  FileText, 
  Download,
  Share,
  Trash2,
  Eye,
  MoreHorizontal,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

export function FilesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [files, setFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const response = await api.getFiles();
      if (response.success && response.data) {
        setFiles(response.data);
      } else {
        toast.error('Erreur lors du chargement des fichiers');
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des fichiers');
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
      case 'webp':
        return <Image className="h-8 w-8 text-green-600" />;
      case 'pdf':
      case 'doc':
      case 'docx':
      case 'txt':
        return <FileText className="h-8 w-8 text-blue-600" />;
      case 'sql':
      case 'js':
      case 'ts':
      case 'py':
        return <File className="h-8 w-8 text-purple-600" />;
      default:
        return <File className="h-8 w-8 text-gray-600" />;
    }
  };

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const response = await api.uploadFile(file);
      if (response.success) {
        toast.success('Fichier uploadé avec succès');
        await loadFiles(); // Recharger la liste
      } else {
        toast.error(response.error || 'Erreur lors de l\'upload');
      }
    } catch (error) {
      toast.error('Erreur lors de l\'upload');
    } finally {
      setUploading(false);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const generatePublicLink = async (filename: string) => {
    try {
      const response = await api.getFileUrl(filename);
      if (response.success && response.data) {
        await navigator.clipboard.writeText(response.data.url);
        toast.success('Lien copié dans le presse-papiers');
      } else {
        toast.error('Erreur lors de la génération du lien');
      }
    } catch (error) {
      toast.error('Erreur lors de la génération du lien');
    }
  };

  const downloadFile = async (filename: string) => {
    try {
      const response = await api.getFileUrl(filename);
      if (response.success && response.data) {
        window.open(response.data.url, '_blank');
        toast.success('Téléchargement démarré');
      } else {
        toast.error('Erreur lors du téléchargement');
      }
    } catch (error) {
      toast.error('Erreur lors du téléchargement');
    }
  };

  const deleteFile = async (filename: string) => {
    try {
      const response = await api.deleteFile(filename);
      if (response.success) {
        setFiles(files.filter(f => f !== filename));
        toast.success('Fichier supprimé');
      } else {
        toast.error(response.error || 'Erreur lors de la suppression');
      }
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const filteredFiles = files.filter(filename => 
    filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Fichiers</h1>
          <p className="text-muted-foreground mt-1">
            Gérez vos fichiers avec MinIO
          </p>
        </div>
        <div className="flex space-x-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleUpload}
            className="hidden"
            accept="*/*"
          />
          <Button 
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Upload...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Uploader un fichier
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Storage Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold">-</div>
            <p className="text-sm text-muted-foreground">Utilisé</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold">{files.length}</div>
            <p className="text-sm text-muted-foreground">Fichiers</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold">1</div>
            <p className="text-sm text-muted-foreground">Bucket</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold">-</div>
            <p className="text-sm text-muted-foreground">Téléchargements</p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Rechercher un fichier..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Fichiers</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : filteredFiles.length === 0 ? (
            <div className="text-center py-8">
              <File className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Aucun fichier</h3>
              <p className="text-muted-foreground">
                {files.length === 0 ? 'Uploadez votre premier fichier' : 'Aucun résultat pour votre recherche'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredFiles.map((filename) => (
                <div key={filename} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50">
                  <div className="flex items-center space-x-4">
                    {getFileIcon(filename)}
                    <div>
                      <p className="font-medium">{filename}</p>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>Taille inconnue</span>
                        <span>Date inconnue</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => downloadFile(filename)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => generatePublicLink(filename)}
                    >
                      <Share className="h-4 w-4" />
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteFile(filename)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}