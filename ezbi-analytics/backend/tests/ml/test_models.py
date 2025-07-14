"""
Tests for ML models and prediction functionality.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import joblib
import tempfile
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import tensorflow as tf

# Import ML components
from ml_engine.models.lstm.lstm_attention_model import LSTMAttentionModel
from ml_engine.models.prophet.prophet_model import ProphetModel
from ml_engine.models.ensemble.ensemble_model import EnsembleModel
from ml_engine.features.manufacturing_features import ManufacturingFeatureExtractor
from ml_engine.training.ml_training_pipeline import MLTrainingPipeline
from ml_engine.inference.inference_server import InferenceServer
from ml_engine.monitoring.model_monitor import ModelMonitor
from ml_engine.utils.data_preprocessor import DataPreprocessor
from ml_engine.utils.feature_validator import FeatureValidator


class TestLSTMAttentionModel:
    """Test LSTM Attention model functionality."""
    
    def test_model_initialization(self):
        """Test LSTM model initialization."""
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=64,
            attention_units=32,
            dropout_rate=0.2
        )
        
        assert model.input_shape == (30, 10)
        assert model.hidden_units == 64
        assert model.attention_units == 32
        assert model.dropout_rate == 0.2
        assert model.model is None  # Not built yet
    
    def test_model_building(self):
        """Test LSTM model building."""
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=64,
            attention_units=32
        )
        
        model.build_model()
        
        assert model.model is not None
        assert len(model.model.layers) > 0
        
        # Check model architecture
        assert model.model.input_shape == (None, 30, 10)
        assert model.model.output_shape == (None, 1)
    
    def test_model_compilation(self):
        """Test model compilation."""
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=64,
            attention_units=32
        )
        
        model.build_model()
        model.compile_model(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        assert model.model.optimizer is not None
        assert model.model.loss == 'mse'
        assert 'mae' in [m.name for m in model.model.metrics]
    
    def test_model_training(self):
        """Test model training."""
        # Generate sample data
        X_train = np.random.random((1000, 30, 10))
        y_train = np.random.random((1000, 1))
        X_val = np.random.random((200, 30, 10))
        y_val = np.random.random((200, 1))
        
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=32,
            attention_units=16
        )
        
        model.build_model()
        model.compile_model()
        
        # Train model
        history = model.train(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=2,
            batch_size=32,
            verbose=0
        )
        
        assert 'loss' in history.history
        assert 'val_loss' in history.history
        assert len(history.history['loss']) == 2
    
    def test_model_prediction(self):
        """Test model prediction."""
        # Generate sample data
        X_test = np.random.random((100, 30, 10))
        
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=32,
            attention_units=16
        )
        
        model.build_model()
        model.compile_model()
        
        # Make predictions
        predictions = model.predict(X_test)
        
        assert predictions.shape == (100, 1)
        assert isinstance(predictions, np.ndarray)
    
    def test_model_saving_loading(self):
        """Test model saving and loading."""
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=32,
            attention_units=16
        )
        
        model.build_model()
        model.compile_model()
        
        # Save model
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_model.h5")
            model.save_model(model_path)
            
            assert os.path.exists(model_path)
            
            # Load model
            loaded_model = LSTMAttentionModel(
                input_shape=(30, 10),
                hidden_units=32,
                attention_units=16
            )
            
            loaded_model.load_model(model_path)
            
            assert loaded_model.model is not None
            assert loaded_model.model.input_shape == (None, 30, 10)
    
    def test_attention_mechanism(self):
        """Test attention mechanism functionality."""
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=32,
            attention_units=16
        )
        
        model.build_model()
        
        # Check that attention layer exists
        attention_layers = [layer for layer in model.model.layers if 'attention' in layer.name.lower()]
        assert len(attention_layers) > 0
        
        # Test attention weights extraction
        X_test = np.random.random((1, 30, 10))
        attention_weights = model.get_attention_weights(X_test)
        
        assert attention_weights is not None
        assert attention_weights.shape[1] == 30  # Sequence length
    
    def test_model_evaluation(self):
        """Test model evaluation."""
        # Generate sample data
        X_test = np.random.random((100, 30, 10))
        y_test = np.random.random((100, 1))
        
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=32,
            attention_units=16
        )
        
        model.build_model()
        model.compile_model()
        
        # Evaluate model
        metrics = model.evaluate(X_test, y_test)
        
        assert 'loss' in metrics
        assert 'mae' in metrics
        assert isinstance(metrics['loss'], float)
        assert isinstance(metrics['mae'], float)
    
    def test_manufacturing_specific_features(self):
        """Test manufacturing-specific model features."""
        # Features: revenue, expenses, production_volume, inventory, etc.
        manufacturing_features = [
            'revenue', 'expenses', 'production_volume', 'inventory',
            'raw_materials_cost', 'labor_cost', 'overhead_cost',
            'seasonal_factor', 'market_demand', 'supply_chain_index'
        ]
        
        model = LSTMAttentionModel(
            input_shape=(30, len(manufacturing_features)),
            hidden_units=64,
            attention_units=32,
            feature_names=manufacturing_features
        )
        
        model.build_model()
        
        assert model.feature_names == manufacturing_features
        assert model.input_shape[1] == len(manufacturing_features)
    
    def test_model_hyperparameter_tuning(self):
        """Test hyperparameter tuning capabilities."""
        hyperparameters = {
            'hidden_units': [32, 64, 128],
            'attention_units': [16, 32, 64],
            'dropout_rate': [0.1, 0.2, 0.3],
            'learning_rate': [0.001, 0.01, 0.1]
        }
        
        best_params = LSTMAttentionModel.tune_hyperparameters(
            hyperparameters=hyperparameters,
            X_train=np.random.random((1000, 30, 10)),
            y_train=np.random.random((1000, 1)),
            X_val=np.random.random((200, 30, 10)),
            y_val=np.random.random((200, 1)),
            trials=3  # Reduced for testing
        )
        
        assert 'hidden_units' in best_params
        assert 'attention_units' in best_params
        assert 'dropout_rate' in best_params
        assert 'learning_rate' in best_params


class TestProphetModel:
    """Test Prophet model functionality."""
    
    def test_model_initialization(self):
        """Test Prophet model initialization."""
        model = ProphetModel(
            growth='linear',
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode='additive'
        )
        
        assert model.growth == 'linear'
        assert model.yearly_seasonality is True
        assert model.weekly_seasonality is False
        assert model.daily_seasonality is False
        assert model.seasonality_mode == 'additive'
    
    def test_model_training(self):
        """Test Prophet model training."""
        # Generate sample time series data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        values = np.random.randn(365).cumsum() + 1000
        
        df = pd.DataFrame({
            'ds': dates,
            'y': values
        })
        
        model = ProphetModel()
        model.fit(df)
        
        assert model.model is not None
        assert hasattr(model.model, 'predict')
    
    def test_model_prediction(self):
        """Test Prophet model prediction."""
        # Generate sample data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        values = np.random.randn(365).cumsum() + 1000
        
        df = pd.DataFrame({
            'ds': dates,
            'y': values
        })
        
        model = ProphetModel()
        model.fit(df)
        
        # Make future predictions
        future_dates = model.make_future_dataframe(periods=30)
        predictions = model.predict(future_dates)
        
        assert 'yhat' in predictions.columns
        assert 'yhat_lower' in predictions.columns
        assert 'yhat_upper' in predictions.columns
        assert len(predictions) == len(df) + 30
    
    def test_manufacturing_seasonality(self):
        """Test manufacturing-specific seasonality."""
        model = ProphetModel(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False
        )
        
        # Add manufacturing-specific seasonality
        model.add_manufacturing_seasonality()
        
        # Generate sample data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        values = np.random.randn(365).cumsum() + 1000
        
        df = pd.DataFrame({
            'ds': dates,
            'y': values
        })
        
        model.fit(df)
        
        # Check that custom seasonality was added
        assert 'manufacturing_peak' in model.model.seasonalities
        assert 'french_holidays' in model.model.seasonalities
    
    def test_external_regressors(self):
        """Test external regressors functionality."""
        # Generate sample data with regressors
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        values = np.random.randn(365).cumsum() + 1000
        production_volume = np.random.randint(800, 1200, 365)
        market_demand = np.random.normal(1.0, 0.1, 365)
        
        df = pd.DataFrame({
            'ds': dates,
            'y': values,
            'production_volume': production_volume,
            'market_demand': market_demand
        })
        
        model = ProphetModel()
        model.add_regressor('production_volume')
        model.add_regressor('market_demand')
        
        model.fit(df)
        
        # Make predictions with regressors
        future_df = model.make_future_dataframe(periods=30)
        future_df['production_volume'] = np.random.randint(800, 1200, len(future_df))
        future_df['market_demand'] = np.random.normal(1.0, 0.1, len(future_df))
        
        predictions = model.predict(future_df)
        
        assert 'yhat' in predictions.columns
        assert len(predictions) == len(future_df)
    
    def test_french_holidays_integration(self):
        """Test French holidays integration."""
        model = ProphetModel()
        model.add_french_holidays()
        
        # Generate sample data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        values = np.random.randn(365).cumsum() + 1000
        
        df = pd.DataFrame({
            'ds': dates,
            'y': values
        })
        
        model.fit(df)
        
        # Check that French holidays were added
        assert model.model.holidays is not None
        assert len(model.model.holidays) > 0
        
        # Check for specific French holidays
        holiday_names = model.model.holidays['holiday'].unique()
        assert 'Nouvel An' in holiday_names
        assert 'Fête du Travail' in holiday_names
        assert 'Fête Nationale' in holiday_names
    
    def test_model_evaluation(self):
        """Test model evaluation metrics."""
        # Generate sample data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        values = np.random.randn(365).cumsum() + 1000
        
        df = pd.DataFrame({
            'ds': dates,
            'y': values
        })
        
        # Split data
        train_df = df.iloc[:300]
        test_df = df.iloc[300:]
        
        model = ProphetModel()
        model.fit(train_df)
        
        # Predict on test data
        test_predictions = model.predict(test_df[['ds']])
        
        # Calculate metrics
        mae = mean_absolute_error(test_df['y'], test_predictions['yhat'])
        mse = mean_squared_error(test_df['y'], test_predictions['yhat'])
        rmse = np.sqrt(mse)
        
        assert mae > 0
        assert mse > 0
        assert rmse > 0
        assert isinstance(mae, float)
        assert isinstance(mse, float)
        assert isinstance(rmse, float)
    
    def test_cross_validation(self):
        """Test cross-validation functionality."""
        # Generate sample data
        dates = pd.date_range('2020-01-01', periods=1000, freq='D')
        values = np.random.randn(1000).cumsum() + 1000
        
        df = pd.DataFrame({
            'ds': dates,
            'y': values
        })
        
        model = ProphetModel()
        
        # Perform cross-validation
        cv_results = model.cross_validation(
            df,
            initial='730 days',
            period='30 days',
            horizon='30 days'
        )
        
        assert 'ds' in cv_results.columns
        assert 'yhat' in cv_results.columns
        assert 'y' in cv_results.columns
        assert len(cv_results) > 0
        
        # Calculate performance metrics
        performance = model.performance_metrics(cv_results)
        
        assert 'mse' in performance.columns
        assert 'rmse' in performance.columns
        assert 'mae' in performance.columns
        assert 'mape' in performance.columns


class TestEnsembleModel:
    """Test Ensemble model functionality."""
    
    def test_ensemble_initialization(self):
        """Test ensemble model initialization."""
        models = {
            'lstm': Mock(),
            'prophet': Mock(),
            'linear': Mock()
        }
        
        ensemble = EnsembleModel(
            models=models,
            weights=[0.5, 0.3, 0.2],
            voting_method='weighted'
        )
        
        assert len(ensemble.models) == 3
        assert ensemble.weights == [0.5, 0.3, 0.2]
        assert ensemble.voting_method == 'weighted'
    
    def test_ensemble_training(self):
        """Test ensemble model training."""
        # Mock individual models
        lstm_model = Mock()
        prophet_model = Mock()
        linear_model = Mock()
        
        models = {
            'lstm': lstm_model,
            'prophet': prophet_model,
            'linear': linear_model
        }
        
        ensemble = EnsembleModel(models=models)
        
        # Mock training data
        X_train = np.random.random((1000, 30, 10))
        y_train = np.random.random((1000, 1))
        
        ensemble.fit(X_train, y_train)
        
        # Verify all models were trained
        lstm_model.fit.assert_called_once()
        prophet_model.fit.assert_called_once()
        linear_model.fit.assert_called_once()
    
    def test_ensemble_prediction(self):
        """Test ensemble model prediction."""
        # Mock individual models with predictions
        lstm_model = Mock()
        lstm_model.predict.return_value = np.array([[100], [110], [120]])
        
        prophet_model = Mock()
        prophet_model.predict.return_value = np.array([[95], [105], [115]])
        
        linear_model = Mock()
        linear_model.predict.return_value = np.array([[105], [115], [125]])
        
        models = {
            'lstm': lstm_model,
            'prophet': prophet_model,
            'linear': linear_model
        }
        
        ensemble = EnsembleModel(
            models=models,
            weights=[0.5, 0.3, 0.2],
            voting_method='weighted'
        )
        
        X_test = np.random.random((3, 30, 10))
        predictions = ensemble.predict(X_test)
        
        # Check weighted average
        expected_0 = 100 * 0.5 + 95 * 0.3 + 105 * 0.2
        expected_1 = 110 * 0.5 + 105 * 0.3 + 115 * 0.2
        expected_2 = 120 * 0.5 + 115 * 0.3 + 125 * 0.2
        
        assert np.isclose(predictions[0], expected_0)
        assert np.isclose(predictions[1], expected_1)
        assert np.isclose(predictions[2], expected_2)
    
    def test_ensemble_weight_optimization(self):
        """Test ensemble weight optimization."""
        # Mock models with different performance
        models = {
            'lstm': Mock(),
            'prophet': Mock(),
            'linear': Mock()
        }
        
        # Mock validation predictions
        lstm_preds = np.array([[100], [110], [120], [130]])
        prophet_preds = np.array([[95], [105], [115], [125]])
        linear_preds = np.array([[105], [115], [125], [135]])
        
        models['lstm'].predict.return_value = lstm_preds
        models['prophet'].predict.return_value = prophet_preds
        models['linear'].predict.return_value = linear_preds
        
        ensemble = EnsembleModel(models=models)
        
        # Mock validation data
        X_val = np.random.random((4, 30, 10))
        y_val = np.array([[98], [108], [118], [128]])
        
        # Optimize weights
        ensemble.optimize_weights(X_val, y_val)
        
        # Check that weights were updated
        assert ensemble.weights is not None
        assert len(ensemble.weights) == 3
        assert abs(sum(ensemble.weights) - 1.0) < 0.01  # Should sum to 1
    
    def test_ensemble_confidence_intervals(self):
        """Test ensemble confidence interval calculation."""
        # Mock models with different predictions
        models = {
            'lstm': Mock(),
            'prophet': Mock(),
            'linear': Mock()
        }
        
        models['lstm'].predict.return_value = np.array([[100], [110], [120]])
        models['prophet'].predict.return_value = np.array([[95], [105], [115]])
        models['linear'].predict.return_value = np.array([[105], [115], [125]])
        
        ensemble = EnsembleModel(models=models)
        
        X_test = np.random.random((3, 30, 10))
        predictions, confidence = ensemble.predict_with_confidence(X_test)
        
        assert len(predictions) == 3
        assert len(confidence) == 3
        assert 'lower' in confidence
        assert 'upper' in confidence
        assert 'std' in confidence
    
    def test_ensemble_model_selection(self):
        """Test automatic model selection."""
        # Mock training data
        X_train = np.random.random((1000, 30, 10))
        y_train = np.random.random((1000, 1))
        X_val = np.random.random((200, 30, 10))
        y_val = np.random.random((200, 1))
        
        # Available model types
        model_types = ['lstm', 'prophet', 'linear_regression', 'random_forest']
        
        ensemble = EnsembleModel.auto_select_models(
            X_train, y_train, X_val, y_val,
            model_types=model_types,
            max_models=3
        )
        
        assert len(ensemble.models) <= 3
        assert ensemble.weights is not None
        assert len(ensemble.weights) == len(ensemble.models)
    
    def test_ensemble_feature_importance(self):
        """Test ensemble feature importance calculation."""
        # Mock models with feature importance
        models = {
            'lstm': Mock(),
            'prophet': Mock(),
            'random_forest': Mock()
        }
        
        # Mock feature importance
        models['lstm'].get_feature_importance.return_value = np.array([0.3, 0.2, 0.1, 0.4])
        models['prophet'].get_feature_importance.return_value = np.array([0.2, 0.3, 0.2, 0.3])
        models['random_forest'].feature_importances_ = np.array([0.25, 0.25, 0.25, 0.25])
        
        ensemble = EnsembleModel(
            models=models,
            weights=[0.4, 0.3, 0.3]
        )
        
        feature_importance = ensemble.get_feature_importance()
        
        assert len(feature_importance) == 4
        assert abs(sum(feature_importance) - 1.0) < 0.01
        assert isinstance(feature_importance, np.ndarray)


class TestManufacturingFeatureExtractor:
    """Test manufacturing feature extraction."""
    
    def test_feature_extractor_initialization(self):
        """Test feature extractor initialization."""
        extractor = ManufacturingFeatureExtractor(
            time_features=True,
            seasonal_features=True,
            lag_features=True,
            rolling_features=True
        )
        
        assert extractor.time_features is True
        assert extractor.seasonal_features is True
        assert extractor.lag_features is True
        assert extractor.rolling_features is True
    
    def test_time_features_extraction(self):
        """Test time-based feature extraction."""
        # Generate sample financial data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'revenue': np.random.randn(365) * 1000 + 150000,
            'expenses': np.random.randn(365) * 800 + 112500,
            'cash_flow': np.random.randn(365) * 500 + 37500
        })
        
        extractor = ManufacturingFeatureExtractor(time_features=True)
        features = extractor.extract_time_features(df)
        
        assert 'year' in features.columns
        assert 'month' in features.columns
        assert 'day_of_week' in features.columns
        assert 'day_of_year' in features.columns
        assert 'quarter' in features.columns
        assert 'is_weekend' in features.columns
        assert 'is_month_end' in features.columns
        assert 'is_quarter_end' in features.columns
    
    def test_seasonal_features_extraction(self):
        """Test seasonal feature extraction."""
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'revenue': np.random.randn(365) * 1000 + 150000
        })
        
        extractor = ManufacturingFeatureExtractor(seasonal_features=True)
        features = extractor.extract_seasonal_features(df)
        
        assert 'seasonal_revenue' in features.columns
        assert 'trend_revenue' in features.columns
        assert 'residual_revenue' in features.columns
        assert 'seasonal_strength' in features.columns
    
    def test_lag_features_extraction(self):
        """Test lag feature extraction."""
        df = pd.DataFrame({
            'revenue': np.random.randn(100) * 1000 + 150000,
            'expenses': np.random.randn(100) * 800 + 112500,
            'cash_flow': np.random.randn(100) * 500 + 37500
        })
        
        extractor = ManufacturingFeatureExtractor(lag_features=True)
        features = extractor.extract_lag_features(df, lags=[1, 7, 30])
        
        assert 'revenue_lag_1' in features.columns
        assert 'revenue_lag_7' in features.columns
        assert 'revenue_lag_30' in features.columns
        assert 'expenses_lag_1' in features.columns
        assert 'cash_flow_lag_1' in features.columns
    
    def test_rolling_features_extraction(self):
        """Test rolling window feature extraction."""
        df = pd.DataFrame({
            'revenue': np.random.randn(100) * 1000 + 150000,
            'expenses': np.random.randn(100) * 800 + 112500,
            'cash_flow': np.random.randn(100) * 500 + 37500
        })
        
        extractor = ManufacturingFeatureExtractor(rolling_features=True)
        features = extractor.extract_rolling_features(df, windows=[7, 30])
        
        assert 'revenue_rolling_mean_7' in features.columns
        assert 'revenue_rolling_std_7' in features.columns
        assert 'revenue_rolling_mean_30' in features.columns
        assert 'expenses_rolling_mean_7' in features.columns
        assert 'cash_flow_rolling_mean_7' in features.columns
    
    def test_manufacturing_specific_features(self):
        """Test manufacturing-specific feature extraction."""
        df = pd.DataFrame({
            'revenue': np.random.randn(100) * 1000 + 150000,
            'expenses': np.random.randn(100) * 800 + 112500,
            'production_volume': np.random.randint(800, 1200, 100),
            'inventory': np.random.randn(100) * 5000 + 37500,
            'raw_materials_cost': np.random.randn(100) * 2000 + 52500,
            'labor_cost': np.random.randn(100) * 1500 + 37500
        })
        
        extractor = ManufacturingFeatureExtractor()
        features = extractor.extract_manufacturing_features(df)
        
        assert 'cost_per_unit' in features.columns
        assert 'profit_margin' in features.columns
        assert 'inventory_turnover' in features.columns
        assert 'labor_efficiency' in features.columns
        assert 'material_efficiency' in features.columns
        assert 'capacity_utilization' in features.columns
    
    def test_french_business_features(self):
        """Test French business-specific features."""
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'revenue': np.random.randn(365) * 1000 + 150000
        })
        
        extractor = ManufacturingFeatureExtractor()
        features = extractor.extract_french_business_features(df)
        
        assert 'is_french_holiday' in features.columns
        assert 'is_vacation_period' in features.columns  # July, August
        assert 'is_back_to_school' in features.columns    # September
        assert 'is_year_end' in features.columns          # December
        assert 'working_days_in_month' in features.columns
    
    def test_feature_validation(self):
        """Test feature validation."""
        # Create features with some invalid values
        features = pd.DataFrame({
            'revenue': [150000, np.inf, 160000, -50000],
            'expenses': [112500, 120000, np.nan, 125000],
            'cash_flow': [37500, 40000, 35000, 38000],
            'production_volume': [1200, 1300, 1100, 0]
        })
        
        extractor = ManufacturingFeatureExtractor()
        validated_features = extractor.validate_features(features)
        
        # Check that invalid values were handled
        assert not np.any(np.isinf(validated_features['revenue']))
        assert not np.any(np.isnan(validated_features['expenses']))
        assert not np.any(validated_features['revenue'] < 0)
        assert not np.any(validated_features['production_volume'] <= 0)
    
    def test_feature_scaling(self):
        """Test feature scaling."""
        features = pd.DataFrame({
            'revenue': np.random.randn(100) * 1000 + 150000,
            'expenses': np.random.randn(100) * 800 + 112500,
            'production_volume': np.random.randint(800, 1200, 100)
        })
        
        extractor = ManufacturingFeatureExtractor()
        scaled_features = extractor.scale_features(features)
        
        # Check that features are scaled (mean ≈ 0, std ≈ 1)
        assert abs(scaled_features['revenue'].mean()) < 0.1
        assert abs(scaled_features['revenue'].std() - 1.0) < 0.1
        assert abs(scaled_features['expenses'].mean()) < 0.1
        assert abs(scaled_features['expenses'].std() - 1.0) < 0.1
    
    def test_complete_feature_pipeline(self):
        """Test complete feature extraction pipeline."""
        # Generate comprehensive sample data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'revenue': np.random.randn(365) * 1000 + 150000,
            'expenses': np.random.randn(365) * 800 + 112500,
            'production_volume': np.random.randint(800, 1200, 365),
            'inventory': np.random.randn(365) * 5000 + 37500,
            'raw_materials_cost': np.random.randn(365) * 2000 + 52500,
            'labor_cost': np.random.randn(365) * 1500 + 37500
        })
        
        extractor = ManufacturingFeatureExtractor(
            time_features=True,
            seasonal_features=True,
            lag_features=True,
            rolling_features=True
        )
        
        # Extract all features
        all_features = extractor.extract_all_features(df)
        
        # Check that all feature types are present
        assert 'year' in all_features.columns  # Time features
        assert 'seasonal_revenue' in all_features.columns  # Seasonal features
        assert 'revenue_lag_1' in all_features.columns  # Lag features
        assert 'revenue_rolling_mean_7' in all_features.columns  # Rolling features
        assert 'cost_per_unit' in all_features.columns  # Manufacturing features
        assert 'is_french_holiday' in all_features.columns  # French business features
        
        # Check feature count
        assert len(all_features.columns) > 20  # Should have many features
        assert len(all_features) == len(df)  # Should have same number of rows


class TestMLTrainingPipeline:
    """Test ML training pipeline."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = MLTrainingPipeline(
            model_type='lstm',
            feature_extractor=ManufacturingFeatureExtractor(),
            validation_split=0.2,
            test_split=0.1
        )
        
        assert pipeline.model_type == 'lstm'
        assert pipeline.validation_split == 0.2
        assert pipeline.test_split == 0.1
        assert pipeline.feature_extractor is not None
    
    def test_data_preprocessing(self):
        """Test data preprocessing."""
        # Generate sample data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'revenue': np.random.randn(365) * 1000 + 150000,
            'expenses': np.random.randn(365) * 800 + 112500,
            'cash_flow': np.random.randn(365) * 500 + 37500
        })
        
        pipeline = MLTrainingPipeline(
            model_type='lstm',
            feature_extractor=ManufacturingFeatureExtractor()
        )
        
        processed_data = pipeline.preprocess_data(df)
        
        assert 'features' in processed_data
        assert 'target' in processed_data
        assert 'dates' in processed_data
        assert len(processed_data['features']) == len(df)
    
    def test_train_test_split(self):
        """Test train/test split functionality."""
        # Generate sample data
        X = np.random.random((1000, 30, 10))
        y = np.random.random((1000, 1))
        
        pipeline = MLTrainingPipeline(
            model_type='lstm',
            validation_split=0.2,
            test_split=0.1
        )
        
        splits = pipeline.train_test_split(X, y)
        
        assert 'X_train' in splits
        assert 'X_val' in splits
        assert 'X_test' in splits
        assert 'y_train' in splits
        assert 'y_val' in splits
        assert 'y_test' in splits
        
        # Check split sizes
        assert len(splits['X_train']) == 700  # 70% of 1000
        assert len(splits['X_val']) == 200   # 20% of 1000
        assert len(splits['X_test']) == 100  # 10% of 1000
    
    def test_model_training(self):
        """Test model training."""
        # Generate sample data
        X = np.random.random((1000, 30, 10))
        y = np.random.random((1000, 1))
        
        pipeline = MLTrainingPipeline(
            model_type='lstm',
            feature_extractor=ManufacturingFeatureExtractor()
        )
        
        trained_model = pipeline.train_model(X, y)
        
        assert trained_model is not None
        assert hasattr(trained_model, 'predict')
    
    def test_model_evaluation(self):
        """Test model evaluation."""
        # Generate sample data
        X_test = np.random.random((200, 30, 10))
        y_test = np.random.random((200, 1))
        
        # Mock trained model
        model = Mock()
        model.predict.return_value = np.random.random((200, 1))
        
        pipeline = MLTrainingPipeline(
            model_type='lstm',
            feature_extractor=ManufacturingFeatureExtractor()
        )
        
        metrics = pipeline.evaluate_model(model, X_test, y_test)
        
        assert 'mae' in metrics
        assert 'mse' in metrics
        assert 'rmse' in metrics
        assert 'r2' in metrics
        assert 'mape' in metrics
    
    def test_hyperparameter_tuning(self):
        """Test hyperparameter tuning."""
        # Generate sample data
        X = np.random.random((1000, 30, 10))
        y = np.random.random((1000, 1))
        
        hyperparameters = {
            'hidden_units': [32, 64],
            'learning_rate': [0.001, 0.01],
            'dropout_rate': [0.1, 0.2]
        }
        
        pipeline = MLTrainingPipeline(
            model_type='lstm',
            feature_extractor=ManufacturingFeatureExtractor()
        )
        
        best_params = pipeline.tune_hyperparameters(X, y, hyperparameters)
        
        assert 'hidden_units' in best_params
        assert 'learning_rate' in best_params
        assert 'dropout_rate' in best_params
    
    def test_model_persistence(self):
        """Test model saving and loading."""
        # Generate sample data
        X = np.random.random((100, 30, 10))
        y = np.random.random((100, 1))
        
        pipeline = MLTrainingPipeline(
            model_type='lstm',
            feature_extractor=ManufacturingFeatureExtractor()
        )
        
        # Train model
        model = pipeline.train_model(X, y)
        
        # Save model
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_model")
            pipeline.save_model(model, model_path)
            
            # Load model
            loaded_model = pipeline.load_model(model_path)
            
            assert loaded_model is not None
            
            # Test predictions are similar
            X_test = np.random.random((10, 30, 10))
            original_pred = model.predict(X_test)
            loaded_pred = loaded_model.predict(X_test)
            
            assert np.allclose(original_pred, loaded_pred, rtol=1e-5)
    
    def test_cross_validation(self):
        """Test cross-validation."""
        # Generate sample data
        X = np.random.random((1000, 30, 10))
        y = np.random.random((1000, 1))
        
        pipeline = MLTrainingPipeline(
            model_type='lstm',
            feature_extractor=ManufacturingFeatureExtractor()
        )
        
        cv_scores = pipeline.cross_validate(X, y, cv_folds=3)
        
        assert 'mae_scores' in cv_scores
        assert 'mse_scores' in cv_scores
        assert 'r2_scores' in cv_scores
        assert len(cv_scores['mae_scores']) == 3
        assert len(cv_scores['mse_scores']) == 3
        assert len(cv_scores['r2_scores']) == 3
    
    def test_manufacturing_specific_validation(self):
        """Test manufacturing-specific validation."""
        # Generate sample manufacturing data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'revenue': np.random.randn(365) * 1000 + 150000,
            'expenses': np.random.randn(365) * 800 + 112500,
            'production_volume': np.random.randint(800, 1200, 365),
            'inventory': np.random.randn(365) * 5000 + 37500,
            'cash_flow': np.random.randn(365) * 500 + 37500
        })
        
        pipeline = MLTrainingPipeline(
            model_type='lstm',
            feature_extractor=ManufacturingFeatureExtractor()
        )
        
        # Validate manufacturing constraints
        validation_results = pipeline.validate_manufacturing_constraints(df)
        
        assert 'revenue_consistency' in validation_results
        assert 'production_correlation' in validation_results
        assert 'seasonal_patterns' in validation_results
        assert 'data_quality' in validation_results


class TestModelMonitor:
    """Test model monitoring functionality."""
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = ModelMonitor(
            model_name='lstm_cash_flow',
            monitoring_window=30,
            alert_threshold=0.1
        )
        
        assert monitor.model_name == 'lstm_cash_flow'
        assert monitor.monitoring_window == 30
        assert monitor.alert_threshold == 0.1
    
    def test_performance_monitoring(self):
        """Test performance monitoring."""
        monitor = ModelMonitor(
            model_name='test_model',
            monitoring_window=30
        )
        
        # Simulate predictions and actuals
        predictions = np.random.random(100)
        actuals = np.random.random(100)
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        
        # Log performance
        for i, (pred, actual, date) in enumerate(zip(predictions, actuals, dates)):
            monitor.log_prediction(pred, actual, date)
        
        # Get performance metrics
        metrics = monitor.get_performance_metrics()
        
        assert 'mae' in metrics
        assert 'mse' in metrics
        assert 'rmse' in metrics
        assert 'r2' in metrics
        assert 'accuracy_trend' in metrics
    
    def test_drift_detection(self):
        """Test data drift detection."""
        monitor = ModelMonitor(
            model_name='test_model',
            monitoring_window=30
        )
        
        # Simulate reference data (training data distribution)
        reference_data = np.random.normal(0, 1, (1000, 10))
        monitor.set_reference_data(reference_data)
        
        # Simulate current data (potentially drifted)
        current_data = np.random.normal(0.5, 1.2, (100, 10))  # Slightly drifted
        
        # Detect drift
        drift_results = monitor.detect_drift(current_data)
        
        assert 'drift_detected' in drift_results
        assert 'drift_score' in drift_results
        assert 'drift_features' in drift_results
        assert isinstance(drift_results['drift_detected'], bool)
    
    def test_model_degradation_detection(self):
        """Test model degradation detection."""
        monitor = ModelMonitor(
            model_name='test_model',
            monitoring_window=30,
            alert_threshold=0.1
        )
        
        # Simulate initial good performance
        for i in range(30):
            pred = np.random.normal(100, 5)
            actual = np.random.normal(100, 5)  # Good predictions
            date = datetime.now() - timedelta(days=30-i)
            monitor.log_prediction(pred, actual, date)
        
        # Simulate degrading performance
        for i in range(30):
            pred = np.random.normal(100, 5)
            actual = np.random.normal(120, 10)  # Degraded predictions
            date = datetime.now() - timedelta(days=30-i)
            monitor.log_prediction(pred, actual, date)
        
        # Check for degradation
        degradation_results = monitor.detect_degradation()
        
        assert 'degradation_detected' in degradation_results
        assert 'performance_change' in degradation_results
        assert 'confidence' in degradation_results
    
    def test_alert_generation(self):
        """Test alert generation."""
        monitor = ModelMonitor(
            model_name='test_model',
            monitoring_window=30,
            alert_threshold=0.1
        )
        
        # Simulate poor performance that should trigger alert
        for i in range(30):
            pred = np.random.normal(100, 5)
            actual = np.random.normal(150, 10)  # Very poor predictions
            date = datetime.now() - timedelta(days=30-i)
            monitor.log_prediction(pred, actual, date)
        
        # Check alerts
        alerts = monitor.get_active_alerts()
        
        assert len(alerts) > 0
        assert 'alert_type' in alerts[0]
        assert 'severity' in alerts[0]
        assert 'message' in alerts[0]
        assert 'timestamp' in alerts[0]
    
    def test_manufacturing_specific_monitoring(self):
        """Test manufacturing-specific monitoring."""
        monitor = ModelMonitor(
            model_name='manufacturing_model',
            monitoring_window=30
        )
        
        # Simulate manufacturing data
        manufacturing_data = {
            'production_volume': np.random.randint(800, 1200, 30),
            'inventory_levels': np.random.randint(30000, 50000, 30),
            'quality_metrics': np.random.uniform(0.95, 0.99, 30),
            'machine_efficiency': np.random.uniform(0.85, 0.95, 30)
        }
        
        # Monitor manufacturing metrics
        manufacturing_alerts = monitor.monitor_manufacturing_metrics(manufacturing_data)
        
        assert 'production_alerts' in manufacturing_alerts
        assert 'inventory_alerts' in manufacturing_alerts
        assert 'quality_alerts' in manufacturing_alerts
        assert 'efficiency_alerts' in manufacturing_alerts
    
    def test_report_generation(self):
        """Test monitoring report generation."""
        monitor = ModelMonitor(
            model_name='test_model',
            monitoring_window=30
        )
        
        # Simulate some monitoring data
        for i in range(30):
            pred = np.random.normal(100, 5)
            actual = np.random.normal(100, 5)
            date = datetime.now() - timedelta(days=30-i)
            monitor.log_prediction(pred, actual, date)
        
        # Generate report
        report = monitor.generate_monitoring_report()
        
        assert 'model_info' in report
        assert 'performance_summary' in report
        assert 'alerts_summary' in report
        assert 'recommendations' in report
        assert 'monitoring_period' in report
    
    def test_real_time_monitoring(self):
        """Test real-time monitoring capabilities."""
        monitor = ModelMonitor(
            model_name='real_time_model',
            monitoring_window=30
        )
        
        # Simulate real-time prediction
        current_prediction = 125.5
        expected_range = (120, 130)
        
        # Check if prediction is within expected range
        anomaly_detected = monitor.check_prediction_anomaly(
            current_prediction, expected_range
        )
        
        assert isinstance(anomaly_detected, bool)
        
        # Log real-time prediction
        monitor.log_real_time_prediction(current_prediction)
        
        # Get real-time metrics
        real_time_metrics = monitor.get_real_time_metrics()
        
        assert 'current_performance' in real_time_metrics
        assert 'prediction_count' in real_time_metrics
        assert 'anomaly_count' in real_time_metrics