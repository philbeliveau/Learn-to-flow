"""
Prophet Model Implementation for Manufacturing Forecasting
Specialized for French business calendar and manufacturing seasonality
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import warnings
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from prophet.plot import plot_cross_validation_metric
import holidays
import logging
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from config.ml_config import config

class ManufacturingProphetModel(BaseEstimator, RegressorMixin):
    """Prophet model specialized for manufacturing forecasting"""
    
    def __init__(self, 
                 model_config: Optional[Dict] = None,
                 include_holidays: bool = True,
                 include_manufacturing_seasonality: bool = True,
                 include_regressors: bool = True):
        """
        Initialize Manufacturing Prophet Model
        
        Args:
            model_config: Prophet model configuration
            include_holidays: Include French holidays
            include_manufacturing_seasonality: Include manufacturing seasonalities
            include_regressors: Include external regressors
        """
        self.model_config = model_config or config.prophet.hyperparameters
        self.include_holidays = include_holidays
        self.include_manufacturing_seasonality = include_manufacturing_seasonality
        self.include_regressors = include_regressors
        
        # Initialize Prophet model
        self.model = None
        self.is_fitted = False
        
        # French holidays
        self.french_holidays = self._create_french_holidays()
        
        # Manufacturing seasonalities
        self.manufacturing_seasonalities = self.model_config.get('manufacturing_seasonality', {})
        
        # Regressors
        self.regressors = []
        
        # Performance metrics
        self.performance_metrics = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _create_french_holidays(self) -> pd.DataFrame:
        """Create French holidays dataframe for Prophet"""
        france_holidays = holidays.France()
        
        # Get holidays for extended period
        start_year = datetime.now().year - 2
        end_year = datetime.now().year + 2
        
        holiday_list = []
        for year in range(start_year, end_year + 1):
            for date, name in france_holidays[year].items():
                holiday_list.append({
                    'holiday': name,
                    'ds': pd.to_datetime(date),
                    'lower_window': -1,
                    'upper_window': 1
                })
        
        # Add manufacturing-specific holidays
        manufacturing_holidays = [
            {
                'holiday': 'summer_shutdown',
                'ds': pd.to_datetime(f'{year}-08-15'),
                'lower_window': -3,
                'upper_window': 3
            }
            for year in range(start_year, end_year + 1)
        ]
        
        holiday_list.extend(manufacturing_holidays)
        
        return pd.DataFrame(holiday_list)
    
    def _initialize_prophet(self) -> Prophet:
        """Initialize Prophet model with manufacturing-specific configuration"""
        # Base Prophet configuration
        prophet_params = {
            'growth': self.model_config.get('growth', 'linear'),
            'seasonality_mode': self.model_config.get('seasonality_mode', 'multiplicative'),
            'yearly_seasonality': self.model_config.get('yearly_seasonality', True),
            'weekly_seasonality': self.model_config.get('weekly_seasonality', True),
            'daily_seasonality': self.model_config.get('daily_seasonality', False),
            'holidays_prior_scale': self.model_config.get('holidays_prior_scale', 10.0),
            'seasonality_prior_scale': self.model_config.get('seasonality_prior_scale', 10.0),
            'changepoint_prior_scale': self.model_config.get('changepoint_prior_scale', 0.05),
            'interval_width': self.model_config.get('interval_width', 0.80),
            'uncertainty_samples': self.model_config.get('uncertainty_samples', 1000)
        }
        
        # Add holidays if enabled
        if self.include_holidays:
            prophet_params['holidays'] = self.french_holidays
        
        model = Prophet(**prophet_params)
        
        # Add manufacturing seasonalities
        if self.include_manufacturing_seasonality:
            self._add_manufacturing_seasonalities(model)
        
        return model
    
    def _add_manufacturing_seasonalities(self, model: Prophet):
        """Add manufacturing-specific seasonalities"""
        seasonalities = self.manufacturing_seasonalities
        
        # Quarterly production cycles
        if 'quarterly_production' in seasonalities:
            config = seasonalities['quarterly_production']
            model.add_seasonality(
                name='quarterly_production',
                period=config['period'],
                fourier_order=config['fourier_order'],
                prior_scale=10.0
            )
        
        # Monthly maintenance cycles
        if 'monthly_maintenance' in seasonalities:
            config = seasonalities['monthly_maintenance']
            model.add_seasonality(
                name='monthly_maintenance',
                period=config['period'],
                fourier_order=config['fourier_order'],
                prior_scale=5.0
            )
        
        # Shift patterns
        if 'shift_patterns' in seasonalities:
            config = seasonalities['shift_patterns']
            model.add_seasonality(
                name='shift_patterns',
                period=config['period'],
                fourier_order=config['fourier_order'],
                prior_scale=10.0
            )
        
        # Add custom seasonalities for manufacturing
        model.add_seasonality(
            name='manufacturing_week',
            period=7,
            fourier_order=3,
            condition_name='is_production_week'
        )
        
        model.add_seasonality(
            name='manufacturing_month',
            period=30.44,
            fourier_order=5,
            condition_name='is_production_month'
        )
    
    def _add_regressors(self, model: Prophet, X: pd.DataFrame):
        """Add external regressors to Prophet model"""
        if not self.include_regressors:
            return
        
        # Define potential regressors
        potential_regressors = [
            'temperature', 'humidity', 'pressure',
            'raw_material_price', 'energy_cost',
            'operator_count', 'machine_utilization',
            'maintenance_hours', 'quality_issues',
            'order_backlog', 'inventory_level'
        ]
        
        for regressor in potential_regressors:
            if regressor in X.columns:
                model.add_regressor(
                    regressor,
                    prior_scale=10.0,
                    standardize=True,
                    mode='additive'
                )
                self.regressors.append(regressor)
                self.logger.info(f"Added regressor: {regressor}")
    
    def _prepare_data(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """Prepare data for Prophet training"""
        # Create Prophet format dataframe
        df = pd.DataFrame({
            'ds': X.index,
            'y': y.values
        })
        
        # Add regressors
        for regressor in self.regressors:
            if regressor in X.columns:
                df[regressor] = X[regressor].values
        
        # Add manufacturing conditions
        df['is_production_week'] = (X.index.dayofweek < 5).astype(int)
        df['is_production_month'] = (~X.index.to_series().dt.month.isin([7, 8])).astype(int)
        
        return df
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'ManufacturingProphetModel':
        """
        Fit Prophet model to training data
        
        Args:
            X: Feature matrix with datetime index
            y: Target values
            
        Returns:
            Fitted model
        """
        self.logger.info("Starting Prophet model training...")
        
        # Initialize Prophet model
        self.model = self._initialize_prophet()
        
        # Add regressors
        self._add_regressors(self.model, X)
        
        # Prepare data
        train_data = self._prepare_data(X, y)
        
        # Fit model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(train_data)
        
        self.is_fitted = True
        self.logger.info("Prophet model training completed")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using fitted Prophet model
        
        Args:
            X: Feature matrix with datetime index
            
        Returns:
            Predictions array
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Prepare future dataframe
        future_df = pd.DataFrame({'ds': X.index})
        
        # Add regressors
        for regressor in self.regressors:
            if regressor in X.columns:
                future_df[regressor] = X[regressor].values
            else:
                # Use mean value if regressor not available
                future_df[regressor] = 0
        
        # Add manufacturing conditions
        future_df['is_production_week'] = (X.index.dayofweek < 5).astype(int)
        future_df['is_production_month'] = (~X.index.to_series().dt.month.isin([7, 8])).astype(int)
        
        # Make predictions
        forecast = self.model.predict(future_df)
        
        return forecast['yhat'].values
    
    def predict_with_uncertainty(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Make predictions with uncertainty intervals
        
        Args:
            X: Feature matrix with datetime index
            
        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Prepare future dataframe
        future_df = pd.DataFrame({'ds': X.index})
        
        # Add regressors
        for regressor in self.regressors:
            if regressor in X.columns:
                future_df[regressor] = X[regressor].values
            else:
                future_df[regressor] = 0
        
        # Add manufacturing conditions
        future_df['is_production_week'] = (X.index.dayofweek < 5).astype(int)
        future_df['is_production_month'] = (~X.index.to_series().dt.month.isin([7, 8])).astype(int)
        
        # Make predictions
        forecast = self.model.predict(future_df)
        
        return (
            forecast['yhat'].values,
            forecast['yhat_lower'].values,
            forecast['yhat_upper'].values
        )
    
    def cross_validate(self, X: pd.DataFrame, y: pd.Series, 
                      periods: str = '30 days', 
                      horizon: str = '7 days',
                      initial: str = '90 days') -> pd.DataFrame:
        """
        Perform cross-validation on Prophet model
        
        Args:
            X: Feature matrix
            y: Target values
            periods: Cross-validation periods
            horizon: Forecast horizon
            initial: Initial training period
            
        Returns:
            Cross-validation results
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before cross-validation")
        
        # Prepare data
        train_data = self._prepare_data(X, y)
        
        # Perform cross-validation
        cv_results = cross_validation(
            self.model,
            initial=initial,
            period=periods,
            horizon=horizon,
            parallel='processes'
        )
        
        # Calculate performance metrics
        cv_metrics = performance_metrics(cv_results)
        
        # Store metrics
        self.performance_metrics['cross_validation'] = {
            'mae': cv_metrics['mae'].mean(),
            'mape': cv_metrics['mape'].mean(),
            'rmse': cv_metrics['rmse'].mean(),
            'coverage': cv_metrics['coverage'].mean()
        }
        
        return cv_results
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate model performance
        
        Args:
            X: Feature matrix
            y: True values
            
        Returns:
            Performance metrics
        """
        predictions = self.predict(X)
        
        metrics = {
            'mae': mean_absolute_error(y, predictions),
            'mse': mean_squared_error(y, predictions),
            'rmse': np.sqrt(mean_squared_error(y, predictions)),
            'r2': r2_score(y, predictions),
            'mape': np.mean(np.abs((y - predictions) / y)) * 100
        }
        
        self.performance_metrics['evaluation'] = metrics
        
        return metrics
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance from Prophet model"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        
        # Get regressor coefficients
        importance_data = []
        
        # Regressor importance
        for regressor in self.regressors:
            if hasattr(self.model, 'extra_regressors') and regressor in self.model.extra_regressors:
                coef = self.model.extra_regressors[regressor]['coef']
                importance_data.append({
                    'feature': regressor,
                    'importance': abs(coef),
                    'coefficient': coef,
                    'type': 'regressor'
                })
        
        # Seasonality importance (approximated)
        seasonalities = ['yearly', 'weekly', 'quarterly_production', 'monthly_maintenance', 'shift_patterns']
        for seasonality in seasonalities:
            if seasonality in self.model.seasonalities:
                # Use seasonality prior scale as proxy for importance
                importance_data.append({
                    'feature': seasonality,
                    'importance': self.model.seasonalities[seasonality]['prior_scale'],
                    'coefficient': self.model.seasonalities[seasonality]['prior_scale'],
                    'type': 'seasonality'
                })
        
        return pd.DataFrame(importance_data).sort_values('importance', ascending=False)
    
    def get_model_components(self, X: pd.DataFrame) -> pd.DataFrame:
        """Get Prophet model components"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting components")
        
        # Prepare future dataframe
        future_df = pd.DataFrame({'ds': X.index})
        
        # Add regressors
        for regressor in self.regressors:
            if regressor in X.columns:
                future_df[regressor] = X[regressor].values
            else:
                future_df[regressor] = 0
        
        # Add manufacturing conditions
        future_df['is_production_week'] = (X.index.dayofweek < 5).astype(int)
        future_df['is_production_month'] = (~X.index.to_series().dt.month.isin([7, 8])).astype(int)
        
        # Get forecast with components
        forecast = self.model.predict(future_df)
        
        return forecast
    
    def save_model(self, filepath: str):
        """Save Prophet model to file"""
        import joblib
        
        model_data = {
            'model': self.model,
            'config': self.model_config,
            'regressors': self.regressors,
            'performance_metrics': self.performance_metrics,
            'is_fitted': self.is_fitted
        }
        
        joblib.dump(model_data, filepath)
        self.logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load Prophet model from file"""
        import joblib
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.model_config = model_data['config']
        self.regressors = model_data['regressors']
        self.performance_metrics = model_data['performance_metrics']
        self.is_fitted = model_data['is_fitted']
        
        self.logger.info(f"Model loaded from {filepath}")