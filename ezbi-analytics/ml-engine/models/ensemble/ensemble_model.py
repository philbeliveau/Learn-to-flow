"""
Ensemble Model for Manufacturing Forecasting
Combines Prophet, LSTM, and XGBoost models for superior accuracy
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
import xgboost as xgb
import joblib
import warnings
import logging
from datetime import datetime
from scipy import stats

from models.prophet.prophet_model import ManufacturingProphetModel
from models.lstm.lstm_attention_model import AttentionLSTMModel
from config.ml_config import config

class ManufacturingEnsembleModel(BaseEstimator, RegressorMixin):
    """Advanced ensemble model for manufacturing forecasting"""
    
    def __init__(self, 
                 ensemble_config: Optional[Dict] = None,
                 include_prophet: bool = True,
                 include_lstm: bool = True,
                 include_xgboost: bool = True,
                 include_random_forest: bool = True,
                 meta_learner: str = 'ridge',
                 voting_method: str = 'weighted_average',
                 dynamic_weights: bool = True):
        """
        Initialize Manufacturing Ensemble Model
        
        Args:
            ensemble_config: Ensemble configuration
            include_prophet: Include Prophet model
            include_lstm: Include LSTM model
            include_xgboost: Include XGBoost model
            include_random_forest: Include Random Forest model
            meta_learner: Meta-learner for stacking
            voting_method: Voting method for ensemble
            dynamic_weights: Use dynamic weight adjustment
        """
        self.ensemble_config = ensemble_config or config.ensemble.hyperparameters
        self.include_prophet = include_prophet
        self.include_lstm = include_lstm
        self.include_xgboost = include_xgboost
        self.include_random_forest = include_random_forest
        self.meta_learner = meta_learner
        self.voting_method = voting_method
        self.dynamic_weights = dynamic_weights
        
        # Base models
        self.models = {}
        self.meta_model = None
        
        # Model weights
        self.weights = {}
        self.weight_history = []
        
        # Performance tracking
        self.performance_metrics = {}
        self.model_performances = {}
        
        # Ensemble state
        self.is_fitted = False
        self.feature_names = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_base_models(self):
        """Initialize base models for ensemble"""
        self.models = {}
        
        # Prophet model
        if self.include_prophet:
            self.models['prophet'] = ManufacturingProphetModel(
                model_config=config.prophet.hyperparameters,
                include_holidays=True,
                include_manufacturing_seasonality=True,
                include_regressors=True
            )
        
        # LSTM model
        if self.include_lstm:
            self.models['lstm'] = AttentionLSTMModel(
                model_config=config.lstm.hyperparameters,
                use_attention=True,
                use_bidirectional=True,
                use_layer_norm=True
            )
        
        # XGBoost model
        if self.include_xgboost:
            self.models['xgboost'] = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                objective='reg:squarederror',
                eval_metric='mae'
            )
        
        # Random Forest model
        if self.include_random_forest:
            self.models['random_forest'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        
        self.logger.info(f"Initialized {len(self.models)} base models")
    
    def _initialize_meta_learner(self):
        """Initialize meta-learner for stacking"""
        if self.meta_learner == 'ridge':
            self.meta_model = Ridge(alpha=1.0, random_state=42)
        elif self.meta_learner == 'elastic_net':
            self.meta_model = ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42)
        elif self.meta_learner == 'xgboost':
            self.meta_model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
        elif self.meta_learner == 'random_forest':
            self.meta_model = RandomForestRegressor(
                n_estimators=50,
                max_depth=5,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown meta-learner: {self.meta_learner}")
    
    def _get_initial_weights(self) -> Dict[str, float]:
        """Get initial weights for ensemble"""
        weights_config = self.ensemble_config.get('weights', 'equal')
        
        if weights_config == 'equal':
            weight_value = 1.0 / len(self.models)
            return {model_name: weight_value for model_name in self.models.keys()}
        
        elif weights_config == 'dynamic':
            # Start with equal weights, will be adjusted during training
            weight_value = 1.0 / len(self.models)
            return {model_name: weight_value for model_name in self.models.keys()}
        
        elif isinstance(weights_config, dict):
            # Normalize provided weights
            total_weight = sum(weights_config.values())
            return {k: v / total_weight for k, v in weights_config.items()}
        
        else:
            # Default to equal weights
            weight_value = 1.0 / len(self.models)
            return {model_name: weight_value for model_name in self.models.keys()}
    
    def _train_base_models(self, X: pd.DataFrame, y: pd.Series):
        """Train all base models"""
        self.logger.info("Training base models...")
        
        for model_name, model in self.models.items():
            try:
                self.logger.info(f"Training {model_name} model...")
                
                # Train model
                model.fit(X, y)
                
                # Evaluate model performance
                predictions = model.predict(X)
                
                # Handle NaN predictions (e.g., from LSTM)
                if hasattr(predictions, '__len__') and len(predictions) > 0:
                    valid_mask = ~np.isnan(predictions)
                    if np.any(valid_mask):
                        y_valid = y.values[valid_mask]
                        pred_valid = predictions[valid_mask]
                        
                        performance = {
                            'mae': mean_absolute_error(y_valid, pred_valid),
                            'mse': mean_squared_error(y_valid, pred_valid),
                            'rmse': np.sqrt(mean_squared_error(y_valid, pred_valid)),
                            'r2': r2_score(y_valid, pred_valid)
                        }
                        
                        self.model_performances[model_name] = performance
                        self.logger.info(f"{model_name} - MAE: {performance['mae']:.4f}, R2: {performance['r2']:.4f}")
                    else:
                        self.logger.warning(f"{model_name} produced only NaN predictions")
                        self.model_performances[model_name] = {'mae': float('inf'), 'r2': -float('inf')}
                
            except Exception as e:
                self.logger.error(f"Error training {model_name}: {str(e)}")
                # Remove failed model
                del self.models[model_name]
        
        self.logger.info("Base models training completed")
    
    def _get_base_predictions(self, X: pd.DataFrame) -> pd.DataFrame:
        """Get predictions from all base models"""
        predictions = pd.DataFrame(index=X.index)
        
        for model_name, model in self.models.items():
            try:
                pred = model.predict(X)
                predictions[model_name] = pred
            except Exception as e:
                self.logger.error(f"Error getting predictions from {model_name}: {str(e)}")
                predictions[model_name] = np.nan
        
        return predictions
    
    def _calculate_dynamic_weights(self, X: pd.DataFrame, y: pd.Series, 
                                  window: int = 30) -> Dict[str, float]:
        """Calculate dynamic weights based on recent performance"""
        if len(X) < window * 2:
            return self._get_initial_weights()
        
        # Use recent data for weight calculation
        recent_X = X.tail(window)
        recent_y = y.tail(window)
        
        # Get predictions for recent data
        recent_predictions = self._get_base_predictions(recent_X)
        
        # Calculate performance for each model
        model_scores = {}
        
        for model_name in self.models.keys():
            if model_name in recent_predictions.columns:
                pred = recent_predictions[model_name].values
                
                # Handle NaN predictions
                valid_mask = ~np.isnan(pred)
                if np.any(valid_mask):
                    y_valid = recent_y.values[valid_mask]
                    pred_valid = pred[valid_mask]
                    
                    # Use inverse MAE as score (higher is better)
                    mae = mean_absolute_error(y_valid, pred_valid)
                    model_scores[model_name] = 1.0 / (mae + 1e-8)
                else:
                    model_scores[model_name] = 0.0
            else:
                model_scores[model_name] = 0.0
        
        # Normalize scores to get weights
        total_score = sum(model_scores.values())
        if total_score > 0:
            weights = {name: score / total_score for name, score in model_scores.items()}
        else:
            weights = self._get_initial_weights()
        
        # Apply smoothing to prevent dramatic weight changes
        if hasattr(self, 'weights') and self.weights:
            alpha = 0.3  # Smoothing factor
            smoothed_weights = {}
            for name in weights.keys():
                if name in self.weights:
                    smoothed_weights[name] = alpha * weights[name] + (1 - alpha) * self.weights[name]
                else:
                    smoothed_weights[name] = weights[name]
            weights = smoothed_weights
        
        return weights
    
    def _ensemble_predict(self, base_predictions: pd.DataFrame) -> np.ndarray:
        """Combine base model predictions using ensemble method"""
        if self.voting_method == 'weighted_average':
            # Weighted average prediction
            ensemble_pred = np.zeros(len(base_predictions))
            
            for model_name, weight in self.weights.items():
                if model_name in base_predictions.columns:
                    pred = base_predictions[model_name].values
                    
                    # Handle NaN predictions
                    valid_mask = ~np.isnan(pred)
                    ensemble_pred[valid_mask] += weight * pred[valid_mask]
            
            return ensemble_pred
        
        elif self.voting_method == 'stacking':
            # Use meta-learner for stacking
            if self.meta_model is None:
                raise ValueError("Meta-learner not initialized for stacking")
            
            # Fill NaN values with median
            base_predictions_filled = base_predictions.fillna(base_predictions.median())
            
            return self.meta_model.predict(base_predictions_filled)
        
        elif self.voting_method == 'median':
            # Median ensemble
            return np.nanmedian(base_predictions.values, axis=1)
        
        elif self.voting_method == 'trimmed_mean':
            # Trimmed mean (remove outliers)
            def trimmed_mean(x, trim_percent=0.1):
                return stats.trim_mean(x[~np.isnan(x)], trim_percent)
            
            return np.apply_along_axis(trimmed_mean, axis=1, arr=base_predictions.values)
        
        else:
            raise ValueError(f"Unknown voting method: {self.voting_method}")
    
    def _train_meta_learner(self, X: pd.DataFrame, y: pd.Series):
        """Train meta-learner for stacking"""
        if self.voting_method != 'stacking':
            return
        
        self.logger.info("Training meta-learner...")
        
        # Cross-validation to get out-of-fold predictions
        tscv = TimeSeriesSplit(n_splits=5)
        meta_features = np.zeros((len(X), len(self.models)))
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Train models on fold
            fold_predictions = []
            
            for i, (model_name, model) in enumerate(self.models.items()):
                try:
                    # Create new model instance for this fold
                    if model_name == 'prophet':
                        fold_model = ManufacturingProphetModel()
                    elif model_name == 'lstm':
                        fold_model = AttentionLSTMModel()
                    elif model_name == 'xgboost':
                        fold_model = xgb.XGBRegressor(
                            n_estimators=100, max_depth=6, learning_rate=0.1,
                            random_state=42, n_jobs=-1
                        )
                    elif model_name == 'random_forest':
                        fold_model = RandomForestRegressor(
                            n_estimators=50, max_depth=8, random_state=42, n_jobs=-1
                        )
                    
                    fold_model.fit(X_train, y_train)
                    pred = fold_model.predict(X_val)
                    
                    # Handle NaN predictions
                    if hasattr(pred, '__len__'):
                        pred = np.nan_to_num(pred, nan=y_val.mean())
                    
                    meta_features[val_idx, i] = pred
                    
                except Exception as e:
                    self.logger.error(f"Error in fold {fold} for {model_name}: {str(e)}")
                    meta_features[val_idx, i] = y_val.mean()
        
        # Train meta-learner
        self._initialize_meta_learner()
        self.meta_model.fit(meta_features, y)
        
        self.logger.info("Meta-learner training completed")
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'ManufacturingEnsembleModel':
        """
        Fit ensemble model to training data
        
        Args:
            X: Feature matrix
            y: Target values
            
        Returns:
            Fitted ensemble model
        """
        self.logger.info("Starting ensemble model training...")
        
        # Store feature names
        self.feature_names = X.columns.tolist()
        
        # Initialize base models
        self._initialize_base_models()
        
        # Initialize weights
        self.weights = self._get_initial_weights()
        
        # Train base models
        self._train_base_models(X, y)
        
        # Train meta-learner if using stacking
        if self.voting_method == 'stacking':
            self._train_meta_learner(X, y)
        
        # Calculate dynamic weights if enabled
        if self.dynamic_weights:
            self.weights = self._calculate_dynamic_weights(X, y)
        
        self.is_fitted = True
        self.logger.info("Ensemble model training completed")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using ensemble model
        
        Args:
            X: Feature matrix
            
        Returns:
            Predictions array
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Get base model predictions
        base_predictions = self._get_base_predictions(X)
        
        # Update weights dynamically if enabled
        if self.dynamic_weights and len(X) > 30:
            # Use last known target values for weight update
            # In practice, you'd have a separate validation set
            pass
        
        # Combine predictions
        ensemble_predictions = self._ensemble_predict(base_predictions)
        
        # Store weight history
        self.weight_history.append({
            'timestamp': datetime.now(),
            'weights': self.weights.copy()
        })
        
        return ensemble_predictions
    
    def predict_with_uncertainty(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Make predictions with uncertainty estimation
        
        Args:
            X: Feature matrix
            
        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Get base model predictions
        base_predictions = self._get_base_predictions(X)
        
        # Get ensemble predictions
        ensemble_predictions = self._ensemble_predict(base_predictions)
        
        # Calculate uncertainty using prediction variance
        prediction_std = np.nanstd(base_predictions.values, axis=1)
        
        # Calculate confidence intervals
        lower_bound = ensemble_predictions - 1.96 * prediction_std
        upper_bound = ensemble_predictions + 1.96 * prediction_std
        
        return ensemble_predictions, lower_bound, upper_bound
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate ensemble model performance
        
        Args:
            X: Feature matrix
            y: True values
            
        Returns:
            Performance metrics
        """
        predictions = self.predict(X)
        
        # Calculate metrics
        metrics = {
            'mae': mean_absolute_error(y, predictions),
            'mse': mean_squared_error(y, predictions),
            'rmse': np.sqrt(mean_squared_error(y, predictions)),
            'r2': r2_score(y, predictions),
            'mape': np.mean(np.abs((y - predictions) / y)) * 100
        }
        
        # Add individual model performances
        base_predictions = self._get_base_predictions(X)
        for model_name in self.models.keys():
            if model_name in base_predictions.columns:
                pred = base_predictions[model_name].values
                valid_mask = ~np.isnan(pred)
                
                if np.any(valid_mask):
                    y_valid = y.values[valid_mask]
                    pred_valid = pred[valid_mask]
                    
                    metrics[f'{model_name}_mae'] = mean_absolute_error(y_valid, pred_valid)
                    metrics[f'{model_name}_r2'] = r2_score(y_valid, pred_valid)
        
        self.performance_metrics['evaluation'] = metrics
        
        return metrics
    
    def get_model_weights(self) -> Dict[str, float]:
        """Get current model weights"""
        return self.weights.copy()
    
    def get_model_performances(self) -> Dict[str, Dict[str, float]]:
        """Get individual model performances"""
        return self.model_performances.copy()
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance from ensemble"""
        importance_data = []
        
        for model_name, model in self.models.items():
            if hasattr(model, 'get_feature_importance'):
                try:
                    model_importance = model.get_feature_importance()
                    model_importance['model'] = model_name
                    model_importance['weight'] = self.weights.get(model_name, 0.0)
                    model_importance['weighted_importance'] = (
                        model_importance['importance'] * model_importance['weight']
                    )
                    importance_data.append(model_importance)
                except Exception as e:
                    self.logger.error(f"Error getting feature importance from {model_name}: {str(e)}")
            elif hasattr(model, 'feature_importances_'):
                # For sklearn models
                importances = model.feature_importances_
                for i, feature in enumerate(self.feature_names):
                    importance_data.append({
                        'feature': feature,
                        'importance': importances[i],
                        'model': model_name,
                        'weight': self.weights.get(model_name, 0.0),
                        'weighted_importance': importances[i] * self.weights.get(model_name, 0.0)
                    })
        
        if importance_data:
            return pd.concat(importance_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def save_model(self, filepath: str):
        """Save ensemble model"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before saving")
        
        # Save individual models
        for model_name, model in self.models.items():
            if hasattr(model, 'save_model'):
                model.save_model(f"{filepath}_{model_name}")
            else:
                joblib.dump(model, f"{filepath}_{model_name}.pkl")
        
        # Save meta-learner if using stacking
        if self.meta_model is not None:
            joblib.dump(self.meta_model, f"{filepath}_meta_learner.pkl")
        
        # Save ensemble data
        ensemble_data = {
            'ensemble_config': self.ensemble_config,
            'weights': self.weights,
            'weight_history': self.weight_history,
            'performance_metrics': self.performance_metrics,
            'model_performances': self.model_performances,
            'feature_names': self.feature_names,
            'voting_method': self.voting_method,
            'dynamic_weights': self.dynamic_weights
        }
        
        joblib.dump(ensemble_data, f"{filepath}_ensemble_data.pkl")
        
        self.logger.info(f"Ensemble model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load ensemble model"""
        # Load ensemble data
        ensemble_data = joblib.load(f"{filepath}_ensemble_data.pkl")
        
        self.ensemble_config = ensemble_data['ensemble_config']
        self.weights = ensemble_data['weights']
        self.weight_history = ensemble_data['weight_history']
        self.performance_metrics = ensemble_data['performance_metrics']
        self.model_performances = ensemble_data['model_performances']
        self.feature_names = ensemble_data['feature_names']
        self.voting_method = ensemble_data['voting_method']
        self.dynamic_weights = ensemble_data['dynamic_weights']
        
        # Load individual models
        self.models = {}
        
        for model_name in self.weights.keys():
            try:
                if model_name == 'prophet':
                    model = ManufacturingProphetModel()
                    model.load_model(f"{filepath}_{model_name}")
                elif model_name == 'lstm':
                    model = AttentionLSTMModel()
                    model.load_model(f"{filepath}_{model_name}")
                else:
                    model = joblib.load(f"{filepath}_{model_name}.pkl")
                
                self.models[model_name] = model
            except Exception as e:
                self.logger.error(f"Error loading {model_name}: {str(e)}")
        
        # Load meta-learner if exists
        try:
            self.meta_model = joblib.load(f"{filepath}_meta_learner.pkl")
        except FileNotFoundError:
            self.meta_model = None
        
        self.is_fitted = True
        self.logger.info(f"Ensemble model loaded from {filepath}")