"""
ML Engine Configuration for EZBI Analytics
Manufacturing-specific ML configuration with French business calendar integration
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
import holidays
from datetime import datetime, timedelta

@dataclass
class ModelConfig:
    """Base model configuration"""
    name: str
    version: str
    enabled: bool = True
    hyperparameters: Dict = None
    
    def __post_init__(self):
        if self.hyperparameters is None:
            self.hyperparameters = {}

@dataclass
class ProphetConfig(ModelConfig):
    """Prophet model configuration with manufacturing seasonality"""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.hyperparameters:
            self.hyperparameters = {
                'growth': 'linear',
                'seasonality_mode': 'multiplicative',
                'yearly_seasonality': True,
                'weekly_seasonality': True,
                'daily_seasonality': False,
                'holidays_prior_scale': 10.0,
                'seasonality_prior_scale': 10.0,
                'changepoint_prior_scale': 0.05,
                'interval_width': 0.80,
                'uncertainty_samples': 1000,
                # Manufacturing-specific seasonalities
                'manufacturing_seasonality': {
                    'quarterly_production': {'period': 91.25, 'fourier_order': 4},
                    'monthly_maintenance': {'period': 30.44, 'fourier_order': 3},
                    'shift_patterns': {'period': 7, 'fourier_order': 2}
                }
            }

@dataclass
class LSTMConfig(ModelConfig):
    """LSTM model configuration with attention mechanism"""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.hyperparameters:
            self.hyperparameters = {
                'sequence_length': 60,
                'hidden_dim': 128,
                'num_layers': 3,
                'dropout': 0.2,
                'attention_dim': 64,
                'batch_size': 32,
                'learning_rate': 0.001,
                'epochs': 100,
                'patience': 15,
                'min_delta': 0.0001,
                'validation_split': 0.2,
                'bidirectional': True,
                'layer_norm': True,
                'gradient_clipping': 1.0
            }

@dataclass
class EnsembleConfig(ModelConfig):
    """Ensemble model configuration"""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.hyperparameters:
            self.hyperparameters = {
                'models': ['prophet', 'lstm', 'xgboost'],
                'weights': 'dynamic',  # or 'equal' or custom dict
                'voting_method': 'weighted_average',
                'meta_learner': 'ridge',
                'stacking_cv': 5,
                'diversity_threshold': 0.1,
                'performance_window': 30,
                'rebalance_frequency': 'daily'
            }

@dataclass
class FeatureConfig:
    """Feature engineering configuration"""
    
    def __init__(self):
        self.time_features = [
            'hour', 'day_of_week', 'day_of_month', 'month', 'quarter',
            'week_of_year', 'is_weekend', 'is_holiday', 'is_business_day'
        ]
        
        self.lag_features = {
            'production_volume': [1, 2, 3, 7, 14, 30],
            'efficiency_rate': [1, 2, 3, 7, 14],
            'maintenance_hours': [1, 7, 14, 30],
            'quality_score': [1, 2, 3, 7]
        }
        
        self.rolling_features = {
            'production_volume': {
                'windows': [3, 7, 14, 30],
                'functions': ['mean', 'std', 'min', 'max']
            },
            'efficiency_rate': {
                'windows': [3, 7, 14],
                'functions': ['mean', 'std', 'trend']
            }
        }
        
        self.manufacturing_features = {
            'shift_patterns': True,
            'machine_utilization': True,
            'operator_efficiency': True,
            'raw_material_quality': True,
            'environmental_factors': True
        }

class MLEngineConfig:
    """Main ML Engine configuration"""
    
    def __init__(self):
        # Model configurations
        self.prophet = ProphetConfig(
            name='prophet_manufacturing',
            version='1.0.0'
        )
        
        self.lstm = LSTMConfig(
            name='lstm_attention',
            version='1.0.0'
        )
        
        self.ensemble = EnsembleConfig(
            name='manufacturing_ensemble',
            version='1.0.0'
        )
        
        # Feature engineering
        self.features = FeatureConfig()
        
        # Training configuration
        self.training = {
            'train_ratio': 0.7,
            'validation_ratio': 0.15,
            'test_ratio': 0.15,
            'cross_validation': {
                'enabled': True,
                'folds': 5,
                'method': 'time_series_split'
            },
            'hyperparameter_tuning': {
                'enabled': True,
                'method': 'optuna',
                'n_trials': 100,
                'direction': 'minimize'
            }
        }
        
        # Inference configuration
        self.inference = {
            'batch_size': 1000,
            'timeout': 30,
            'cache_ttl': 3600,
            'model_refresh_interval': 3600,
            'confidence_threshold': 0.8
        }
        
        # Monitoring configuration
        self.monitoring = {
            'metrics_collection': True,
            'performance_tracking': True,
            'drift_detection': True,
            'alert_thresholds': {
                'accuracy_drop': 0.05,
                'prediction_drift': 0.1,
                'latency_increase': 2.0
            }
        }
        
        # French business calendar
        self.french_holidays = self._get_french_holidays()
        
        # Manufacturing-specific settings
        self.manufacturing = {
            'business_hours': {
                'start': 6,  # 6 AM
                'end': 22,   # 10 PM
                'shifts': [
                    {'name': 'morning', 'start': 6, 'end': 14},
                    {'name': 'afternoon', 'start': 14, 'end': 22},
                    {'name': 'night', 'start': 22, 'end': 6}
                ]
            },
            'maintenance_windows': [
                {'day': 'sunday', 'start': 0, 'end': 6},
                {'day': 'saturday', 'start': 20, 'end': 24}
            ],
            'production_cycles': {
                'daily': 3,  # 3 shifts per day
                'weekly': 6,  # 6 production days per week
                'monthly': 22  # average production days per month
            }
        }
    
    def _get_french_holidays(self) -> List[datetime]:
        """Get French holidays for the next 2 years"""
        france_holidays = holidays.France()
        current_year = datetime.now().year
        
        holiday_dates = []
        for year in range(current_year, current_year + 2):
            holiday_dates.extend(list(france_holidays[year].keys()))
        
        return holiday_dates
    
    def get_business_calendar(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Create business calendar with French holidays and manufacturing schedules"""
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        calendar = pd.DataFrame({
            'date': date_range,
            'is_business_day': [d.weekday() < 6 for d in date_range],
            'is_holiday': [d.date() in self.french_holidays for d in date_range],
            'is_weekend': [d.weekday() >= 5 for d in date_range],
            'day_of_week': [d.weekday() for d in date_range],
            'month': [d.month for d in date_range],
            'quarter': [d.quarter for d in date_range],
            'week_of_year': [d.week for d in date_range]
        })
        
        # Add manufacturing-specific flags
        calendar['is_production_day'] = (
            calendar['is_business_day'] & 
            ~calendar['is_holiday'] & 
            ~calendar['is_weekend']
        )
        
        calendar['shift_count'] = calendar['is_production_day'].astype(int) * 3
        
        return calendar

# Global configuration instance
config = MLEngineConfig()