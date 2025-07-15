# 🚀 Sovera - Plateforme Souveraine

![Sovera Logo](https://img.shields.io/badge/Sovera-Platform-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![Next.js](https://img.shields.io/badge/Next.js-13.5.1-black)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

## 🚀 Vue d'ensemble

Sovera est une **alternative française à Supabase**, entièrement auto-hébergeable et open source. C'est une plateforme de développement complète qui combine une base de données PostgreSQL, une authentification sécurisée, un stockage de fichiers, et une interface d'administration moderne.

### 🎯 Objectifs

- **Souveraineté numérique** : Gardez le contrôle total de vos données
- **Auto-hébergement** : Déployez sur votre propre infrastructure
- **Open Source** : Code ouvert et transparent
- **Performance** : Architecture moderne et optimisée
- **Sécurité** : Authentification robuste et gestion des permissions

## 🏗️ Architecture

### Stack Technologique

**Backend (API)**
- **FastAPI** - Framework web moderne et performant
- **SQLModel** - ORM basé sur SQLAlchemy et Pydantic
- **PostgreSQL** - Base de données relationnelle
- **MinIO** - Stockage d'objets S3-compatible
- **JWT** - Authentification par tokens
- **GraphQL** - API flexible avec Strawberry
- **WebSocket** - Communication temps réel

**Frontend (Interface)**
- **Next.js 13** - Framework React avec App Router
- **TypeScript** - Typage statique
- **Tailwind CSS** - Framework CSS utilitaire
- **Radix UI** - Components accessibles
- **Zustand** - Gestion d'état
- **shadcn/ui** - Bibliothèque de composants

**Infrastructure**
- **Docker** - Conteneurisation
- **Docker Compose** - Orchestration multi-services
- **Nginx** - Reverse proxy (optionnel)

## 🚀 Démarrage Rapide

### Prérequis

- Docker et Docker Compose
- Git
- Node.js 18+ (pour le développement)
- Python 3.11+ (pour le développement)

### Installation

1. **Cloner le projet**
```bash
git clone https://github.com/votre-username/sovera.git
cd sovera
```

2. **Configuration des variables d'environnement**
```bash
cp .env.example .env
```

Éditez le fichier `.env` avec vos valeurs :
```env
# Base de données
POSTGRES_DB=sovera_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Authentification
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stockage MinIO
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=your_secure_minio_password

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Lancer l'application**
```bash
docker-compose up -d
```

4. **Accéder aux services**
- **Application** : http://localhost:3000
- **API Backend** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Adminer (DB)** : http://localhost:8080
- **MinIO Console** : http://localhost:9001

### Création du premier utilisateur admin

```bash
docker-compose exec backend python scripts/create_admin.py
```

## 📁 Structure du Projet

```
sovera/
├── backend/                 # API FastAPI
│   ├── auth/               # Authentification et autorisation
│   ├── core/               # Configuration et utilitaires
│   ├── database/           # Session DB et multi-tenant
│   ├── models/             # Modèles SQLModel
│   ├── projects/           # Gestion des projets
│   ├── services/           # Services métier
│   ├── admin/              # Administration
│   ├── monitoring/         # Monitoring système
│   └── main.py            # Point d'entrée FastAPI
├── frontend/               # Interface Next.js
│   ├── app/               # Pages (App Router)
│   ├── components/        # Composants React
│   ├── lib/               # Utilitaires et types
│   └── hooks/             # React Hooks
├── docker-compose.yml      # Configuration Docker
└── README.md              # Documentation
```

## 🔐 Fonctionnalités

### Authentification et Autorisation
- **JWT** avec refresh tokens
- **RBAC** (Role-Based Access Control)
- **Multi-tenant** avec isolation des données
- **Permissions granulaires**

### Gestion des Projets
- **Espaces de travail** isolés
- **Membres** avec rôles différents
- **Tables** et schémas personnalisés
- **API GraphQL** par projet

### Stockage et Fichiers
- **MinIO** pour le stockage d'objets
- **Upload** sécurisé de fichiers
- **Permissions** par projet
- **Backup** automatique

### Interface d'Administration
- **Dashboard** temps réel
- **Gestion des utilisateurs**
- **Monitoring** système
- **Logs** centralisés

### API et Intégrations
- **REST API** complète
- **GraphQL** flexible
- **WebSocket** pour temps réel
- **Documentation** automatique

## 🛠️ Développement

### Environnement de développement

1. **Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Frontend**
```bash
cd frontend
npm install
npm run dev
```

### Structure des API

#### Endpoints principaux

- **Auth** : `/auth/login`, `/auth/register`, `/auth/refresh`
- **Projects** : `/projects/`, `/projects/{id}/`
- **Tables** : `/projects/{id}/tables/`
- **Files** : `/projects/{id}/files/`
- **Users** : `/admin/users/`
- **System** : `/system/health`, `/system/metrics`

#### GraphQL

Chaque projet dispose de son propre endpoint GraphQL :
```
/projects/{project_id}/graphql
```

### WebSocket

Connexions temps réel pour :
- Notifications
- Mises à jour des données
- Collaboration en temps réel

## 🐳 Déploiement

### Production avec Docker

1. **Préparer l'environnement**
```bash
# Cloner et configurer
git clone https://github.com/votre-username/sovera.git
cd sovera
cp .env.example .env
# Éditer .env avec vos valeurs de production
```

2. **Lancer en production**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Avec Nginx (recommandé)

```nginx
server {
    listen 80;
    server_name votre-domaine.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Monitoring

### Logs
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Métriques système
- CPU, RAM, Disque via `/system/metrics`
- Santé des services via `/system/health`
- Logs centralisés dans `backend/logs/`

## 🔧 Configuration Avancée

### Multi-tenant

Chaque projet est isolé avec :
- **Schéma DB** dédié
- **Permissions** spécifiques
- **Stockage** séparé

### Sécurité

- **HTTPS** obligatoire en production
- **CORS** configuré
- **Validation** des données
- **Rate limiting** (à implémenter)

### Backup

```bash
# Backup automatique DB
docker-compose exec backend python scripts/backup_db.py

# Backup MinIO
docker-compose exec minio mc mirror /data /backup
```

## 🤝 Contribution

### Workflow de développement

1. **Fork** le projet
2. **Créer** une branche feature : `git checkout -b feature/nouvelle-fonctionnalite`
3. **Commit** : `git commit -m 'Ajout nouvelle fonctionnalité'`
4. **Push** : `git push origin feature/nouvelle-fonctionnalite`
5. **Pull Request**

### Standards de code

- **Python** : PEP 8, type hints
- **TypeScript** : ESLint, Prettier
- **Commits** : Conventional Commits
- **Tests** : Pytest (backend), Jest (frontend)

## 📝 Roadmap

### Version 1.0
- [x] Authentification JWT
- [x] Multi-tenant
- [x] GraphQL par projet
- [x] Interface d'administration
- [x] Stockage de fichiers

### Version 1.1
- [ ] API REST complète
- [ ] Tests automatisés
- [ ] Documentation API
- [ ] Monitoring avancé

### Version 1.2
- [ ] Webhooks
- [ ] Intégrations tierces
- [ ] Backup automatique
- [ ] Clustering

## 🐛 Problèmes Connus

### Limitations actuelles
- Pas de clustering multi-instances
- Backup manuel uniquement
- Pas de rate limiting

### Corrections en cours
- Optimisation des performances
- Amélioration de la sécurité
- Tests automatisés

## 📚 Documentation

### Liens utiles
- **API Docs** : http://localhost:8000/docs
- **GraphQL Playground** : http://localhost:8000/projects/{id}/graphql
- **Adminer** : http://localhost:8080
- **MinIO Console** : http://localhost:9001

### Guides
- [Installation détaillée](docs/installation.md)
- [Configuration](docs/configuration.md)
- [API Reference](docs/api.md)
- [Déploiement](docs/deployment.md)

## 📄 Licence

Ce projet est sous licence [MIT](LICENSE).

## 🙏 Remerciements

- **FastAPI** pour le framework backend
- **Next.js** pour le framework frontend
- **Supabase** pour l'inspiration
- **Communauté Open Source**

## 📞 Support

### Contactez-nous
- **Email** : support@sovera.fr
- **Discord** : https://discord.gg/sovera
- **GitHub Issues** : https://github.com/votre-username/sovera/issues

### FAQ

**Q: Puis-je utiliser Sovera en production ?**
R: Oui, mais testez d'abord en développement. Version 1.0 stable prévue bientôt.

**Q: Comment migrer depuis Supabase ?**
R: Un outil de migration est en développement. Contactez-nous pour l'aide.

**Q: Sovera est-il compatible avec les clients Supabase ?**
R: Partiellement. Nous travaillons sur une API compatible.

---

**Fait avec ❤️ en France pour la souveraineté numérique**
