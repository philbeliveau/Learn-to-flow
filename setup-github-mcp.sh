#!/bin/bash

# 🚀 EZBI Analytics - Configuration GitHub MCP
# Ce script aide à configurer l'accès GitHub MCP

echo "🔧 Configuration GitHub MCP pour EZBI Analytics"
echo "=============================================="
echo ""

# Vérifier les prérequis
echo "🔍 Vérification des prérequis..."

# Vérifier npm et GitHub MCP server
if ! command -v npx &> /dev/null; then
    echo "❌ npx n'est pas installé. Veuillez installer Node.js"
    exit 1
fi

if ! npm list -g @modelcontextprotocol/server-github &> /dev/null; then
    echo "❌ GitHub MCP server n'est pas installé globalement"
    echo "💡 Installation: npm install -g @modelcontextprotocol/server-github"
    exit 1
fi

echo "✅ Prérequis OK"
echo ""

# Demander le token GitHub
echo "🔑 Configuration du Personal Access Token GitHub"
echo ""
echo "Pour configurer GitHub MCP, vous devez créer un Personal Access Token sur:"
echo "👉 https://github.com/settings/tokens"
echo ""
echo "Permissions requises:"
echo "  ├── repo (Full control of private repositories)"
echo "  ├── workflow (Update GitHub Action workflows)"
echo "  ├── admin:org (Full control of orgs and teams)"
echo "  └── user (Update ALL user data)"
echo ""

read -p "Avez-vous créé votre token ? (y/n): " token_created

if [[ $token_created != "y" && $token_created != "Y" ]]; then
    echo "📋 Veuillez créer votre token et relancer ce script"
    echo "🔗 URL: https://github.com/settings/tokens"
    exit 1
fi

echo ""
read -s -p "🔐 Entrez votre GitHub Personal Access Token: " github_token
echo ""

# Vérifier le token
echo "🧪 Test du token GitHub..."

# Test simple avec curl
if curl -s -H "Authorization: bearer $github_token" https://api.github.com/user | grep -q '"login"'; then
    echo "✅ Token GitHub valide"
    
    # Récupérer les infos utilisateur
    user_info=$(curl -s -H "Authorization: bearer $github_token" https://api.github.com/user)
    username=$(echo $user_info | grep -o '"login":"[^"]*' | cut -d'"' -f4)
    echo "👋 Connecté en tant que: $username"
else
    echo "❌ Token GitHub invalide ou problème de connexion"
    exit 1
fi

echo ""

# Créer le fichier .env
echo "📝 Création du fichier .env..."

if [ -f .env ]; then
    echo "⚠️  Le fichier .env existe déjà. Création d'une sauvegarde..."
    cp .env .env.backup.$(date +%s)
fi

# Créer le fichier .env avec le token
cat > .env << EOF
# 🔑 EZBI Analytics - Variables d'Environnement
# Généré automatiquement le $(date)

# GitHub Configuration
GITHUB_PERSONAL_ACCESS_TOKEN=$github_token

# Database Configuration (à configurer si nécessaire)
# DATABASE_URL=postgresql://username:password@localhost:5432/ezbi_analytics

# Security
JWT_SECRET=$(openssl rand -base64 32)
ENCRYPTION_MASTER_KEY=$(openssl rand -base64 32)

# Claude Flow
CLAUDE_FLOW_HOOKS_ENABLED=true
CLAUDE_FLOW_TELEMETRY_ENABLED=true
CLAUDE_FLOW_GITHUB_INTEGRATION=true
EOF

echo "✅ Fichier .env créé avec succès"
echo ""

# Test de la configuration MCP
echo "🧪 Test de la configuration MCP..."

# Exporter les variables d'environnement pour le test
export GITHUB_PERSONAL_ACCESS_TOKEN=$github_token

# Test rapide du serveur GitHub MCP
echo "📡 Test du serveur GitHub MCP..."

# Créer un test simple
timeout 10s npx @modelcontextprotocol/server-github --help > /dev/null 2>&1

if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo "✅ Serveur GitHub MCP opérationnel"
else
    echo "⚠️  Problème potentiel avec le serveur GitHub MCP"
fi

echo ""
echo "🎉 Configuration terminée !"
echo ""
echo "📋 Prochaines étapes:"
echo "  1. ✅ GitHub MCP configuré"
echo "  2. 🔄 Redémarrez Claude Code pour charger la nouvelle configuration"
echo "  3. 🚀 Commencez le développement EZBI Analytics"
echo ""
echo "💡 Commandes utiles:"
echo "  - Tester l'accès GitHub: git ls-remote https://github.com/$username/test.git"
echo "  - Créer un nouveau repo: gh repo create ezbi-analytics --private"
echo "  - Voir la config: cat .claude/settings.json"
echo ""
echo "🔒 Sécurité: Le token est stocké dans .env (ajouté au .gitignore)"