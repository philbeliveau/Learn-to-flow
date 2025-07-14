🎯 You are acting as a senior product strategist and full-stack architect.

You are tasked with generating the complete frontend and backend of a predictive platform called **EZBI** for B2B sales and cash flow forecasting.

### 🧠 Goal:
Build a web application (frontend on Vercel, backend on Railway) that allows users in manufacturing companies to:

- Upload non-structured files (Excel, CSV, PDFs)
- Extract and qualify leads and customers from sales data
- Predict future sales and cash flows over a 3–6 month horizon
- Visualize forecasts, confidence intervals, and payment behavior
- Compare expected cash inflows vs. historical trends

### 🏭 Target Market:
- B2B companies with long sales cycles
- Manufacturing firms with irregular client orders and payment delays
- SMBs lacking advanced CRM and forecasting tools

### 💡 Key Insight:
Clients want simple predictive insights from messy internal data (Excel exports from ERP or accounting tools). They don’t want to change software – just get better visibility and decision support.

---

## 🧱 Build this in: `task/Ventes-CashFlow-Prediction`

Deliver a complete French-language MVP.

Include:
- Upload module
- Data extraction pipeline from Excel (non-normalized tables)
- Lead classification logic
- Time series modeling (e.g. LSTM, or regression-based)
- Forecast visualizations (line graph, prediction intervals)
- Forecast export (CSV, PNG)
- User dashboard (Recent uploads, status, alerts)
- Cash-flow dashboard
- API for predictions

Use Next.js + Tailwind + Typescript for frontend  
Use FastAPI or Express.js for backend  
Use Railway for deployment

---

## 📝 Product Requirements Document (FR)

🧾 PRD – Plateforme EZBI
🧭 Objectif du projet
Une plateforme web pour automatiser l'extraction de données de ventes à partir de fichiers internes (Excel/CSV), classifier les leads, et prédire les flux de ventes et de trésorerie à court terme pour les entreprises manufacturières.

🎯 Proposition de valeur
Transformez vos feuilles Excel en prédictions intelligentes. EZBI vous aide à anticiper les ventes, qualifier vos clients, et visualiser vos flux de trésorerie, sans changer vos outils existants.

🧑‍💼 Segments cibles
Segment	Besoin principal
PME manufacturières	Visibilité sur les flux de trésorerie à 3–6 mois
Directeurs des ventes	Prioriser les leads avec plus de chances de convertir
Contrôleurs financiers	Éviter les ruptures de trésorerie
Agents de développement B2B	Comprendre les comportements de paiement

🧩 Fonctionnalités principales
Fonction	Description
📤 Upload de fichiers	Excel (.xlsx, .csv), identification des feuilles et colonnes pertinentes
🧠 Extraction de données	Détection des clients, montants, dates, statuts, fréquence de commandes
🗂️ Classification des leads	Analyse de récence, fréquence, montant (modèle RFM ou K-Means)
📈 Prédiction de ventes	Modèles Time Series adaptés au contexte (ARIMA, Prophet, ML...)
💸 Prévision de cash flow	Intègre comportements de paiement (délais, échéances)
📊 Visualisation	Graphiques ligne, bande de confiance, camemberts, heatmap clients
🧾 Export des prévisions	CSV des résultats, PNG des graphiques
📚 Historique des fichiers	Dashboard utilisateur avec statut des traitements passés

🧪 Architecture Technique
Côté	Stack / Technologie
Frontend	Next.js + Tailwind CSS + Typescript
Backend	FastAPI ou Express.js
Modèle prédictif	Prophet, ARIMA, ou Random Forest Regressor
Pipeline de données	pandas + openpyxl (lecture Excel)
Hébergement frontend	Vercel
Hébergement backend	Railway
Intégration dans le channel slack des entreprises **primordial**

🧱 Composants UI
UploadBox(fileType: xlsx | csv)

LeadInsightsCard(clientName, score, frequency, montantMoyen)

ForecastGraph(data, interval, yLabel)

CashflowChart(cashInForecast, cashOutHistory)

StatusTimeline(processingStage, timestamps)

ExportButton(type: csv | png)

🔗 Routes API (backend)
Méthode	Route	Description
POST	/api/upload	Upload de fichier Excel
GET	/api/leads	Retourne les leads classifiés
GET	/api/forecast/sales	Prévision des ventes
GET	/api/forecast/cashflow	Prévision des entrées de trésorerie
GET	/api/history	Liste des fichiers traités

📅 Timeline MVP (3 phases)
Semaine	Étapes principales
1	Implémentation du frontend + pages upload/status
2	Extraction automatique + premiers modèles ML
3	Visualisations, export, dashboard utilisateur

📌 À noter pour Claude-code
Utiliser le français pour toutes les routes, labels, titres.

Afficher les unités monétaires en € (euros).

Rendre l'interface très simple à utiliser (1–2 clics max pour obtenir des insights).

Ne pas nécessiter d'authentification pour la démo (mode public).

---

## 🧠 MODÈLES PRÉDICTIFS ET DONNÉES DE DÉMO

### 📊 Modèles Machine Learning Recommandés

Basé sur les dernières recherches (2025), voici la hiérarchie de performance pour la prédiction de cash flow :

#### 1. **LSTM (Long Short-Term Memory)** - RECOMMANDÉ ⭐
- **Performance** : 30-day LSTM plus précis qu'un 1-day ARIMA/Prophet
- **Cas d'usage** : Données complexes, patterns non-linéaires, prédictions long-terme
- **Implémentation** : TensorFlow/Keras avec preprocessing pandas
- **Avantages** : Capture les dépendances long-terme, gère la saisonnalité complexe

#### 2. **Prophet (Facebook)** - BUSINESS-FRIENDLY ⭐
- **Performance** : Excellent pour données saisonnières avec missing values
- **Cas d'usage** : Entreprises manufacturières avec cycles saisonniers
- **Implémentation** : `pip install prophet`, API simple
- **Avantages** : Gère automatiquement saisonnalité, jours fériés, données manquantes

#### 3. **ARIMA** - BASELINE SOLIDE
- **Performance** : Efficace pour données stationnaires court-terme
- **Cas d'usage** : Prédictions rapides, données simples
- **Implémentation** : `statsmodels.tsa.arima`
- **Avantages** : Rapide, interprétable, peu de données requises

#### 4. **Ensemble LSTM + ARIMA** - OPTIMAL ⭐⭐
- **Performance** : Combine robustesse ARIMA + précision LSTM
- **Implémentation** : Weighted average des prédictions
- **Recommandation** : Pour production finale

### 🏭 Données Démo Manufacturières

#### Sources de Données Réalistes

1. **Adventure Works Cycles Dataset** (Recommandé)
   - Entreprise manufacturière multinationale (vélos)
   - Marchés : Amérique du Nord, Europe, Asie
   - Format : SQL Server, adaptable Excel/CSV
   - Contient : ClientID, OrderDate, SalesAmount, ProductCategory

2. **French Manufacturing Companies Database**
   - 503,000 entreprises françaises (Excel format)
   - Source : companiesdata.cloud
   - Utilisation : Noms réalistes, secteurs, régions

3. **Sample B2B Sales Data Structure**
   ```
   client_id,nom_entreprise,secteur,region,date_commande,montant,delai_paiement,statut_commande
   FR001,Metalux SARL,Métallurgie,Auvergne-Rhône-Alpes,2024-01-15,15420.50,45,Payé
   FR002,PlastiForm SAS,Plastique,Nouvelle-Aquitaine,2024-01-18,8750.00,30,En cours
   ```

#### 🧮 Analyse RFM pour Classification Clients

**Implémentation Python recommandée :**
```python
# Calcul RFM
recency = (datetime.now() - client_data['derniere_commande']).dt.days
frequency = client_data.groupby('client_id')['commande_id'].count()
monetary = client_data.groupby('client_id')['montant'].mean()

# Segmentation
segments = {
    'Champions': (5,5,5),
    'Loyaux': (4,4,4),
    'Nouveaux': (5,1,1),
    'À risque': (2,3,3)
}
```

### 📈 Pipeline de Prédiction Recommandé

#### 1. **Preprocessing des Données**
```python
# Extraction Excel avec openpyxl
import pandas as pd
from openpyxl import load_workbook

def extract_sales_data(file_path):
    wb = load_workbook(file_path)
    # Auto-détection colonnes: Date, Client, Montant, Statut
    return cleaned_dataframe
```

#### 2. **Feature Engineering**
- Variables temporelles : jour_semaine, mois, trimestre
- Variables business : délai_paiement_moyen, saisonnalité_secteur
- Variables RFM : recency, frequency, monetary

#### 3. **Modèles Hybrides**
```python
# Ensemble Prophet + LSTM
prophet_pred = prophet_model.predict(dates)
lstm_pred = lstm_model.predict(sequences)
final_pred = 0.6 * lstm_pred + 0.4 * prophet_pred
```

### 🎯 Métriques Business Clés

#### Prédictions à Implémenter
1. **Cash Flow 3-6 mois** : Entrées de trésorerie prévues
2. **Probabilité de paiement** : Délais client par client
3. **Saisonnalité des ventes** : Pics/creux par secteur
4. **Score lead** : Classification RFM automatique

#### Visualisations Essentielles
- Graphique temporel avec bandes de confiance
- Heatmap délais de paiement par client
- Camembert répartition segments RFM
- Timeline cash flow prévisionnel vs réel

### 🗂️ Structure des Données Démo

#### Fichiers Excel Types à Supporter
1. **Export comptable** : Date,Référence,Client,Débit,Crédit,Libellé
2. **CRM export** : Client,Contact,Statut,Date_création,Montant_estimé
3. **Facturation** : Facture,Client,Date_émission,Échéance,Montant,Statut

#### Génération de Données Synthétiques
```python
# Générateur de données réalistes
import faker
import random
from datetime import datetime, timedelta

def generate_manufacturing_data(n_clients=100, n_transactions=1000):
    # Noms entreprises françaises réalistes
    # Montants cohérents secteur manufacturier (1K-100K€)
    # Délais paiement variables (15-90 jours)
    # Saisonnalité (baisse été, pic Q4)
    return synthetic_dataframe
```

### 🔧 Stack Technique Optimisé

#### Backend Prediction Pipeline
```python
# FastAPI + MLflow pour versioning modèles
from fastapi import FastAPI
from mlflow.pyfunc import load_model

app = FastAPI()
prophet_model = load_model("models/prophet_v1.2")
lstm_model = load_model("models/lstm_v1.0")

@app.post("/api/predict/cashflow")
async def predict_cashflow(file: UploadFile):
    # Pipeline complet : Extract → Clean → Predict → Visualize
    return {"predictions": forecast_data, "confidence": intervals}
```

#### Frontend Visualisation
```typescript
// Recharts avec données temps réel
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CashFlowChart = ({ predictions, historical }) => (
  <ResponsiveContainer width="100%" height={400}>
    <LineChart data={mergedData}>
      <Line type="monotone" dataKey="historique" stroke="#8884d8" strokeWidth={2} />
      <Line type="monotone" dataKey="prevision" stroke="#82ca9d" strokeWidth={2} strokeDasharray="5 5" />
      <Line type="monotone" dataKey="confiance_min" stroke="#ffc658" strokeWidth={1} />
      <Line type="monotone" dataKey="confiance_max" stroke="#ffc658" strokeWidth={1} />
    </LineChart>
  </ResponsiveContainer>
);
```

### 📋 Checklist Implémentation Complète

#### Phase 1 : Infrastructure (Semaine 1)
- [ ] Setup Next.js + Tailwind + TypeScript
- [ ] Setup FastAPI backend avec upload de fichiers
- [ ] Configuration Railway deployment
- [ ] Base de données (SQLite → PostgreSQL)

#### Phase 2 : ML Pipeline (Semaine 2)
- [ ] Module extraction Excel/CSV automatique
- [ ] Implémentation Prophet baseline
- [ ] Calcul RFM et segmentation clients
- [ ] API endpoints prédiction

#### Phase 3 : UX/Visualisation (Semaine 3)
- [ ] Dashboard interactif Recharts
- [ ] Export PDF/CSV des prédictions
- [ ] Intégration Slack notifications
- [ ] Tests avec données démo réalistes

#### Phase 4 : Optimisation (Bonus)
- [ ] Modèle LSTM avancé
- [ ] A/B testing Prophet vs LSTM
- [ ] Métriques business (MAPE, RMSE)
- [ ] Cache Redis pour performances

---

## 🚀 DÉMARRAGE RAPIDE

### Commandes d'Initialisation
```bash
# Frontend
npx create-next-app@latest ezbi-frontend --typescript --tailwind --app
cd ezbi-frontend && npm install recharts @hookform/resolvers zod lucide-react

# Backend
mkdir ezbi-backend && cd ezbi-backend
pip install fastapi uvicorn pandas openpyxl prophet scikit-learn
pip install python-multipart aiofiles pydantic
```

### Templates de Données Démo
Créer `demo-data/` avec :
- `manufacturing_sales_sample.xlsx` (500 lignes)
- `b2b_transactions_q4.csv` (1000 transactions)
- `client_master_data.json` (100 entreprises)

Cette structure complète permet un développement guidé avec des données réalistes et des modèles state-of-the-art.