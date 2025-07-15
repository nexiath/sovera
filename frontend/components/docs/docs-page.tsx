'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { 
  BookOpen, 
  Search, 
  FileText, 
  Code, 
  Settings, 
  Database,
  Shield,
  ExternalLink
} from 'lucide-react';

export function DocsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeSection, setActiveSection] = useState('getting-started');

  const sections = [
    {
      id: 'getting-started',
      title: 'Démarrage rapide',
      icon: BookOpen,
      items: [
        'Installation',
        'Configuration initiale',
        'Premier projet',
        'Authentification'
      ]
    },
    {
      id: 'api',
      title: 'API REST',
      icon: Code,
      items: [
        'Authentification',
        'Endpoints',
        'Requêtes',
        'Réponses',
        'Pagination'
      ]
    },
    {
      id: 'database',
      title: 'Base de données',
      icon: Database,
      items: [
        'Connexion PostgreSQL',
        'Migrations',
        'Requêtes SQL',
        'Backup & Restore'
      ]
    },
    {
      id: 'storage',
      title: 'Stockage',
      icon: FileText,
      items: [
        'Configuration MinIO',
        'Upload de fichiers',
        'Liens publics',
        'Gestion des permissions'
      ]
    },
    {
      id: 'security',
      title: 'Sécurité',
      icon: Shield,
      items: [
        'Authentification JWT',
        'Permissions',
        'CORS',
        'Rate limiting'
      ]
    },
    {
      id: 'deployment',
      title: 'Déploiement',
      icon: Settings,
      items: [
        'Docker',
        'Configuration',
        'Variables d\'environnement',
        'Production'
      ]
    }
  ];

  const content = {
    'getting-started': {
      title: 'Démarrage rapide',
      content: `
# Bienvenue sur Sovera

Sovera est une alternative française à Supabase, entièrement open source et auto-hébergeable.

## Installation

### Prérequis

- Docker et Docker Compose
- PostgreSQL 13+
- MinIO pour le stockage

### Installation rapide

\`\`\`bash
git clone https://github.com/sovera-dev/sovera.git
cd sovera
docker-compose up -d
\`\`\`

## Configuration initiale

1. Créez votre premier utilisateur administrateur
2. Configurez votre base de données PostgreSQL
3. Paramétrez le stockage MinIO
4. Générez vos clés API

## Créer votre premier projet

1. Connectez-vous à l'interface d'administration
2. Cliquez sur "Nouveau projet"
3. Configurez votre base de données
4. Récupérez votre clé API

## Authentification

Sovera supporte plusieurs méthodes d'authentification :

- Email/mot de passe
- Magic links
- JWT tokens

### Exemple d'utilisation

\`\`\`javascript
import { createClient } from '@sovera/client'

const sovera = createClient(
  'https://your-instance.com',
  'your-api-key'
)

// Connexion
const { data, error } = await sovera.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})
\`\`\`
      `
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Documentation</h1>
          <p className="text-muted-foreground mt-1">
            Guide complet pour utiliser Sovera
          </p>
        </div>
        <Button 
          variant="outline"
          onClick={() => window.open('http://localhost:8000/docs', '_blank')}
        >
          <ExternalLink className="h-4 w-4 mr-2" />
          API Documentation (Swagger)
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Rechercher dans la documentation..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation */}
        <Card>
          <CardHeader>
            <CardTitle>Sections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {sections.map((section) => {
                const Icon = section.icon;
                return (
                  <div key={section.id}>
                    <Button
                      variant={activeSection === section.id ? 'default' : 'ghost'}
                      className="w-full justify-start"
                      onClick={() => setActiveSection(section.id)}
                    >
                      <Icon className="h-4 w-4 mr-2" />
                      {section.title}
                    </Button>
                    {activeSection === section.id && (
                      <div className="ml-6 mt-2 space-y-1">
                        {section.items.map((item) => (
                          <Button
                            key={item}
                            variant="ghost"
                            size="sm"
                            className="w-full justify-start text-sm"
                          >
                            {item}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Content */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>
                {content[activeSection as keyof typeof content]?.title || 'Documentation'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-slate dark:prose-invert max-w-none">
                {activeSection === 'getting-started' ? (
                  <div className="space-y-6">
                    <section>
                      <h2 className="text-2xl font-bold mb-4">Bienvenue sur Sovera</h2>
                      <p className="text-muted-foreground mb-4">
                        Sovera est une alternative française à Supabase, entièrement open source et auto-hébergeable.
                      </p>
                    </section>

                    <section>
                      <h3 className="text-xl font-semibold mb-3">Installation</h3>
                      <div className="bg-muted p-4 rounded-lg">
                        <h4 className="font-medium mb-2">Prérequis</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          <li>Docker et Docker Compose</li>
                          <li>PostgreSQL 13+</li>
                          <li>MinIO pour le stockage</li>
                        </ul>
                      </div>
                    </section>

                    <section>
                      <h4 className="font-medium mb-2">Installation rapide</h4>
                      <div className="bg-slate-900 text-slate-100 p-4 rounded-lg font-mono text-sm">
                        <div>git clone https://github.com/sovera-dev/sovera.git</div>
                        <div>cd sovera</div>
                        <div>docker-compose up -d</div>
                      </div>
                    </section>

                    <section>
                      <h3 className="text-xl font-semibold mb-3">Configuration initiale</h3>
                      <ol className="list-decimal list-inside space-y-2">
                        <li>Créez votre premier utilisateur administrateur</li>
                        <li>Configurez votre base de données PostgreSQL</li>
                        <li>Paramétrez le stockage MinIO</li>
                        <li>Générez vos clés API</li>
                      </ol>
                    </section>

                    <section>
                      <h3 className="text-xl font-semibold mb-3">Authentification</h3>
                      <p className="mb-4">
                        Sovera supporte plusieurs méthodes d'authentification :
                      </p>
                      <ul className="list-disc list-inside space-y-1 mb-4">
                        <li>Email/mot de passe</li>
                        <li>Magic links</li>
                        <li>JWT tokens</li>
                      </ul>
                      
                      <div className="bg-slate-900 text-slate-100 p-4 rounded-lg font-mono text-sm">
                        <div className="text-green-400">import</div>
                        <div>{'{ createClient }'} from '@sovera/client'</div>
                        <br />
                        <div className="text-blue-400">const</div>
                        <div>sovera = createClient(</div>
                        <div>&nbsp;&nbsp;'https://your-instance.com',</div>
                        <div>&nbsp;&nbsp;'your-api-key'</div>
                        <div>)</div>
                      </div>
                    </section>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">
                      Sélectionnez une section pour voir la documentation
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}