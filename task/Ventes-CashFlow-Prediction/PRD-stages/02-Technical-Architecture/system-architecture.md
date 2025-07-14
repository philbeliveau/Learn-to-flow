# 🏗️ ARCHITECTURE SYSTÈME - EZBI ANALYTICS

## 🎯 VISION ARCHITECTURALE

### Principes Directeurs
```
🧠 Architecture Philosophy

1. AI-First Design:
├── ML Pipeline as Core Service
├── Real-time Prediction Engine
├── Continuous Learning System
└── Intelligence-Driven UX

2. Cloud-Native Scalability:
├── Microservices Architecture
├── Auto-scaling Components
├── Global CDN Distribution
└── Multi-region Deployment

3. Developer Experience:
├── API-First Approach
├── Comprehensive Documentation
├── SDK Multi-language
└── Webhook-driven Integrations

4. Security by Design:
├── Zero-trust Architecture
├── End-to-end Encryption
├── GDPR Compliance Native
└── Audit Trail Complete
```

### Architecture Overview
```
🌐 High-Level System Architecture

┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  Web App    │  Mobile App  │  API Clients │  Integrations  │
│  (Next.js)  │  (React Native) │  (REST/GraphQL) │  (Webhooks) │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   EDGE LAYER      │
                    │  (Vercel Edge)    │
                    │  - CDN Global     │
                    │  - Edge Functions │
                    │  - Rate Limiting  │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                      API GATEWAY                             │
│  (Kong/AWS API Gateway)                                      │
│  - Authentication        - Load Balancing                    │
│  - Rate Limiting         - Request Routing                   │
│  - API Versioning        - Monitoring & Analytics            │
└─────────────────────────────┬─────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌────────▼────────┐   ┌───────▼──────┐
│  WEB API     │    │   ML PIPELINE   │   │ INTEGRATION  │
│  SERVICE     │    │    SERVICE      │   │   SERVICE    │
│              │    │                 │   │              │
│ - User Mgmt  │    │ - ARIMA         │   │ - Slack API  │
│ - File Proc  │    │ - LSTM Models   │   │ - ERP Connec │
│ - Analytics  │    │ - RFM Analysis  │   │ - Bank APIs  │
│ - Reporting  │    │ - Ensemble      │   │ - Webhooks   │
└──────┬───────┘    └────────┬────────┘   └───────┬──────┘
       │                     │                    │
       └─────────────────────┼────────────────────┘
                             │
    ┌────────────────────────▼────────────────────────┐
    │                 DATA LAYER                      │
    ├─────────────────────────────────────────────────┤
    │  Primary DB     │  Time Series  │  File Storage │
    │  (PostgreSQL)   │  (InfluxDB)    │  (S3/MinIO)   │
    │                 │                │               │
    │ - Users         │ - Predictions  │ - Excel Files │
    │ - Companies     │ - Metrics      │ - Exports     │
    │ - Transactions  │ - Events       │ - Models      │
    │ - Models        │ - Logs         │ - Backups     │
    └─────────────────────────────────────────────────┘
```

---

## 🚀 FRONTEND ARCHITECTURE

### Next.js 14 Application Structure
```
📁 Frontend Architecture (Next.js 14 App Router)

ezbi-frontend/
├── app/                          # App Router (Next.js 14)
│   ├── (auth)/                   # Route Groups
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/              # Protected Routes
│   │   ├── overview/
│   │   ├── upload/
│   │   ├── predictions/
│   │   ├── clients/
│   │   └── settings/
│   ├── api/                      # API Routes
│   │   ├── auth/
│   │   ├── upload/
│   │   └── webhooks/
│   ├── globals.css
│   ├── layout.tsx                # Root Layout
│   ├── loading.tsx               # Global Loading UI
│   ├── error.tsx                 # Global Error UI
│   └── not-found.tsx             # 404 Page
├── components/                   # Reusable Components
│   ├── ui/                       # Base UI Components (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── charts/                   # Chart Components
│   │   ├── PredictionChart.tsx
│   │   ├── CashFlowTimeline.tsx
│   │   ├── RFMHeatmap.tsx
│   │   └── ConfidenceIndicator.tsx
│   ├── upload/                   # File Upload Components
│   │   ├── SmartUploadZone.tsx
│   │   ├── FilePreview.tsx
│   │   └── ProcessingStatus.tsx
│   └── dashboard/                # Dashboard Components
│       ├── DashboardShell.tsx
│       ├── MetricCard.tsx
│       └── PredictionCard.tsx
├── lib/                          # Utility Libraries
│   ├── auth.ts                   # Authentication Logic
│   ├── api.ts                    # API Client
│   ├── utils.ts                  # General Utilities
│   ├── validations.ts            # Zod Schemas
│   └── constants.ts              # App Constants
├── hooks/                        # Custom React Hooks
│   ├── useAuth.ts
│   ├── usePredictions.ts
│   ├── useUpload.ts
│   └── useRealtime.ts
├── types/                        # TypeScript Definitions
│   ├── auth.ts
│   ├── api.ts
│   ├── predictions.ts
│   └── uploads.ts
├── stores/                       # State Management (Zustand)
│   ├── authStore.ts
│   ├── uploadStore.ts
│   └── dashboardStore.ts
└── config/                       # Configuration
    ├── database.ts
    ├── env.ts
    └── constants.ts
```

### State Management Strategy
```typescript
// 🗄️ State Architecture with Zustand

// Global State Stores
interface AuthStore {
  user: User | null;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

interface DashboardStore {
  currentCompany: Company | null;
  predictions: Prediction[];
  metrics: DashboardMetrics;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  loadDashboard: () => Promise<void>;
  refreshPredictions: () => Promise<void>;
  updateTimeRange: (range: TimeRange) => void;
}

interface UploadStore {
  files: UploadFile[];
  currentUpload: UploadFile | null;
  processingStatus: ProcessingStatus;
  
  // Actions
  addFile: (file: File) => void;
  removeFile: (id: string) => void;
  processFile: (id: string) => Promise<void>;
  clearCompleted: () => void;
}

// Component-Level State
interface PredictionChartState {
  timeRange: TimeRange;
  selectedScenario: Scenario;
  showConfidence: boolean;
  chartType: 'line' | 'area' | 'bar';
}
```

### Component Architecture Patterns
```typescript
// 🧩 Component Design Patterns

// 1. Container/Presenter Pattern
// Container (Smart Component)
export function DashboardContainer() {
  const { data, loading, error } = useDashboardData();
  const { predictions } = usePredictions();
  
  if (loading) return <DashboardSkeleton />;
  if (error) return <ErrorBoundary error={error} />;
  
  return <DashboardPresenter data={data} predictions={predictions} />;
}

// Presenter (Dumb Component)
interface DashboardPresenterProps {
  data: DashboardData;
  predictions: Prediction[];
}

export function DashboardPresenter({ data, predictions }: DashboardPresenterProps) {
  return (
    <div className="dashboard-grid">
      <MetricsOverview metrics={data.metrics} />
      <PredictionChart predictions={predictions} />
      <ClientSegments segments={data.segments} />
    </div>
  );
}

// 2. Compound Component Pattern (Charts)
export function PredictionChart({ data }: PredictionChartProps) {
  return (
    <Chart data={data}>
      <Chart.Header>
        <Chart.Title>Cash Flow Predictions</Chart.Title>
        <Chart.Controls />
      </Chart.Header>
      <Chart.Canvas>
        <Chart.Line dataKey="historical" stroke="#8884d8" />
        <Chart.Line dataKey="predicted" stroke="#82ca9d" strokeDasharray="5 5" />
        <Chart.ConfidenceBand dataKey="confidence" fill="#82ca9d" opacity={0.2} />
      </Chart.Canvas>
      <Chart.Legend />
    </Chart>
  );
}

// 3. Hook-based Data Fetching
export function usePredictions(companyId: string, timeRange: TimeRange) {
  return useSWR(
    ['predictions', companyId, timeRange],
    () => api.predictions.get(companyId, timeRange),
    {
      refreshInterval: 30000, // Refresh every 30s
      revalidateOnFocus: true,
      errorRetryCount: 3,
    }
  );
}
```

---

## ⚙️ BACKEND ARCHITECTURE

### FastAPI Microservices Structure
```
🏗️ Backend Services Architecture

ezbi-backend/
├── services/
│   ├── api-gateway/              # Main API Gateway
│   │   ├── main.py
│   │   ├── middleware/
│   │   ├── routers/
│   │   └── dependencies/
│   ├── ml-service/               # ML Pipeline Service
│   │   ├── models/
│   │   │   ├── prophet_model.py
│   │   │   ├── lstm_model.py
│   │   │   └── ensemble_model.py
│   │   ├── preprocessing/
│   │   ├── training/
│   │   └── inference/
│   ├── data-service/             # Data Processing Service
│   │   ├── extractors/
│   │   │   ├── excel_extractor.py
│   │   │   ├── csv_extractor.py
│   │   │   └── pdf_extractor.py
│   │   ├── validators/
│   │   ├── transformers/
│   │   └── loaders/
│   ├── user-service/             # User Management
│   │   ├── auth/
│   │   ├── models/
│   │   └── crud/
│   └── integration-service/      # External Integrations
│       ├── slack/
│       ├── webhooks/
│       └── erp/
├── shared/                       # Shared Libraries
│   ├── database/
│   ├── security/
│   ├── utils/
│   └── schemas/
├── infrastructure/               # Infrastructure as Code
│   ├── docker/
│   ├── kubernetes/
│   └── terraform/
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

### API Design Patterns
```python
# 🔌 RESTful API Design

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio

# API Versioning
router = APIRouter(prefix="/api/v1", tags=["predictions"])

# Request/Response Models
class PredictionRequest(BaseModel):
    company_id: str
    time_horizon: int = 90  # days
    scenario: str = "realistic"
    confidence_level: float = 0.95
    
class PredictionResponse(BaseModel):
    prediction_id: str
    cash_flow_forecast: List[CashFlowPoint]
    confidence_intervals: List[ConfidenceInterval]
    insights: List[BusinessInsight]
    accuracy_score: float
    generated_at: datetime

# Async Endpoint with Dependencies
@router.post("/predictions", response_model=PredictionResponse)
async def create_prediction(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    ml_service: MLService = Depends(get_ml_service),
    db: AsyncSession = Depends(get_db)
):
    # Input validation
    await validate_company_access(current_user.id, request.company_id, db)
    
    # Async ML prediction
    prediction_task = await ml_service.predict_async(
        company_id=request.company_id,
        horizon=request.time_horizon,
        scenario=request.scenario
    )
    
    # Store prediction
    prediction = await db_predictions.create(
        db=db,
        prediction_data=prediction_task.result,
        user_id=current_user.id
    )
    
    # Background tasks
    background_tasks.add_task(
        send_prediction_notification,
        user_id=current_user.id,
        prediction_id=prediction.id
    )
    
    return PredictionResponse.from_orm(prediction)

# WebSocket for Real-time Updates
@router.websocket("/predictions/{prediction_id}/status")
async def prediction_status_websocket(
    websocket: WebSocket,
    prediction_id: str,
    current_user: User = Depends(get_current_user_ws)
):
    await websocket.accept()
    
    async for status_update in ml_service.get_prediction_stream(prediction_id):
        await websocket.send_json({
            "type": "status_update",
            "data": status_update.dict()
        })
```

### Database Architecture
```sql
-- 🗄️ PostgreSQL Database Schema

-- Core Business Entities
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    industry_sector VARCHAR(100),
    employee_count INTEGER,
    annual_revenue DECIMAL(15, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    company_id UUID REFERENCES companies(id),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transaction Data
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    client_name VARCHAR(255),
    amount DECIMAL(12, 2) NOT NULL,
    transaction_date DATE NOT NULL,
    payment_date DATE,
    status VARCHAR(50) DEFAULT 'pending',
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ML Predictions
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    user_id UUID REFERENCES users(id),
    model_type VARCHAR(50) NOT NULL,
    input_data JSONB NOT NULL,
    prediction_result JSONB NOT NULL,
    confidence_score DECIMAL(3, 2),
    time_horizon INTEGER, -- days
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- File Uploads
CREATE TABLE file_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    user_id UUID REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    processing_status VARCHAR(50) DEFAULT 'pending',
    extracted_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RFM Analysis Results
CREATE TABLE client_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    client_name VARCHAR(255) NOT NULL,
    recency_score INTEGER CHECK (recency_score BETWEEN 1 AND 5),
    frequency_score INTEGER CHECK (frequency_score BETWEEN 1 AND 5),
    monetary_score INTEGER CHECK (monetary_score BETWEEN 1 AND 5),
    segment_label VARCHAR(50),
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX idx_transactions_company_date ON transactions(company_id, transaction_date);
CREATE INDEX idx_predictions_company_created ON predictions(company_id, created_at);
CREATE INDEX idx_client_segments_company ON client_segments(company_id);
CREATE INDEX idx_file_uploads_status ON file_uploads(processing_status);

-- Time Series Extension for InfluxDB Integration
CREATE EXTENSION IF NOT EXISTS timescaledb;
SELECT create_hypertable('predictions', 'created_at');
```

---

## 🤖 ML PIPELINE ARCHITECTURE

### ML Service Infrastructure
```python
# 🧠 ML Pipeline Architecture

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import asyncio
from prophet import Prophet
import numpy as np
import pandas as pd

# Base ML Model Interface
class BasePredictor(ABC):
    """Abstract base class for all prediction models"""
    
    @abstractmethod
    async def train(self, data: pd.DataFrame) -> Dict:
        pass
    
    @abstractmethod
    async def predict(self, data: pd.DataFrame, horizon: int) -> Dict:
        pass
    
    @abstractmethod
    def get_feature_importance(self) -> Dict:
        pass

# Prophet Implementation
class ProphetPredictor(BasePredictor):
    def __init__(self, seasonality_mode: str = 'multiplicative'):
        self.model = Prophet(
            seasonality_mode=seasonality_mode,
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        self.is_trained = False
    
    async def train(self, data: pd.DataFrame) -> Dict:
        # Prepare data for Prophet
        prophet_data = data.rename(columns={
            'transaction_date': 'ds',
            'amount': 'y'
        })
        
        # Add custom seasonalities for manufacturing
        self.model.add_seasonality(
            name='quarterly',
            period=91.25,
            fourier_order=8
        )
        
        # Async training
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.model.fit, prophet_data)
        
        self.is_trained = True
        return {"status": "trained", "model_type": "prophet"}
    
    async def predict(self, data: pd.DataFrame, horizon: int) -> Dict:
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=horizon)
        
        # Generate predictions
        loop = asyncio.get_event_loop()
        forecast = await loop.run_in_executor(None, self.model.predict, future)
        
        return {
            "predictions": forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict('records'),
            "components": self.model.predict(future)[['ds', 'trend', 'seasonal']].to_dict('records'),
            "model_type": "prophet"
        }

# LSTM Implementation
class LSTMPredictor(BasePredictor):
    def __init__(self, sequence_length: int = 30, hidden_size: int = 128):
        import torch
        import torch.nn as nn
        
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.model = None
        self.scaler = None
        self.is_trained = False
    
    def build_model(self, input_size: int):
        import torch.nn as nn
        
        class LSTMModel(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers=2):
                super(LSTMModel, self).__init__()
                self.hidden_size = hidden_size
                self.num_layers = num_layers
                
                self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
                self.fc = nn.Linear(hidden_size, 1)
                self.dropout = nn.Dropout(0.2)
            
            def forward(self, x):
                h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
                c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
                
                out, _ = self.lstm(x, (h0, c0))
                out = self.dropout(out[:, -1, :])
                out = self.fc(out)
                return out
        
        return LSTMModel(input_size, self.hidden_size)
    
    async def train(self, data: pd.DataFrame) -> Dict:
        from sklearn.preprocessing import MinMaxScaler
        import torch
        import torch.nn as nn
        
        # Feature engineering
        features = self.create_features(data)
        
        # Scale data
        self.scaler = MinMaxScaler()
        scaled_data = self.scaler.fit_transform(features)
        
        # Create sequences
        X, y = self.create_sequences(scaled_data)
        
        # Build and train model
        self.model = self.build_model(X.shape[2])
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        # Training loop
        for epoch in range(100):
            self.model.train()
            optimizer.zero_grad()
            
            outputs = self.model(torch.FloatTensor(X))
            loss = criterion(outputs, torch.FloatTensor(y))
            
            loss.backward()
            optimizer.step()
        
        self.is_trained = True
        return {"status": "trained", "model_type": "lstm", "final_loss": loss.item()}

# Ensemble Model
class EnsemblePredictor(BasePredictor):
    def __init__(self, models: List[BasePredictor], weights: Optional[List[float]] = None):
        self.models = models
        self.weights = weights or [1.0 / len(models)] * len(models)
        
    async def train(self, data: pd.DataFrame) -> Dict:
        # Train all models in parallel
        training_tasks = [model.train(data) for model in self.models]
        results = await asyncio.gather(*training_tasks)
        
        return {
            "status": "trained",
            "model_type": "ensemble",
            "individual_results": results
        }
    
    async def predict(self, data: pd.DataFrame, horizon: int) -> Dict:
        # Get predictions from all models
        prediction_tasks = [model.predict(data, horizon) for model in self.models]
        predictions = await asyncio.gather(*prediction_tasks)
        
        # Weighted ensemble
        ensemble_prediction = self.combine_predictions(predictions)
        
        return {
            "predictions": ensemble_prediction,
            "individual_predictions": predictions,
            "model_type": "ensemble",
            "weights_used": self.weights
        }

# ML Service Orchestrator
class MLService:
    def __init__(self):
        self.models = {
            "prophet": ProphetPredictor(),
            "lstm": LSTMPredictor(),
            "ensemble": EnsemblePredictor([
                ProphetPredictor(),
                LSTMPredictor()
            ])
        }
        self.model_registry = {}
    
    async def train_model(self, company_id: str, model_type: str, data: pd.DataFrame):
        model = self.models[model_type]
        result = await model.train(data)
        
        # Save trained model
        self.model_registry[f"{company_id}_{model_type}"] = model
        
        return result
    
    async def predict_async(self, company_id: str, horizon: int, scenario: str = "realistic"):
        # Get best model for company
        model_key = f"{company_id}_ensemble"
        if model_key not in self.model_registry:
            raise ValueError(f"No trained model found for company {company_id}")
        
        model = self.model_registry[model_key]
        
        # Load historical data
        historical_data = await self.load_company_data(company_id)
        
        # Generate prediction
        prediction = await model.predict(historical_data, horizon)
        
        # Apply scenario adjustments
        adjusted_prediction = self.apply_scenario(prediction, scenario)
        
        return adjusted_prediction
```

---

## 🔄 INTEGRATION ARCHITECTURE

### External Services Integration
```python
# 🔗 Integration Layer Architecture

from abc import ABC, abstractmethod
import httpx
import asyncio
from typing import Dict, Any, Optional

# Base Integration Interface
class BaseIntegration(ABC):
    @abstractmethod
    async def authenticate(self) -> bool:
        pass
    
    @abstractmethod
    async def sync_data(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def send_notification(self, message: str) -> bool:
        pass

# Slack Integration
class SlackIntegration(BaseIntegration):
    def __init__(self, webhook_url: str, bot_token: str):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.client = httpx.AsyncClient()
    
    async def authenticate(self) -> bool:
        try:
            response = await self.client.post(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {self.bot_token}"}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def send_prediction_alert(self, prediction_data: Dict):
        """Send AI prediction results to Slack"""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🧠 Nouvelle Prédiction EZBI"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Cash Flow Prévu:* €{prediction_data['amount']:,.2f}"},
                    {"type": "mrkdwn", "text": f"*Confiance:* {prediction_data['confidence']*100:.1f}%"},
                    {"type": "mrkdwn", "text": f"*Horizon:* {prediction_data['horizon']} jours"},
                    {"type": "mrkdwn", "text": f"*Tendance:* {prediction_data['trend']}"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Insights:* {prediction_data['insights']}"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Voir Dashboard"},
                        "url": f"https://app.ezbi.fr/predictions/{prediction_data['id']}"
                    }
                ]
            }
        ]
        
        await self.client.post(self.webhook_url, json={"blocks": blocks})

# ERP Integration Base
class ERPIntegration(BaseIntegration):
    def __init__(self, erp_type: str, api_endpoint: str, credentials: Dict):
        self.erp_type = erp_type
        self.api_endpoint = api_endpoint
        self.credentials = credentials
        self.client = httpx.AsyncClient()
    
    async def sync_transactions(self) -> List[Dict]:
        """Sync transaction data from ERP"""
        if self.erp_type == "sage":
            return await self._sync_sage_transactions()
        elif self.erp_type == "odoo":
            return await self._sync_odoo_transactions()
        else:
            raise ValueError(f"Unsupported ERP type: {self.erp_type}")
    
    async def _sync_sage_transactions(self) -> List[Dict]:
        # Sage X3 API integration
        auth_response = await self.client.post(
            f"{self.api_endpoint}/auth",
            json=self.credentials
        )
        token = auth_response.json()["access_token"]
        
        # Fetch transactions
        response = await self.client.get(
            f"{self.api_endpoint}/transactions",
            headers={"Authorization": f"Bearer {token}"},
            params={"date_from": "2024-01-01", "limit": 1000}
        )
        
        return response.json()["transactions"]

# Webhook Handler
class WebhookService:
    def __init__(self):
        self.handlers = {}
    
    def register_handler(self, event_type: str, handler_func):
        self.handlers[event_type] = handler_func
    
    async def process_webhook(self, event_type: str, payload: Dict):
        if event_type in self.handlers:
            await self.handlers[event_type](payload)
    
    async def handle_prediction_complete(self, payload: Dict):
        """Handle ML prediction completion"""
        prediction_id = payload["prediction_id"]
        company_id = payload["company_id"]
        
        # Send Slack notification
        slack = SlackIntegration(
            webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            bot_token=os.getenv("SLACK_BOT_TOKEN")
        )
        await slack.send_prediction_alert(payload["prediction_data"])
        
        # Update dashboard in real-time
        await self.broadcast_to_dashboard(company_id, {
            "type": "prediction_update",
            "data": payload["prediction_data"]
        })
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

### Cloud Infrastructure
```yaml
# 🌥️ Kubernetes Deployment Configuration

# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: ezbi-production

---
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: ezbi-config
  namespace: ezbi-production
data:
  DATABASE_URL: "postgresql://ezbi:password@postgres:5432/ezbi"
  REDIS_URL: "redis://redis:6379"
  ML_MODEL_PATH: "/app/models"
  LOG_LEVEL: "INFO"

---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: ezbi-secrets
  namespace: ezbi-production
type: Opaque
data:
  jwt-secret: <base64-encoded-secret>
  slack-webhook: <base64-encoded-webhook>
  openai-api-key: <base64-encoded-key>

---
# API Gateway Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: ezbi-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: ezbi/api-gateway:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: ezbi-config
              key: DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: ezbi-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# ML Service Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-service
  namespace: ezbi-production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ml-service
  template:
    metadata:
      labels:
        app: ml-service
    spec:
      containers:
      - name: ml-service
        image: ezbi/ml-service:v1.0.0
        ports:
        - containerPort: 8001
        env:
        - name: MODEL_PATH
          valueFrom:
            configMapKeyRef:
              name: ezbi-config
              key: ML_MODEL_PATH
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
            nvidia.com/gpu: 0
          limits:
            memory: "2Gi"
            cpu: "1000m"
            nvidia.com/gpu: 1
        volumeMounts:
        - name: model-storage
          mountPath: /app/models
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: ml-models-pvc

---
# Load Balancer Service
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
  namespace: ezbi-production
spec:
  selector:
    app: api-gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: ezbi-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Infrastructure as Code (Terraform)
```hcl
# 🏗️ Terraform Infrastructure

# Provider Configuration
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "ezbi-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
  
  tags = {
    Environment = var.environment
    Project     = "ezbi-analytics"
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "ezbi-${var.environment}"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  # Node Groups
  eks_managed_node_groups = {
    general = {
      min_size     = 2
      max_size     = 10
      desired_size = 3
      
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
    
    ml_nodes = {
      min_size     = 0
      max_size     = 5
      desired_size = 1
      
      instance_types = ["g4dn.xlarge"]  # GPU instances for ML
      capacity_type  = "SPOT"
      
      taints = {
        dedicated = {
          key    = "ml-workload"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }
  
  tags = {
    Environment = var.environment
    Project     = "ezbi-analytics"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier = "ezbi-${var.environment}"
  
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_encrypted     = true
  
  db_name  = "ezbi"
  username = "ezbi"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = var.environment == "production"
  
  tags = {
    Environment = var.environment
    Project     = "ezbi-analytics"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "ezbi-${var.environment}"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "ezbi-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
  
  tags = {
    Environment = var.environment
    Project     = "ezbi-analytics"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "file_storage" {
  bucket = "ezbi-${var.environment}-files"
  
  tags = {
    Environment = var.environment
    Project     = "ezbi-analytics"
  }
}

resource "aws_s3_bucket" "ml_models" {
  bucket = "ezbi-${var.environment}-models"
  
  tags = {
    Environment = var.environment
    Project     = "ezbi-analytics"
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name = aws_s3_bucket.file_storage.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.file_storage.bucket}"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }
  
  enabled = true
  
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.file_storage.bucket}"
    compress              = true
    viewer_protocol_policy = "redirect-to-https"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = true
  }
  
  tags = {
    Environment = var.environment
    Project     = "ezbi-analytics"
  }
}
```

Cette architecture système complète assure une scalabilité, une sécurité et une performance optimales pour EZBI Analytics, avec une séparation claire des responsabilités et une infrastructure cloud-native moderne.