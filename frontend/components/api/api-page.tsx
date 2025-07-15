'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { 
  Code, 
  Play, 
  Copy, 
  Key,
  Database,
  Settings,
  BookOpen,
  Plus
} from 'lucide-react';
import { toast } from 'sonner';

export function APIPage() {
  const [selectedEndpoint, setSelectedEndpoint] = useState('users');
  const [method, setMethod] = useState('GET');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const endpoints = [
    {
      table: 'users',
      endpoints: [
        { method: 'GET', path: '/api/users', description: 'Récupérer tous les utilisateurs' },
        { method: 'POST', path: '/api/users', description: 'Créer un utilisateur' },
        { method: 'GET', path: '/api/users/{id}', description: 'Récupérer un utilisateur' },
        { method: 'PUT', path: '/api/users/{id}', description: 'Modifier un utilisateur' },
        { method: 'DELETE', path: '/api/users/{id}', description: 'Supprimer un utilisateur' }
      ]
    },
    {
      table: 'products',
      endpoints: [
        { method: 'GET', path: '/api/products', description: 'Récupérer tous les produits' },
        { method: 'POST', path: '/api/products', description: 'Créer un produit' },
        { method: 'GET', path: '/api/products/{id}', description: 'Récupérer un produit' },
        { method: 'PUT', path: '/api/products/{id}', description: 'Modifier un produit' },
        { method: 'DELETE', path: '/api/products/{id}', description: 'Supprimer un produit' }
      ]
    },
    {
      table: 'orders',
      endpoints: [
        { method: 'GET', path: '/api/orders', description: 'Récupérer toutes les commandes' },
        { method: 'POST', path: '/api/orders', description: 'Créer une commande' },
        { method: 'GET', path: '/api/orders/{id}', description: 'Récupérer une commande' },
        { method: 'PUT', path: '/api/orders/{id}', description: 'Modifier une commande' },
        { method: 'DELETE', path: '/api/orders/{id}', description: 'Supprimer une commande' }
      ]
    }
  ];

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100';
      case 'POST':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100';
      case 'PUT':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100';
      case 'DELETE':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100';
    }
  };

  const handleTestAPI = async () => {
    setLoading(true);
    // Simuler un appel API
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const mockResponse = {
      data: [
        {
          id: 1,
          email: 'admin@sovera.fr',
          name: 'Administrateur',
          role: 'admin',
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: 2,
          email: 'dev@example.com',
          name: 'Développeur',
          role: 'developer',
          created_at: '2024-01-16T09:15:00Z'
        }
      ],
      meta: {
        count: 2,
        total: 2,
        page: 1,
        per_page: 10
      }
    };
    
    setResponse(JSON.stringify(mockResponse, null, 2));
    setLoading(false);
    toast.success('API testée avec succès');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copié dans le presse-papier');
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">API Explorer</h1>
          <p className="text-muted-foreground mt-1">
            Testez et documentez vos APIs REST
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <BookOpen className="h-4 w-4 mr-2" />
            Documentation
          </Button>
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Paramètres API
          </Button>
        </div>
      </div>

      {/* API Key */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Key className="h-5 w-5" />
            <span>Authentification</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2">
            <Input
              value="sk_live_abc123def456ghi789"
              readOnly
              className="font-mono"
            />
            <Button
              variant="outline"
              onClick={() => copyToClipboard('sk_live_abc123def456ghi789')}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Utilisez cette clé dans l'en-tête Authorization: Bearer [clé]
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Endpoints List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Database className="h-5 w-5" />
              <span>Endpoints</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {endpoints.map((table) => (
                <div key={table.table}>
                  <h4 className="font-medium mb-2 capitalize">{table.table}</h4>
                  <div className="space-y-2">
                    {table.endpoints.map((endpoint, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-2 rounded-lg hover:bg-muted cursor-pointer"
                        onClick={() => setSelectedEndpoint(endpoint.path)}
                      >
                        <div className="flex items-center space-x-2">
                          <Badge className={getMethodColor(endpoint.method)}>
                            {endpoint.method}
                          </Badge>
                          <span className="text-sm font-mono">{endpoint.path}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* API Tester */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Testeur d'API</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="request" className="w-full">
                <TabsList>
                  <TabsTrigger value="request">Requête</TabsTrigger>
                  <TabsTrigger value="response">Réponse</TabsTrigger>
                  <TabsTrigger value="headers">En-têtes</TabsTrigger>
                </TabsList>
                
                <TabsContent value="request" className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <select 
                      value={method} 
                      onChange={(e) => setMethod(e.target.value)}
                      className="px-3 py-2 border rounded-md"
                    >
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="DELETE">DELETE</option>
                    </select>
                    <Input
                      value={selectedEndpoint}
                      onChange={(e) => setSelectedEndpoint(e.target.value)}
                      placeholder="/api/users"
                      className="flex-1"
                    />
                    <Button onClick={handleTestAPI} disabled={loading}>
                      {loading ? (
                        <>
                          <Code className="h-4 w-4 mr-2 animate-spin" />
                          Test...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-2" />
                          Tester
                        </>
                      )}
                    </Button>
                  </div>
                  
                  {(method === 'POST' || method === 'PUT') && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Corps de la requête (JSON)</label>
                      <Textarea
                        placeholder='{"name": "Nouvel utilisateur", "email": "user@example.com"}'
                        className="font-mono"
                        rows={6}
                      />
                    </div>
                  )}
                </TabsContent>
                
                <TabsContent value="response" className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Réponse</label>
                      {response && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(response)}
                        >
                          <Copy className="h-4 w-4 mr-2" />
                          Copier
                        </Button>
                      )}
                    </div>
                    <Textarea
                      value={response}
                      readOnly
                      placeholder="La réponse apparaîtra ici..."
                      className="font-mono"
                      rows={15}
                    />
                  </div>
                </TabsContent>
                
                <TabsContent value="headers" className="space-y-4">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">En-têtes de requête</label>
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <Input placeholder="Nom" />
                          <Input placeholder="Valeur" />
                          <Button variant="outline" size="sm">
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium">En-têtes par défaut</label>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between p-2 bg-muted rounded">
                          <span>Content-Type</span>
                          <span>application/json</span>
                        </div>
                        <div className="flex justify-between p-2 bg-muted rounded">
                          <span>Authorization</span>
                          <span>Bearer sk_live_abc123def456ghi789</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}