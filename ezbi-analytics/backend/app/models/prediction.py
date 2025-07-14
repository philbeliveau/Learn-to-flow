from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, JSON, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
import enum

from app.core.database import Base

class PredictionType(enum.Enum):
    """Prediction type classification."""
    CASH_FLOW = "cash_flow"
    REVENUE = "revenue"
    EXPENSES = "expenses"
    LIQUIDITY = "liquidity"
    PROFITABILITY = "profitability"
    WORKING_CAPITAL = "working_capital"
    CUSTOM = "custom"

class PredictionStatus(enum.Enum):
    """Prediction status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ModelType(enum.Enum):
    """ML model types."""
    PROPHET = "prophet"
    LSTM = "lstm"
    ARIMA = "arima"
    ENSEMBLE = "ensemble"
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    CUSTOM = "custom"

class Prediction(Base):
    """ML predictions and forecasts."""
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Prediction identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    prediction_type = Column(String(30), nullable=False)
    
    # Prediction parameters
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    prediction_horizon = Column(Integer, nullable=False)  # Days
    
    # Model information
    model_type = Column(String(30), nullable=False)
    model_version = Column(String(20), nullable=True)
    model_parameters = Column(JSON, nullable=True)
    
    # Prediction results
    predictions = Column(JSON, nullable=True)  # Array of prediction points
    confidence_intervals = Column(JSON, nullable=True)  # Upper/lower bounds
    metrics = Column(JSON, nullable=True)  # Model performance metrics
    
    # Accuracy and validation
    accuracy_score = Column(Numeric(5, 4), nullable=True)  # 0.0000-1.0000
    validation_results = Column(JSON, nullable=True)
    
    # Status and processing
    status = Column(String(20), default=PredictionStatus.PENDING.value)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Business context
    business_assumptions = Column(JSON, nullable=True)
    external_factors = Column(JSON, nullable=True)
    seasonality_data = Column(JSON, nullable=True)
    
    # Feature importance and explainability
    feature_importance = Column(JSON, nullable=True)
    model_explanation = Column(JSON, nullable=True)
    
    # Data sources and inputs
    data_sources = Column(JSON, nullable=True)
    input_features = Column(JSON, nullable=True)
    data_quality_score = Column(Numeric(5, 4), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # User tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="predictions")
    creator = relationship("User", foreign_keys=[created_by])
    scenarios = relationship("PredictionScenario", back_populates="prediction")
    
    # Hybrid properties
    @hybrid_property
    def is_completed(self) -> bool:
        """Check if prediction is completed."""
        return self.status == PredictionStatus.COMPLETED.value
    
    @hybrid_property
    def is_failed(self) -> bool:
        """Check if prediction failed."""
        return self.status == PredictionStatus.FAILED.value
    
    @hybrid_property
    def duration_days(self) -> int:
        """Get prediction duration in days."""
        return (self.end_date - self.start_date).days
    
    @hybrid_property
    def is_short_term(self) -> bool:
        """Check if prediction is short-term (< 30 days)."""
        return self.prediction_horizon < 30
    
    @hybrid_property
    def is_long_term(self) -> bool:
        """Check if prediction is long-term (> 90 days)."""
        return self.prediction_horizon > 90
    
    @hybrid_property
    def is_high_accuracy(self) -> bool:
        """Check if prediction has high accuracy (> 0.8)."""
        return self.accuracy_score and self.accuracy_score > 0.8
    
    # Methods
    def get_prediction_summary(self) -> Dict[str, Any]:
        """Get summary of prediction results."""
        if not self.predictions:
            return {}
        
        values = [p["value"] for p in self.predictions if "value" in p]
        if not values:
            return {}
        
        return {
            "total_predictions": len(values),
            "avg_value": sum(values) / len(values),
            "min_value": min(values),
            "max_value": max(values),
            "trend": self._calculate_trend(values),
            "volatility": self._calculate_volatility(values),
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate overall trend direction."""
        if len(values) < 2:
            return "stable"
        
        start_avg = sum(values[:len(values)//3]) / (len(values)//3)
        end_avg = sum(values[-len(values)//3:]) / (len(values)//3)
        
        if end_avg > start_avg * 1.05:
            return "increasing"
        elif end_avg < start_avg * 0.95:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate coefficient of variation as volatility measure."""
        if len(values) < 2:
            return 0.0
        
        import statistics
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        return std_dev / mean if mean != 0 else 0.0
    
    def get_confidence_summary(self) -> Dict[str, Any]:
        """Get confidence interval summary."""
        if not self.confidence_intervals:
            return {}
        
        intervals = self.confidence_intervals
        
        return {
            "avg_lower_bound": sum(ci["lower"] for ci in intervals) / len(intervals),
            "avg_upper_bound": sum(ci["upper"] for ci in intervals) / len(intervals),
            "avg_confidence_width": sum(ci["upper"] - ci["lower"] for ci in intervals) / len(intervals),
            "min_confidence": min(ci.get("confidence", 0.95) for ci in intervals),
            "max_confidence": max(ci.get("confidence", 0.95) for ci in intervals),
        }
    
    def get_model_metrics(self) -> Dict[str, Any]:
        """Get model performance metrics."""
        if not self.metrics:
            return {}
        
        return {
            "accuracy_score": float(self.accuracy_score) if self.accuracy_score else None,
            "mae": self.metrics.get("mae"),  # Mean Absolute Error
            "mse": self.metrics.get("mse"),  # Mean Squared Error
            "rmse": self.metrics.get("rmse"),  # Root Mean Squared Error
            "mape": self.metrics.get("mape"),  # Mean Absolute Percentage Error
            "r2_score": self.metrics.get("r2_score"),  # R-squared
            "data_quality_score": float(self.data_quality_score) if self.data_quality_score else None,
        }
    
    def get_feature_importance_summary(self) -> Dict[str, Any]:
        """Get feature importance summary."""
        if not self.feature_importance:
            return {}
        
        # Sort features by importance
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "top_features": sorted_features[:5],
            "total_features": len(self.feature_importance),
            "most_important": sorted_features[0] if sorted_features else None,
            "least_important": sorted_features[-1] if sorted_features else None,
        }
    
    def add_business_assumption(self, assumption: Dict[str, Any]) -> None:
        """Add business assumption to prediction."""
        assumptions = self.business_assumptions or []
        assumptions.append({
            **assumption,
            "added_at": datetime.utcnow().isoformat(),
        })
        self.business_assumptions = assumptions
    
    def add_external_factor(self, factor: Dict[str, Any]) -> None:
        """Add external factor to prediction."""
        factors = self.external_factors or []
        factors.append({
            **factor,
            "added_at": datetime.utcnow().isoformat(),
        })
        self.external_factors = factors
    
    def calculate_accuracy_against_actual(self, actual_data: List[Dict[str, Any]]) -> None:
        """Calculate accuracy against actual data."""
        if not self.predictions or not actual_data:
            return
        
        # Match predictions with actual data by date
        errors = []
        for pred in self.predictions:
            pred_date = pred.get("date")
            pred_value = pred.get("value")
            
            # Find matching actual data
            actual_value = None
            for actual in actual_data:
                if actual.get("date") == pred_date:
                    actual_value = actual.get("value")
                    break
            
            if actual_value is not None and pred_value is not None:
                error = abs(pred_value - actual_value)
                relative_error = error / abs(actual_value) if actual_value != 0 else 0
                errors.append(relative_error)
        
        if errors:
            # Calculate Mean Absolute Percentage Error (MAPE)
            mape = sum(errors) / len(errors)
            self.accuracy_score = max(0, 1 - mape)  # Convert to accuracy score
            
            # Update metrics
            current_metrics = self.metrics or {}
            current_metrics.update({
                "mape": mape,
                "accuracy_calculated_at": datetime.utcnow().isoformat(),
                "validation_points": len(errors),
            })
            self.metrics = current_metrics
    
    def mark_as_completed(self) -> None:
        """Mark prediction as completed."""
        self.status = PredictionStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark prediction as failed."""
        self.status = PredictionStatus.FAILED.value
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
    
    def to_dict(self, include_detailed: bool = False) -> Dict[str, Any]:
        """Convert prediction to dictionary."""
        result = {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "prediction_type": self.prediction_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "prediction_horizon": self.prediction_horizon,
            "model_type": self.model_type,
            "model_version": self.model_version,
            "status": self.status,
            "accuracy_score": float(self.accuracy_score) if self.accuracy_score else None,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "is_short_term": self.is_short_term,
            "is_long_term": self.is_long_term,
            "is_high_accuracy": self.is_high_accuracy,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        
        if include_detailed:
            result.update({
                "predictions": self.predictions,
                "confidence_intervals": self.confidence_intervals,
                "metrics": self.get_model_metrics(),
                "prediction_summary": self.get_prediction_summary(),
                "confidence_summary": self.get_confidence_summary(),
                "feature_importance": self.get_feature_importance_summary(),
                "business_assumptions": self.business_assumptions,
                "external_factors": self.external_factors,
                "seasonality_data": self.seasonality_data,
                "model_parameters": self.model_parameters,
                "data_sources": self.data_sources,
                "input_features": self.input_features,
                "validation_results": self.validation_results,
                "model_explanation": self.model_explanation,
            })
        
        return result
    
    def __repr__(self):
        return f"<Prediction {self.name} ({self.model_type})>"

class PredictionScenario(Base):
    """Scenario-based predictions for what-if analysis."""
    
    __tablename__ = "prediction_scenarios"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    
    # Scenario details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Scenario parameters
    scenario_type = Column(String(30), nullable=False)  # optimistic, pessimistic, realistic
    parameters = Column(JSON, nullable=False)  # Scenario-specific parameters
    
    # Scenario results
    results = Column(JSON, nullable=True)
    probability = Column(Numeric(5, 4), nullable=True)  # 0.0000-1.0000
    
    # Impact analysis
    impact_analysis = Column(JSON, nullable=True)
    risk_factors = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prediction = relationship("Prediction", back_populates="scenarios")
    
    def calculate_impact(self, baseline_results: Dict[str, Any]) -> None:
        """Calculate impact compared to baseline prediction."""
        if not self.results or not baseline_results:
            return
        
        # Compare key metrics
        impact = {}
        
        for metric in ["total_value", "avg_value", "min_value", "max_value"]:
            baseline_val = baseline_results.get(metric, 0)
            scenario_val = self.results.get(metric, 0)
            
            if baseline_val != 0:
                impact[metric] = {
                    "baseline": baseline_val,
                    "scenario": scenario_val,
                    "difference": scenario_val - baseline_val,
                    "percentage_change": ((scenario_val - baseline_val) / baseline_val) * 100,
                }
        
        self.impact_analysis = impact
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary."""
        return {
            "id": self.id,
            "prediction_id": self.prediction_id,
            "name": self.name,
            "description": self.description,
            "scenario_type": self.scenario_type,
            "parameters": self.parameters,
            "results": self.results,
            "probability": float(self.probability) if self.probability else None,
            "impact_analysis": self.impact_analysis,
            "risk_factors": self.risk_factors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<PredictionScenario {self.name} ({self.scenario_type})>"

class ModelPerformance(Base):
    """Track ML model performance over time."""
    
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Model identification
    model_type = Column(String(30), nullable=False)
    model_version = Column(String(20), nullable=False)
    
    # Performance metrics
    accuracy_score = Column(Numeric(5, 4), nullable=False)
    mae = Column(Numeric(10, 4), nullable=True)
    mse = Column(Numeric(10, 4), nullable=True)
    rmse = Column(Numeric(10, 4), nullable=True)
    mape = Column(Numeric(5, 4), nullable=True)
    r2_score = Column(Numeric(5, 4), nullable=True)
    
    # Data quality metrics
    data_quality_score = Column(Numeric(5, 4), nullable=True)
    training_data_size = Column(Integer, nullable=True)
    validation_data_size = Column(Integer, nullable=True)
    
    # Performance context
    prediction_horizon = Column(Integer, nullable=False)
    prediction_type = Column(String(30), nullable=False)
    
    # Training details
    training_time_ms = Column(Integer, nullable=True)
    training_parameters = Column(JSON, nullable=True)
    
    # Timestamps
    evaluation_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company")
    
    def get_performance_grade(self) -> str:
        """Get performance grade based on accuracy score."""
        if self.accuracy_score >= 0.9:
            return "A+"
        elif self.accuracy_score >= 0.8:
            return "A"
        elif self.accuracy_score >= 0.7:
            return "B"
        elif self.accuracy_score >= 0.6:
            return "C"
        elif self.accuracy_score >= 0.5:
            return "D"
        else:
            return "F"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model performance to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "model_type": self.model_type,
            "model_version": self.model_version,
            "accuracy_score": float(self.accuracy_score),
            "mae": float(self.mae) if self.mae else None,
            "mse": float(self.mse) if self.mse else None,
            "rmse": float(self.rmse) if self.rmse else None,
            "mape": float(self.mape) if self.mape else None,
            "r2_score": float(self.r2_score) if self.r2_score else None,
            "data_quality_score": float(self.data_quality_score) if self.data_quality_score else None,
            "training_data_size": self.training_data_size,
            "validation_data_size": self.validation_data_size,
            "prediction_horizon": self.prediction_horizon,
            "prediction_type": self.prediction_type,
            "training_time_ms": self.training_time_ms,
            "performance_grade": self.get_performance_grade(),
            "evaluation_date": self.evaluation_date.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<ModelPerformance {self.model_type} accuracy={self.accuracy_score}>"
