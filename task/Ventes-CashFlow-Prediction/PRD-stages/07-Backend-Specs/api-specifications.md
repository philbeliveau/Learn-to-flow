# 🔧 SPÉCIFICATIONS BACKEND API - EZBI ANALYTICS

## 🎯 ARCHITECTURE BACKEND

### FastAPI Application Structure
```
📁 Backend Architecture Complète

ezbi-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                   # Application FastAPI principale
│   ├── config.py                 # Configuration et settings
│   ├── dependencies.py           # Dépendances globales
│   │
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py          # JWT, authentification
│   │   ├── database.py          # Database connections
│   │   ├── cache.py             # Redis cache
│   │   ├── logging.py           # Logging configuration
│   │   └── exceptions.py        # Custom exceptions
│   │
│   ├── models/                   # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py              # Base model
│   │   ├── user.py              # User models
│   │   ├── company.py           # Company models
│   │   ├── transaction.py       # Transaction models
│   │   ├── prediction.py        # Prediction models
│   │   └── ml_model.py          # ML model metadata
│   │
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication schemas
│   │   ├── user.py              # User schemas
│   │   ├── company.py           # Company schemas
│   │   ├── transaction.py       # Transaction schemas
│   │   ├── prediction.py        # Prediction schemas
│   │   └── common.py            # Common schemas
│   │
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   ├── deps.py              # API dependencies
│   │   ├── auth.py              # Authentication routes
│   │   ├── users.py             # User management
│   │   ├── companies.py         # Company management
│   │   ├── transactions.py      # Transaction management
│   │   ├── predictions.py       # Prediction routes
│   │   ├── upload.py            # File upload
│   │   ├── analytics.py         # Analytics routes
│   │   └── webhooks.py          # Webhook endpoints
│   │
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication service
│   │   ├── user_service.py      # User management
│   │   ├── company_service.py   # Company management
│   │   ├── transaction_service.py # Transaction processing
│   │   ├── prediction_service.py # Prediction logic
│   │   ├── upload_service.py    # File processing
│   │   ├── analytics_service.py # Analytics computation
│   │   └── notification_service.py # Notifications
│   │
│   ├── ml/                       # Machine Learning
│   │   ├── __init__.py
│   │   ├── models/              # ML model implementations
│   │   │   ├── prophet_model.py
│   │   │   ├── lstm_model.py
│   │   │   └── ensemble_model.py
│   │   ├── features/            # Feature engineering
│   │   │   ├── __init__.py
│   │   │   ├── base_features.py
│   │   │   ├── time_features.py
│   │   │   └── manufacturing_features.py
│   │   ├── training/            # Model training
│   │   │   ├── __init__.py
│   │   │   ├── trainer.py
│   │   │   └── evaluator.py
│   │   └── inference/           # Model inference
│   │       ├── __init__.py
│   │       ├── predictor.py
│   │       └── model_loader.py
│   │
│   ├── utils/                    # Utilities
│   │   ├── __init__.py
│   │   ├── data_validation.py   # Data validation
│   │   ├── file_processing.py   # File processing
│   │   ├── email.py             # Email utilities
│   │   ├── export.py            # Export utilities
│   │   └── helpers.py           # Helper functions
│   │
│   └── tests/                    # Tests
│       ├── __init__.py
│       ├── conftest.py          # Test configuration
│       ├── test_auth.py         # Authentication tests
│       ├── test_predictions.py  # Prediction tests
│       ├── test_ml_models.py    # ML model tests
│       └── test_services.py     # Service tests
│
├── migrations/                   # Database migrations
├── requirements.txt              # Dependencies
├── requirements-dev.txt          # Development dependencies
├── Dockerfile                    # Docker configuration
├── docker-compose.yml           # Docker compose
└── .env.example                 # Environment variables
```

---

## 🔐 AUTHENTIFICATION & SÉCURITÉ

### JWT Authentication System
```python
# 🔐 core/security.py - Système d'authentification JWT

from datetime import datetime, timedelta
from typing import Optional, Union
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

class JWTConfig:
    SECRET_KEY = "your-secret-key-here"  # À définir en environnement
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 30

class TokenData(BaseModel):
    user_id: str
    email: str
    company_id: str
    role: str
    permissions: list[str]

class SecurityService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifier un mot de passe"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hasher un mot de passe"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Créer un token d'accès JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(to_encode, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)
    
    def create_refresh_token(self, data: dict) -> str:
        """Créer un refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=JWTConfig.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)
    
    def verify_token(self, token: str) -> TokenData:
        """Vérifier et décoder un token JWT"""
        try:
            payload = jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM])
            
            user_id = payload.get("sub")
            email = payload.get("email")
            company_id = payload.get("company_id")
            role = payload.get("role")
            permissions = payload.get("permissions", [])
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(
                user_id=user_id,
                email=email,
                company_id=company_id,
                role=role,
                permissions=permissions
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expiré",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Dependency pour l'authentification
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    security_service = SecurityService()
    token_data = security_service.verify_token(credentials.credentials)
    return token_data
```

### API Authentication Routes
```python
# 🔐 api/auth.py - Routes d'authentification

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import SecurityService
from app.schemas.auth import TokenResponse, LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Connexion utilisateur"""
    auth_service = AuthService(db)
    
    try:
        result = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type="bearer",
            user=result["user"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

@router.post("/register", response_model=TokenResponse)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Inscription utilisateur"""
    auth_service = AuthService(db)
    
    try:
        result = await auth_service.register_user(
            name=register_data.name,
            email=register_data.email,
            password=register_data.password,
            company_name=register_data.company_name,
            company_size=register_data.company_size
        )
        
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type="bearer",
            user=result["user"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Rafraîchir le token d'accès"""
    auth_service = AuthService(db)
    
    try:
        result = await auth_service.refresh_access_token(refresh_token)
        
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type="bearer",
            user=result["user"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide"
        )

@router.post("/logout")
async def logout(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Déconnexion utilisateur"""
    auth_service = AuthService(db)
    
    await auth_service.logout_user(current_user.user_id)
    
    return {"message": "Déconnexion réussie"}

@router.get("/verify")
async def verify_token(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vérifier la validité du token"""
    auth_service = AuthService(db)
    
    user = await auth_service.get_user_by_id(current_user.user_id)
    
    return {"user": user, "valid": True}
```

---

## 🔮 API PRÉDICTIONS

### Prediction Service
```python
# 🔮 services/prediction_service.py - Service de prédictions

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.prediction import Prediction
from app.models.transaction import Transaction
from app.ml.inference.predictor import PredictionEngine
from app.schemas.prediction import PredictionRequest, PredictionResponse
import asyncio

class PredictionService:
    def __init__(self, db: Session):
        self.db = db
        self.prediction_engine = PredictionEngine()
    
    async def create_prediction(
        self,
        company_id: str,
        prediction_request: PredictionRequest
    ) -> PredictionResponse:
        """Créer une nouvelle prédiction"""
        
        # 1. Récupérer les données historiques
        historical_data = await self._get_historical_data(
            company_id=company_id,
            lookback_days=prediction_request.lookback_days or 365
        )
        
        if len(historical_data) < 30:
            raise ValueError("Données insuffisantes pour la prédiction (minimum 30 jours)")
        
        # 2. Générer les prédictions
        prediction_results = await self.prediction_engine.predict(
            data=historical_data,
            horizon_days=prediction_request.horizon_days,
            model_type=prediction_request.model_type,
            confidence_level=prediction_request.confidence_level
        )
        
        # 3. Sauvegarder les prédictions
        predictions = []
        for result in prediction_results:
            prediction = Prediction(
                company_id=company_id,
                target_date=result["date"],
                predicted_value=result["value"],
                confidence_score=result["confidence"],
                confidence_interval_lower=result["interval_lower"],
                confidence_interval_upper=result["interval_upper"],
                model_type=prediction_request.model_type,
                model_version=self.prediction_engine.get_model_version(prediction_request.model_type),
                features_used=result["features"],
                metadata={
                    "horizon_days": prediction_request.horizon_days,
                    "lookback_days": prediction_request.lookback_days,
                    "request_timestamp": datetime.utcnow().isoformat()
                }
            )
            self.db.add(prediction)
            predictions.append(prediction)
        
        self.db.commit()
        
        # 4. Calculer les métriques
        metrics = await self._calculate_prediction_metrics(predictions)
        
        return PredictionResponse(
            predictions=predictions,
            model_type=prediction_request.model_type,
            confidence_level=prediction_request.confidence_level,
            metrics=metrics,
            generated_at=datetime.utcnow()
        )
    
    async def get_predictions(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_type: Optional[str] = None
    ) -> List[Prediction]:
        """Récupérer les prédictions existantes"""
        
        query = self.db.query(Prediction).filter(
            Prediction.company_id == company_id
        )
        
        if start_date:
            query = query.filter(Prediction.target_date >= start_date)
        
        if end_date:
            query = query.filter(Prediction.target_date <= end_date)
        
        if model_type:
            query = query.filter(Prediction.model_type == model_type)
        
        return query.order_by(Prediction.target_date.asc()).all()
    
    async def evaluate_prediction_accuracy(
        self,
        company_id: str,
        prediction_id: str
    ) -> Dict:
        """Évaluer la précision d'une prédiction"""
        
        prediction = self.db.query(Prediction).filter(
            Prediction.id == prediction_id,
            Prediction.company_id == company_id
        ).first()
        
        if not prediction:
            raise ValueError("Prédiction non trouvée")
        
        # Récupérer la valeur réelle
        actual_value = await self._get_actual_value(
            company_id=company_id,
            date=prediction.target_date
        )
        
        if actual_value is None:
            return {"status": "pending", "message": "Données réelles non disponibles"}
        
        # Calculer la précision
        accuracy_metrics = self._calculate_accuracy_metrics(
            predicted=prediction.predicted_value,
            actual=actual_value,
            confidence_lower=prediction.confidence_interval_lower,
            confidence_upper=prediction.confidence_interval_upper
        )
        
        # Mettre à jour la prédiction
        prediction.actual_value = actual_value
        prediction.prediction_accuracy = accuracy_metrics["mape"]
        self.db.commit()
        
        return accuracy_metrics
    
    async def _get_historical_data(
        self,
        company_id: str,
        lookback_days: int
    ) -> List[Dict]:
        """Récupérer les données historiques"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        transactions = self.db.query(Transaction).filter(
            Transaction.company_id == company_id,
            Transaction.transaction_date >= cutoff_date
        ).order_by(Transaction.transaction_date.asc()).all()
        
        # Agréger par jour
        daily_data = {}
        for transaction in transactions:
            date_key = transaction.transaction_date.strftime("%Y-%m-%d")
            
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "date": transaction.transaction_date,
                    "total_amount": 0,
                    "sales": 0,
                    "purchases": 0,
                    "expenses": 0,
                    "transaction_count": 0
                }
            
            daily_data[date_key]["total_amount"] += transaction.amount
            daily_data[date_key]["transaction_count"] += 1
            
            if transaction.type == "sale":
                daily_data[date_key]["sales"] += transaction.amount
            elif transaction.type == "purchase":
                daily_data[date_key]["purchases"] += transaction.amount
            elif transaction.type == "expense":
                daily_data[date_key]["expenses"] += transaction.amount
        
        return list(daily_data.values())
    
    async def _get_actual_value(
        self,
        company_id: str,
        date: datetime
    ) -> Optional[float]:
        """Récupérer la valeur réelle pour une date donnée"""
        
        transactions = self.db.query(Transaction).filter(
            Transaction.company_id == company_id,
            Transaction.transaction_date == date.date()
        ).all()
        
        if not transactions:
            return None
        
        return sum(t.amount for t in transactions)
    
    def _calculate_accuracy_metrics(
        self,
        predicted: float,
        actual: float,
        confidence_lower: float,
        confidence_upper: float
    ) -> Dict:
        """Calculer les métriques de précision"""
        
        # Mean Absolute Percentage Error
        mape = abs(predicted - actual) / abs(actual) if actual != 0 else 0
        
        # Absolute Error
        mae = abs(predicted - actual)
        
        # Confidence interval hit
        confidence_hit = confidence_lower <= actual <= confidence_upper
        
        # Relative error
        relative_error = (predicted - actual) / actual if actual != 0 else 0
        
        return {
            "mape": mape,
            "mae": mae,
            "relative_error": relative_error,
            "confidence_hit": confidence_hit,
            "predicted": predicted,
            "actual": actual,
            "confidence_interval": [confidence_lower, confidence_upper]
        }
```

### Prediction API Routes
```python
# 🔮 api/predictions.py - Routes de prédiction

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.schemas.prediction import (
    PredictionRequest, PredictionResponse, PredictionListResponse
)
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.post("/", response_model=PredictionResponse)
async def create_prediction(
    request: PredictionRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle prédiction"""
    
    prediction_service = PredictionService(db)
    
    try:
        result = await prediction_service.create_prediction(
            company_id=current_user.company_id,
            prediction_request=request
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération de la prédiction"
        )

@router.get("/", response_model=PredictionListResponse)
async def get_predictions(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    model_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer les prédictions"""
    
    prediction_service = PredictionService(db)
    
    predictions = await prediction_service.get_predictions(
        company_id=current_user.company_id,
        start_date=start_date,
        end_date=end_date,
        model_type=model_type
    )
    
    # Pagination
    total = len(predictions)
    predictions = predictions[offset:offset+limit]
    
    return PredictionListResponse(
        predictions=predictions,
        total=total,
        offset=offset,
        limit=limit
    )

@router.get("/{prediction_id}")
async def get_prediction(
    prediction_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer une prédiction spécifique"""
    
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.company_id == current_user.company_id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prédiction non trouvée"
        )
    
    return prediction

@router.post("/{prediction_id}/evaluate")
async def evaluate_prediction(
    prediction_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Évaluer la précision d'une prédiction"""
    
    prediction_service = PredictionService(db)
    
    try:
        result = await prediction_service.evaluate_prediction_accuracy(
            company_id=current_user.company_id,
            prediction_id=prediction_id
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/models/available")
async def get_available_models(
    current_user: TokenData = Depends(get_current_user)
):
    """Récupérer les modèles disponibles"""
    
    models = [
        {
            "name": "prophet",
            "display_name": "Prophet",
            "description": "Modèle de prédiction temporelle de Facebook, optimisé pour les données business",
            "suitable_for": ["seasonal_data", "trend_analysis"],
            "min_data_points": 30,
            "max_horizon_days": 365
        },
        {
            "name": "lstm",
            "display_name": "LSTM",
            "description": "Réseau de neurones LSTM avec mécanisme d'attention",
            "suitable_for": ["complex_patterns", "short_term_predictions"],
            "min_data_points": 100,
            "max_horizon_days": 90
        },
        {
            "name": "ensemble",
            "display_name": "Ensemble",
            "description": "Combinaison intelligente de Prophet et LSTM",
            "suitable_for": ["high_accuracy", "robust_predictions"],
            "min_data_points": 100,
            "max_horizon_days": 365
        }
    ]
    
    return {"models": models}
```

---

## 📊 API ANALYTICS

### Analytics Service
```python
# 📊 services/analytics_service.py - Service d'analytics

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.transaction import Transaction
from app.models.prediction import Prediction
from app.schemas.analytics import AnalyticsResponse, KPIResponse

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_dashboard_analytics(
        self,
        company_id: str,
        period: str = "30d"
    ) -> AnalyticsResponse:
        """Récupérer les analytics du dashboard"""
        
        # Calculer les dates
        days = self._parse_period(period)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # KPIs principaux
        kpis = await self._calculate_kpis(company_id, start_date)
        
        # Tendances
        trends = await self._calculate_trends(company_id, start_date)
        
        # Répartition par catégorie
        categories = await self._calculate_category_breakdown(company_id, start_date)
        
        # Prédictions récentes
        recent_predictions = await self._get_recent_predictions(company_id)
        
        return AnalyticsResponse(
            kpis=kpis,
            trends=trends,
            categories=categories,
            recent_predictions=recent_predictions,
            period=period,
            generated_at=datetime.utcnow()
        )
    
    async def _calculate_kpis(
        self,
        company_id: str,
        start_date: datetime
    ) -> List[KPIResponse]:
        """Calculer les KPIs principaux"""
        
        # Chiffre d'affaires
        sales_query = self.db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.company_id == company_id,
            Transaction.type == "sale",
            Transaction.transaction_date >= start_date
        ).scalar() or 0
        
        # Dépenses
        expenses_query = self.db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.company_id == company_id,
            Transaction.type.in_(["purchase", "expense"]),
            Transaction.transaction_date >= start_date
        ).scalar() or 0
        
        # Flux de trésorerie
        cash_flow = sales_query - expenses_query
        
        # Nombre de transactions
        transaction_count = self.db.query(Transaction).filter(
            Transaction.company_id == company_id,
            Transaction.transaction_date >= start_date
        ).count()
        
        # Précision des prédictions
        predictions_accuracy = self.db.query(
            func.avg(Prediction.prediction_accuracy)
        ).filter(
            Prediction.company_id == company_id,
            Prediction.prediction_accuracy.isnot(None)
        ).scalar() or 0
        
        return [
            KPIResponse(
                name="Chiffre d'affaires",
                value=sales_query,
                format="currency",
                trend=await self._calculate_trend(company_id, "sales", start_date)
            ),
            KPIResponse(
                name="Flux de trésorerie",
                value=cash_flow,
                format="currency",
                trend=await self._calculate_trend(company_id, "cash_flow", start_date)
            ),
            KPIResponse(
                name="Nombre de transactions",
                value=transaction_count,
                format="number",
                trend=await self._calculate_trend(company_id, "transaction_count", start_date)
            ),
            KPIResponse(
                name="Précision IA",
                value=predictions_accuracy * 100,
                format="percentage",
                trend=await self._calculate_trend(company_id, "accuracy", start_date)
            )
        ]
    
    async def _calculate_trends(
        self,
        company_id: str,
        start_date: datetime
    ) -> List[Dict]:
        """Calculer les tendances temporelles"""
        
        # Grouper par jour
        daily_sales = self.db.query(
            func.date(Transaction.transaction_date).label("date"),
            func.sum(Transaction.amount).label("amount")
        ).filter(
            Transaction.company_id == company_id,
            Transaction.type == "sale",
            Transaction.transaction_date >= start_date
        ).group_by(
            func.date(Transaction.transaction_date)
        ).all()
        
        return [
            {
                "date": record.date.isoformat(),
                "value": float(record.amount)
            }
            for record in daily_sales
        ]
    
    def _parse_period(self, period: str) -> int:
        """Parser la période en nombre de jours"""
        period_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365
        }
        return period_map.get(period, 30)
```

---

## 📤 API UPLOAD

### Upload Service
```python
# 📤 services/upload_service.py - Service d'upload

import io
import pandas as pd
from typing import Dict, List, Optional, Tuple
from fastapi import UploadFile, HTTPException
from app.core.database import get_db
from app.services.transaction_service import TransactionService
from app.utils.data_validation import DataValidator
from app.utils.file_processing import ExcelProcessor

class UploadService:
    def __init__(self, db):
        self.db = db
        self.validator = DataValidator()
        self.excel_processor = ExcelProcessor()
        self.transaction_service = TransactionService(db)
    
    async def process_file_upload(
        self,
        file: UploadFile,
        company_id: str,
        user_id: str
    ) -> Dict:
        """Traiter un fichier uploadé"""
        
        # Validation du fichier
        if not self._validate_file(file):
            raise HTTPException(
                status_code=400,
                detail="Type de fichier non supporté"
            )
        
        # Lire le fichier
        content = await file.read()
        
        # Traiter selon le type
        if file.filename.endswith(('.xlsx', '.xls')):
            return await self._process_excel_file(content, company_id, user_id)
        elif file.filename.endswith('.csv'):
            return await self._process_csv_file(content, company_id, user_id)
        else:
            raise HTTPException(
                status_code=400,
                detail="Format de fichier non supporté"
            )
    
    async def _process_excel_file(
        self,
        content: bytes,
        company_id: str,
        user_id: str
    ) -> Dict:
        """Traiter un fichier Excel"""
        
        # Analyser le fichier Excel
        analysis = await self.excel_processor.analyze_file(content)
        
        # Extraire les données
        df = await self.excel_processor.extract_data(
            content,
            sheet_name=analysis['main_sheet'],
            column_mapping=analysis['column_mapping']
        )
        
        # Valider les données
        validation_result = await self.validator.validate_dataframe(df)
        
        if not validation_result['is_valid']:
            return {
                "success": False,
                "error": "Données invalides",
                "validation_errors": validation_result['errors']
            }
        
        # Transformer et sauvegarder
        transactions_created = await self.transaction_service.create_transactions_from_dataframe(
            df=df,
            company_id=company_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "analysis_results": {
                "dataType": "transactions",
                "rowCount": len(df),
                "columnCount": len(df.columns),
                "dateRange": {
                    "start": df['transaction_date'].min().isoformat(),
                    "end": df['transaction_date'].max().isoformat()
                },
                "detectedColumns": list(analysis['column_mapping'].values()),
                "dataQuality": validation_result['quality_score'],
                "suggestions": validation_result['suggestions']
            },
            "transactions_created": transactions_created
        }
    
    def _validate_file(self, file: UploadFile) -> bool:
        """Valider le fichier uploadé"""
        
        # Vérifier l'extension
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        if not any(file.filename.endswith(ext) for ext in allowed_extensions):
            return False
        
        # Vérifier la taille (10MB max)
        if file.size > 10 * 1024 * 1024:
            return False
        
        return True
```

Cette spécification complète du Backend API fournit une architecture robuste et scalable pour EZBI Analytics, avec toutes les fonctionnalités nécessaires pour la gestion des utilisateurs, des prédictions, des analytics et des uploads de fichiers.