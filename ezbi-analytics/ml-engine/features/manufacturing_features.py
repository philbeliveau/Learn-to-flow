"""
Manufacturing-Specific Feature Engineering
Specialized features for manufacturing forecasting and optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime, timedelta
import warnings

from features.extractors.time_features import TimeFeatureExtractor, LagFeatureExtractor, RollingFeatureExtractor
from config.ml_config import config

class ManufacturingFeatureEngine(BaseEstimator, TransformerMixin):
    """Comprehensive feature engineering for manufacturing data"""
    
    def __init__(self, 
                 include_time_features: bool = True,
                 include_lag_features: bool = True,
                 include_rolling_features: bool = True,
                 include_manufacturing_features: bool = True,
                 include_interaction_features: bool = True,
                 include_domain_features: bool = True):
        """
        Initialize Manufacturing Feature Engine
        
        Args:
            include_time_features: Include time-based features
            include_lag_features: Include lag features
            include_rolling_features: Include rolling window features
            include_manufacturing_features: Include manufacturing-specific features
            include_interaction_features: Include feature interactions
            include_domain_features: Include domain knowledge features
        """
        self.include_time_features = include_time_features
        self.include_lag_features = include_lag_features
        self.include_rolling_features = include_rolling_features
        self.include_manufacturing_features = include_manufacturing_features
        self.include_interaction_features = include_interaction_features
        self.include_domain_features = include_domain_features
        
        # Feature extractors
        self.time_extractor = None
        self.lag_extractor = None
        self.rolling_extractor = None
        
        # Scalers and encoders
        self.scalers = {}
        self.encoders = {}
        
        # Configuration
        self.feature_config = config.features
        
        # Fitted state
        self.is_fitted = False
        self.feature_names = None
        self.original_columns = None
    
    def _create_shift_efficiency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create shift efficiency features"""
        if 'current_shift' not in df.columns:
            return df
        
        result = df.copy()
        
        # Shift performance indicators
        for shift in ['morning', 'afternoon', 'night']:
            shift_mask = df['current_shift'] == shift
            
            if 'production_volume' in df.columns:
                # Average production per shift
                result[f'{shift}_avg_production'] = df['production_volume'].where(shift_mask).rolling(7).mean()
                
                # Shift efficiency trend
                result[f'{shift}_efficiency_trend'] = (
                    df['production_volume'].where(shift_mask).rolling(7).mean() -
                    df['production_volume'].where(shift_mask).rolling(14).mean()
                )
        
        # Shift transitions impact
        if 'is_shift_start' in df.columns:
            result['shift_transition_impact'] = (
                df['is_shift_start'].rolling(3).sum() * 
                df.get('efficiency_rate', 1.0)
            )
        
        return result
    
    def _create_machine_utilization_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create machine utilization features"""
        result = df.copy()
        
        # Machine efficiency features
        if 'machine_utilization' in df.columns:
            # Utilization efficiency bands
            result['high_utilization'] = (df['machine_utilization'] > 0.8).astype(int)
            result['medium_utilization'] = (
                (df['machine_utilization'] > 0.6) & 
                (df['machine_utilization'] <= 0.8)
            ).astype(int)
            result['low_utilization'] = (df['machine_utilization'] <= 0.6).astype(int)
            
            # Utilization stability
            result['utilization_stability'] = (
                1.0 / (df['machine_utilization'].rolling(7).std() + 0.01)
            )
            
            # Utilization momentum
            result['utilization_momentum'] = (
                df['machine_utilization'].rolling(3).mean() -
                df['machine_utilization'].rolling(7).mean()
            )
        
        # Machine performance indicators
        if 'maintenance_hours' in df.columns:
            # Maintenance impact
            result['maintenance_impact'] = (
                df['maintenance_hours'].rolling(7).sum() /
                (df.get('machine_utilization', 1.0) + 0.01)
            )
            
            # Days since maintenance
            result['days_since_maintenance'] = (
                df['maintenance_hours'].rolling(30, min_periods=1).apply(
                    lambda x: np.argmax(x[::-1] > 0) if np.any(x > 0) else 30
                )
            )
        
        return result
    
    def _create_quality_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create quality-related features"""
        result = df.copy()
        
        if 'quality_score' in df.columns:
            # Quality bands
            result['high_quality'] = (df['quality_score'] > 0.95).astype(int)
            result['medium_quality'] = (
                (df['quality_score'] > 0.85) & 
                (df['quality_score'] <= 0.95)
            ).astype(int)
            result['low_quality'] = (df['quality_score'] <= 0.85).astype(int)
            
            # Quality trend
            result['quality_trend'] = (
                df['quality_score'].rolling(7).mean() -
                df['quality_score'].rolling(14).mean()
            )
            
            # Quality volatility
            result['quality_volatility'] = df['quality_score'].rolling(7).std()
            
            # Quality momentum
            result['quality_momentum'] = (
                df['quality_score'].diff().rolling(3).mean()
            )
        
        # Defect rate features
        if 'defect_rate' in df.columns:
            result['defect_rate_ma'] = df['defect_rate'].rolling(7).mean()
            result['defect_rate_trend'] = df['defect_rate'].diff().rolling(3).mean()
            result['defect_spike'] = (
                df['defect_rate'] > df['defect_rate'].rolling(14).mean() + 
                2 * df['defect_rate'].rolling(14).std()
            ).astype(int)
        
        return result
    
    def _create_production_cycle_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create production cycle features"""
        result = df.copy()
        
        if 'production_volume' in df.columns:
            # Production cycle patterns
            result['production_cycle_position'] = (
                df.index.dayofweek / 6.0  # Normalized day of week
            )
            
            # Weekly production pattern
            result['weekly_production_pattern'] = (
                df['production_volume'].rolling(7).mean() / 
                df['production_volume'].rolling(28).mean()
            )
            
            # Monthly production pattern
            result['monthly_production_pattern'] = (
                df['production_volume'].rolling(30).mean() / 
                df['production_volume'].rolling(90).mean()
            )
            
            # Production acceleration
            result['production_acceleration'] = (
                df['production_volume'].diff().diff()
            )
            
            # Production efficiency
            if 'target_production' in df.columns:
                result['production_efficiency'] = (
                    df['production_volume'] / 
                    (df['target_production'] + 0.01)
                )
                
                result['efficiency_gap'] = (
                    df['target_production'] - df['production_volume']
                )
        
        return result
    
    def _create_external_factor_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create external factor features"""
        result = df.copy()
        
        # Weather impact features
        weather_cols = ['temperature', 'humidity', 'pressure']
        for col in weather_cols:
            if col in df.columns:
                # Weather comfort zones
                if col == 'temperature':
                    result['temp_comfort_zone'] = (
                        (df[col] > 18) & (df[col] < 25)
                    ).astype(int)
                elif col == 'humidity':
                    result['humidity_comfort_zone'] = (
                        (df[col] > 40) & (df[col] < 60)
                    ).astype(int)
                
                # Weather stability
                result[f'{col}_stability'] = (
                    1.0 / (df[col].rolling(7).std() + 0.01)
                )
                
                # Weather extremes
                result[f'{col}_extreme'] = (
                    np.abs(df[col] - df[col].rolling(30).mean()) > 
                    2 * df[col].rolling(30).std()
                ).astype(int)
        
        # Economic factors
        economic_cols = ['raw_material_price', 'energy_cost', 'labor_cost']
        for col in economic_cols:
            if col in df.columns:
                # Cost pressure
                result[f'{col}_pressure'] = (
                    df[col] / df[col].rolling(30).mean()
                )
                
                # Cost volatility
                result[f'{col}_volatility'] = df[col].rolling(7).std()
                
                # Cost trend
                result[f'{col}_trend'] = (
                    df[col].rolling(7).mean() - 
                    df[col].rolling(14).mean()
                )
        
        return result
    
    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features between different domains"""
        result = df.copy()
        
        # Production-Quality interaction
        if 'production_volume' in df.columns and 'quality_score' in df.columns:
            result['production_quality_ratio'] = (
                df['production_volume'] * df['quality_score']
            )
            
            result['quality_pressure'] = (
                df['production_volume'] / (df['quality_score'] + 0.01)
            )
        
        # Utilization-Efficiency interaction
        if 'machine_utilization' in df.columns and 'efficiency_rate' in df.columns:
            result['utilization_efficiency'] = (
                df['machine_utilization'] * df['efficiency_rate']
            )
            
            result['efficiency_utilization_gap'] = (
                df['efficiency_rate'] - df['machine_utilization']
            )
        
        # Shift-Performance interaction
        if 'current_shift' in df.columns and 'production_volume' in df.columns:
            # Encode shift numerically for interaction
            shift_encoded = result['current_shift'].map({
                'morning': 0, 'afternoon': 1, 'night': 2
            }).fillna(0)
            
            result['shift_performance_interaction'] = (
                shift_encoded * df['production_volume']
            )
        
        # Weather-Production interaction
        if 'temperature' in df.columns and 'production_volume' in df.columns:
            result['temp_production_interaction'] = (
                df['temperature'] * df['production_volume']
            )
        
        # Maintenance-Quality interaction
        if 'maintenance_hours' in df.columns and 'quality_score' in df.columns:
            result['maintenance_quality_impact'] = (
                df['maintenance_hours'].rolling(7).sum() * 
                df['quality_score']
            )
        
        return result
    
    def _create_domain_knowledge_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features based on manufacturing domain knowledge"""
        result = df.copy()
        
        # OEE (Overall Equipment Effectiveness) components
        if all(col in df.columns for col in ['availability', 'performance', 'quality_score']):
            result['oee'] = (
                df['availability'] * df['performance'] * df['quality_score']
            )
        
        # Throughput efficiency
        if 'production_volume' in df.columns and 'cycle_time' in df.columns:
            result['throughput_efficiency'] = (
                df['production_volume'] / (df['cycle_time'] + 0.01)
            )
        
        # Resource utilization efficiency
        if 'operator_count' in df.columns and 'production_volume' in df.columns:
            result['labor_productivity'] = (
                df['production_volume'] / (df['operator_count'] + 0.01)
            )
        
        # Energy efficiency
        if 'energy_consumption' in df.columns and 'production_volume' in df.columns:
            result['energy_efficiency'] = (
                df['production_volume'] / (df['energy_consumption'] + 0.01)
            )
        
        # Setup efficiency
        if 'setup_time' in df.columns and 'production_volume' in df.columns:
            result['setup_efficiency'] = (
                df['production_volume'] / (df['setup_time'] + 0.01)
            )
        
        # Bottleneck indicators
        if 'queue_length' in df.columns:
            result['bottleneck_indicator'] = (
                df['queue_length'] > df['queue_length'].rolling(7).mean() + 
                df['queue_length'].rolling(7).std()
            ).astype(int)
        
        # Process stability indicators
        if 'process_variation' in df.columns:
            result['process_stability'] = (
                1.0 / (df['process_variation'] + 0.01)
            )
        
        # Capacity utilization
        if 'actual_capacity' in df.columns and 'max_capacity' in df.columns:
            result['capacity_utilization'] = (
                df['actual_capacity'] / (df['max_capacity'] + 0.01)
            )
        
        return result
    
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        """
        Fit the feature engine to training data
        
        Args:
            X: Input feature matrix
            y: Target values (optional)
        """
        self.original_columns = X.columns.tolist()
        
        # Initialize feature extractors
        if self.include_time_features:
            self.time_extractor = TimeFeatureExtractor(
                include_holidays=True,
                include_business_calendar=True,
                include_manufacturing_shifts=True,
                include_cyclical_encoding=True
            )
        
        if self.include_lag_features:
            self.lag_extractor = LagFeatureExtractor(
                lag_config=self.feature_config.lag_features
            )
        
        if self.include_rolling_features:
            self.rolling_extractor = RollingFeatureExtractor(
                rolling_config=self.feature_config.rolling_features
            )
        
        # Fit extractors
        if self.time_extractor:
            self.time_extractor.fit(X)
        
        if self.lag_extractor:
            self.lag_extractor.fit(X)
        
        if self.rolling_extractor:
            self.rolling_extractor.fit(X)
        
        # Fit scalers for numerical features
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in X.columns:
                self.scalers[col] = StandardScaler()
                self.scalers[col].fit(X[col].values.reshape(-1, 1))
        
        # Fit encoders for categorical features
        categorical_columns = X.select_dtypes(include=['object', 'category']).columns
        for col in categorical_columns:
            if col in X.columns:
                self.encoders[col] = LabelEncoder()
                self.encoders[col].fit(X[col].fillna('missing'))
        
        self.is_fitted = True
        
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform input data with feature engineering
        
        Args:
            X: Input feature matrix
            
        Returns:
            Transformed feature matrix
        """
        if not self.is_fitted:
            raise ValueError("FeatureEngine must be fitted before transform")
        
        result = X.copy()
        
        # Apply time features
        if self.include_time_features and self.time_extractor:
            result = self.time_extractor.transform(result)
        
        # Apply lag features
        if self.include_lag_features and self.lag_extractor:
            result = self.lag_extractor.transform(result)
        
        # Apply rolling features
        if self.include_rolling_features and self.rolling_extractor:
            result = self.rolling_extractor.transform(result)
        
        # Apply manufacturing-specific features
        if self.include_manufacturing_features:
            result = self._create_shift_efficiency_features(result)
            result = self._create_machine_utilization_features(result)
            result = self._create_quality_features(result)
            result = self._create_production_cycle_features(result)
            result = self._create_external_factor_features(result)
        
        # Apply interaction features
        if self.include_interaction_features:
            result = self._create_interaction_features(result)
        
        # Apply domain knowledge features
        if self.include_domain_features:
            result = self._create_domain_knowledge_features(result)
        
        # Handle missing values
        result = self._handle_missing_values(result)
        
        # Store final feature names
        self.feature_names = result.columns.tolist()
        
        return result
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in features"""
        result = df.copy()
        
        # Forward fill for time series
        result = result.fillna(method='ffill')
        
        # Backward fill for remaining
        result = result.fillna(method='bfill')
        
        # Fill remaining with median/mode
        for col in result.columns:
            if result[col].dtype in ['int64', 'float64']:
                result[col] = result[col].fillna(result[col].median())
            else:
                result[col] = result[col].fillna(result[col].mode()[0] if not result[col].mode().empty else 'missing')
        
        return result
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names after transformation"""
        if not self.is_fitted:
            raise ValueError("FeatureEngine must be fitted first")
        
        return self.feature_names if self.feature_names else []
    
    def get_feature_importance_groups(self) -> Dict[str, List[str]]:
        """Get feature groups for importance analysis"""
        if not self.feature_names:
            return {}
        
        groups = {
            'time_features': [],
            'lag_features': [],
            'rolling_features': [],
            'manufacturing_features': [],
            'interaction_features': [],
            'domain_features': [],
            'original_features': []
        }
        
        for feature in self.feature_names:
            if any(time_feat in feature for time_feat in ['hour', 'day', 'week', 'month', 'quarter', 'holiday', 'business', 'shift']):
                groups['time_features'].append(feature)
            elif '_lag_' in feature:
                groups['lag_features'].append(feature)
            elif '_rolling_' in feature:
                groups['rolling_features'].append(feature)
            elif any(manuf_feat in feature for manuf_feat in ['efficiency', 'utilization', 'quality', 'production', 'maintenance']):
                groups['manufacturing_features'].append(feature)
            elif '_interaction' in feature or '_ratio' in feature:
                groups['interaction_features'].append(feature)
            elif any(domain_feat in feature for domain_feat in ['oee', 'throughput', 'productivity', 'bottleneck', 'capacity']):
                groups['domain_features'].append(feature)
            elif feature in self.original_columns:
                groups['original_features'].append(feature)
        
        return groups