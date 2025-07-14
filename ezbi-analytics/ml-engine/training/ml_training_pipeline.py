"""
ML Training Pipeline for Manufacturing Forecasting
Comprehensive training pipeline with evaluation and optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
import warnings
import joblib
import os
from pathlib import Path

# ML libraries
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

# Model imports
from models.prophet.prophet_model import ManufacturingProphetModel
from models.lstm.lstm_attention_model import AttentionLSTMModel
from models.ensemble.ensemble_model import ManufacturingEnsembleModel
from features.manufacturing_features import ManufacturingFeatureEngine

# Config
from config.ml_config import config

class MLTrainingPipeline:
    """Comprehensive ML training pipeline for manufacturing forecasting"""
    
    def __init__(self, 
                 model_type: str = 'ensemble',
                 output_dir: str = './models',
                 enable_hyperparameter_tuning: bool = True,
                 enable_cross_validation: bool = True,
                 enable_feature_selection: bool = True):
        """
        Initialize ML Training Pipeline
        
        Args:
            model_type: Type of model to train ('prophet', 'lstm', 'ensemble')
            output_dir: Directory to save trained models
            enable_hyperparameter_tuning: Enable hyperparameter optimization
            enable_cross_validation: Enable cross-validation
            enable_feature_selection: Enable feature selection
        """
        self.model_type = model_type
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_hyperparameter_tuning = enable_hyperparameter_tuning
        self.enable_cross_validation = enable_cross_validation
        self.enable_feature_selection = enable_feature_selection
        
        # Pipeline components
        self.feature_engine = None
        self.model = None
        self.study = None
        
        # Training configuration
        self.training_config = config.training
        
        # Results storage
        self.training_results = {}
        self.evaluation_results = {}
        self.hyperparameter_results = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Create log file
        log_file = self.output_dir / f'training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def prepare_data(self, 
                     data: pd.DataFrame,
                     target_column: str,
                     test_size: float = 0.2,
                     validation_size: float = 0.1) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """
        Prepare data for training
        
        Args:
            data: Input dataframe with datetime index
            target_column: Name of target column
            test_size: Proportion of data for testing
            validation_size: Proportion of data for validation
            
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        self.logger.info("Preparing data for training...")
        
        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have datetime index")
        
        # Sort by datetime
        data = data.sort_index()
        
        # Separate features and target
        X = data.drop(columns=[target_column])
        y = data[target_column]
        
        # Time series split
        n_samples = len(data)
        train_size = int(n_samples * (1 - test_size - validation_size))
        val_size = int(n_samples * validation_size)
        
        X_train = X.iloc[:train_size]
        X_val = X.iloc[train_size:train_size + val_size]
        X_test = X.iloc[train_size + val_size:]
        
        y_train = y.iloc[:train_size]
        y_val = y.iloc[train_size:train_size + val_size]
        y_test = y.iloc[train_size + val_size:]
        
        # Initialize and fit feature engine
        self.feature_engine = ManufacturingFeatureEngine(
            include_time_features=True,
            include_lag_features=True,
            include_rolling_features=True,
            include_manufacturing_features=True,
            include_interaction_features=True,
            include_domain_features=True
        )
        
        self.feature_engine.fit(X_train, y_train)
        
        # Transform features
        X_train_transformed = self.feature_engine.transform(X_train)
        X_val_transformed = self.feature_engine.transform(X_val)
        X_test_transformed = self.feature_engine.transform(X_test)
        
        self.logger.info(f"Data preparation completed:")
        self.logger.info(f"  Train: {len(X_train_transformed)} samples")
        self.logger.info(f"  Validation: {len(X_val_transformed)} samples")
        self.logger.info(f"  Test: {len(X_test_transformed)} samples")
        self.logger.info(f"  Features: {len(X_train_transformed.columns)}")
        
        return X_train_transformed, X_val_transformed, X_test_transformed, y_train, y_val, y_test
    
    def _create_objective_function(self, 
                                  X_train: pd.DataFrame, 
                                  y_train: pd.Series,
                                  X_val: pd.DataFrame, 
                                  y_val: pd.Series):
        """Create objective function for hyperparameter tuning"""
        
        def objective(trial):
            try:
                if self.model_type == 'prophet':
                    # Prophet hyperparameters
                    hyperparameters = {
                        'changepoint_prior_scale': trial.suggest_float('changepoint_prior_scale', 0.001, 0.5),
                        'seasonality_prior_scale': trial.suggest_float('seasonality_prior_scale', 0.01, 50),
                        'holidays_prior_scale': trial.suggest_float('holidays_prior_scale', 0.01, 50),
                        'growth': trial.suggest_categorical('growth', ['linear', 'logistic']),
                        'seasonality_mode': trial.suggest_categorical('seasonality_mode', ['additive', 'multiplicative']),
                        'interval_width': trial.suggest_float('interval_width', 0.8, 0.95),
                        'uncertainty_samples': trial.suggest_categorical('uncertainty_samples', [100, 500, 1000])
                    }
                    
                    model = ManufacturingProphetModel(model_config=hyperparameters)
                
                elif self.model_type == 'lstm':
                    # LSTM hyperparameters
                    hyperparameters = {
                        'sequence_length': trial.suggest_int('sequence_length', 30, 120),
                        'hidden_dim': trial.suggest_int('hidden_dim', 64, 256),
                        'num_layers': trial.suggest_int('num_layers', 2, 5),
                        'dropout': trial.suggest_float('dropout', 0.1, 0.5),
                        'attention_dim': trial.suggest_int('attention_dim', 32, 128),
                        'batch_size': trial.suggest_categorical('batch_size', [16, 32, 64]),
                        'learning_rate': trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True),
                        'epochs': trial.suggest_int('epochs', 50, 150)
                    }
                    
                    model = AttentionLSTMModel(model_config=hyperparameters)
                
                elif self.model_type == 'ensemble':
                    # Ensemble hyperparameters
                    hyperparameters = {
                        'voting_method': trial.suggest_categorical('voting_method', ['weighted_average', 'stacking']),
                        'meta_learner': trial.suggest_categorical('meta_learner', ['ridge', 'elastic_net', 'xgboost']),
                        'weights': trial.suggest_categorical('weights', ['equal', 'dynamic']),
                        'diversity_threshold': trial.suggest_float('diversity_threshold', 0.05, 0.2)
                    }
                    
                    model = ManufacturingEnsembleModel(ensemble_config=hyperparameters)
                
                # Train model
                model.fit(X_train, y_train)
                
                # Make predictions
                predictions = model.predict(X_val)
                
                # Calculate error
                # Handle NaN predictions
                if hasattr(predictions, '__len__'):
                    valid_mask = ~np.isnan(predictions)
                    if np.any(valid_mask):
                        y_val_valid = y_val.values[valid_mask]
                        pred_valid = predictions[valid_mask]
                        error = mean_absolute_error(y_val_valid, pred_valid)
                    else:
                        error = float('inf')
                else:
                    error = float('inf')
                
                return error
                
            except Exception as e:
                self.logger.error(f"Error in trial: {str(e)}")
                return float('inf')
        
        return objective
    
    def hyperparameter_optimization(self, 
                                   X_train: pd.DataFrame, 
                                   y_train: pd.Series,
                                   X_val: pd.DataFrame, 
                                   y_val: pd.Series,
                                   n_trials: int = 100) -> Dict[str, Any]:
        """
        Perform hyperparameter optimization
        
        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target
            n_trials: Number of optimization trials
            
        Returns:
            Best hyperparameters
        """
        if not self.enable_hyperparameter_tuning:
            return {}
        
        self.logger.info("Starting hyperparameter optimization...")
        
        # Create study
        self.study = optuna.create_study(
            direction='minimize',
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=10)
        )
        
        # Create objective function
        objective_func = self._create_objective_function(X_train, y_train, X_val, y_val)
        
        # Run optimization
        self.study.optimize(objective_func, n_trials=n_trials)
        
        # Get best parameters
        best_params = self.study.best_params
        best_value = self.study.best_value
        
        self.logger.info(f"Hyperparameter optimization completed:")
        self.logger.info(f"  Best value: {best_value}")
        self.logger.info(f"  Best parameters: {best_params}")
        
        # Save results
        self.hyperparameter_results = {
            'best_params': best_params,
            'best_value': best_value,
            'n_trials': n_trials,
            'study': self.study
        }
        
        return best_params
    
    def cross_validation(self, 
                        X: pd.DataFrame, 
                        y: pd.Series,
                        n_splits: int = 5,
                        gap: int = 0) -> Dict[str, float]:
        """
        Perform time series cross-validation
        
        Args:
            X: Feature matrix
            y: Target values
            n_splits: Number of CV splits
            gap: Gap between train and test sets
            
        Returns:
            Cross-validation results
        """
        if not self.enable_cross_validation:
            return {}
        
        self.logger.info("Starting cross-validation...")
        
        # Time series split
        tscv = TimeSeriesSplit(n_splits=n_splits, gap=gap)
        
        cv_scores = []
        fold_results = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            self.logger.info(f"Processing fold {fold + 1}/{n_splits}")
            
            X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
            y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]
            
            # Create model
            if self.model_type == 'prophet':
                model = ManufacturingProphetModel()
            elif self.model_type == 'lstm':
                model = AttentionLSTMModel()
            elif self.model_type == 'ensemble':
                model = ManufacturingEnsembleModel()
            
            try:
                # Train model
                model.fit(X_train_fold, y_train_fold)
                
                # Make predictions
                predictions = model.predict(X_val_fold)
                
                # Calculate metrics
                valid_mask = ~np.isnan(predictions) if hasattr(predictions, '__len__') else True
                if np.any(valid_mask):
                    y_val_valid = y_val_fold.values[valid_mask] if hasattr(predictions, '__len__') else y_val_fold.values
                    pred_valid = predictions[valid_mask] if hasattr(predictions, '__len__') else predictions
                    
                    mae = mean_absolute_error(y_val_valid, pred_valid)
                    rmse = np.sqrt(mean_squared_error(y_val_valid, pred_valid))
                    r2 = r2_score(y_val_valid, pred_valid)
                    
                    fold_result = {
                        'fold': fold + 1,
                        'mae': mae,
                        'rmse': rmse,
                        'r2': r2,
                        'train_size': len(X_train_fold),
                        'val_size': len(X_val_fold)
                    }
                    
                    cv_scores.append(mae)
                    fold_results.append(fold_result)
                    
                    self.logger.info(f"  Fold {fold + 1} - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")
                
            except Exception as e:
                self.logger.error(f"Error in fold {fold + 1}: {str(e)}")
                cv_scores.append(float('inf'))
        
        # Calculate overall metrics
        cv_results = {
            'mean_mae': np.mean(cv_scores),
            'std_mae': np.std(cv_scores),
            'fold_results': fold_results,
            'n_splits': n_splits
        }
        
        self.logger.info(f"Cross-validation completed:")
        self.logger.info(f"  Mean MAE: {cv_results['mean_mae']:.4f} (+/- {cv_results['std_mae']:.4f})")
        
        return cv_results
    
    def train_model(self, 
                   X_train: pd.DataFrame, 
                   y_train: pd.Series,
                   X_val: pd.DataFrame = None,
                   y_val: pd.Series = None,
                   best_params: Dict = None) -> Any:
        """
        Train the final model
        
        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
            best_params: Best hyperparameters from optimization
            
        Returns:
            Trained model
        """
        self.logger.info("Training final model...")
        
        # Create model with best parameters
        if self.model_type == 'prophet':
            model_config = best_params if best_params else config.prophet.hyperparameters
            self.model = ManufacturingProphetModel(model_config=model_config)
        elif self.model_type == 'lstm':
            model_config = best_params if best_params else config.lstm.hyperparameters
            self.model = AttentionLSTMModel(model_config=model_config)
        elif self.model_type == 'ensemble':
            ensemble_config = best_params if best_params else config.ensemble.hyperparameters
            self.model = ManufacturingEnsembleModel(ensemble_config=ensemble_config)
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate on validation set if provided
        if X_val is not None and y_val is not None:
            val_predictions = self.model.predict(X_val)
            
            # Calculate validation metrics
            valid_mask = ~np.isnan(val_predictions) if hasattr(val_predictions, '__len__') else True
            if np.any(valid_mask):
                y_val_valid = y_val.values[valid_mask] if hasattr(val_predictions, '__len__') else y_val.values
                pred_valid = val_predictions[valid_mask] if hasattr(val_predictions, '__len__') else val_predictions
                
                val_metrics = {
                    'mae': mean_absolute_error(y_val_valid, pred_valid),
                    'rmse': np.sqrt(mean_squared_error(y_val_valid, pred_valid)),
                    'r2': r2_score(y_val_valid, pred_valid),
                    'mape': np.mean(np.abs((y_val_valid - pred_valid) / y_val_valid)) * 100
                }
                
                self.logger.info(f"Validation metrics:")
                for metric, value in val_metrics.items():
                    self.logger.info(f"  {metric.upper()}: {value:.4f}")
        
        self.logger.info("Model training completed")
        
        return self.model
    
    def evaluate_model(self, 
                      X_test: pd.DataFrame, 
                      y_test: pd.Series) -> Dict[str, float]:
        """
        Evaluate trained model on test set
        
        Args:
            X_test: Test features
            y_test: Test target
            
        Returns:
            Evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model must be trained before evaluation")
        
        self.logger.info("Evaluating model on test set...")
        
        # Make predictions
        predictions = self.model.predict(X_test)
        
        # Calculate metrics
        valid_mask = ~np.isnan(predictions) if hasattr(predictions, '__len__') else True
        if np.any(valid_mask):
            y_test_valid = y_test.values[valid_mask] if hasattr(predictions, '__len__') else y_test.values
            pred_valid = predictions[valid_mask] if hasattr(predictions, '__len__') else predictions
            
            metrics = {
                'mae': mean_absolute_error(y_test_valid, pred_valid),
                'mse': mean_squared_error(y_test_valid, pred_valid),
                'rmse': np.sqrt(mean_squared_error(y_test_valid, pred_valid)),
                'r2': r2_score(y_test_valid, pred_valid),
                'mape': np.mean(np.abs((y_test_valid - pred_valid) / y_test_valid)) * 100
            }
            
            # Additional metrics
            metrics['residual_mean'] = np.mean(y_test_valid - pred_valid)
            metrics['residual_std'] = np.std(y_test_valid - pred_valid)
            
            self.logger.info(f"Test set evaluation:")
            for metric, value in metrics.items():
                self.logger.info(f"  {metric.upper()}: {value:.4f}")
            
            self.evaluation_results = metrics
            
        return metrics
    
    def save_model(self, model_name: str = None):
        """Save trained model and pipeline components"""
        if self.model is None:
            raise ValueError("Model must be trained before saving")
        
        if model_name is None:
            model_name = f"{self.model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        model_path = self.output_dir / model_name
        
        # Save model
        self.model.save_model(str(model_path))
        
        # Save feature engine
        if self.feature_engine:
            joblib.dump(self.feature_engine, model_path.with_suffix('.feature_engine.pkl'))
        
        # Save pipeline results
        pipeline_results = {
            'model_type': self.model_type,
            'training_results': self.training_results,
            'evaluation_results': self.evaluation_results,
            'hyperparameter_results': self.hyperparameter_results,
            'timestamp': datetime.now().isoformat()
        }
        
        joblib.dump(pipeline_results, model_path.with_suffix('.pipeline_results.pkl'))
        
        self.logger.info(f"Model saved to {model_path}")
        
        return str(model_path)
    
    def run_full_pipeline(self, 
                         data: pd.DataFrame,
                         target_column: str,
                         model_name: str = None) -> Dict[str, Any]:
        """
        Run the complete training pipeline
        
        Args:
            data: Input data with datetime index
            target_column: Target column name
            model_name: Name for saved model
            
        Returns:
            Complete pipeline results
        """
        self.logger.info("Starting full ML training pipeline...")
        
        # Prepare data
        X_train, X_val, X_test, y_train, y_val, y_test = self.prepare_data(
            data, target_column
        )
        
        # Hyperparameter optimization
        best_params = self.hyperparameter_optimization(
            X_train, y_train, X_val, y_val
        )
        
        # Cross-validation
        cv_results = self.cross_validation(
            pd.concat([X_train, X_val]), 
            pd.concat([y_train, y_val])
        )
        
        # Train final model
        self.train_model(X_train, y_train, X_val, y_val, best_params)
        
        # Evaluate model
        test_metrics = self.evaluate_model(X_test, y_test)
        
        # Save model
        model_path = self.save_model(model_name)
        
        # Compile results
        results = {
            'model_type': self.model_type,
            'model_path': model_path,
            'best_hyperparameters': best_params,
            'cross_validation_results': cv_results,
            'test_metrics': test_metrics,
            'data_info': {
                'train_size': len(X_train),
                'val_size': len(X_val),
                'test_size': len(X_test),
                'n_features': len(X_train.columns),
                'target_column': target_column
            },
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info("Full pipeline completed successfully!")
        
        return results