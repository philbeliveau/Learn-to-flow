"""
LSTM with Attention Mechanism for Manufacturing Forecasting
Advanced neural network model for complex time series patterns
"""

import tensorflow as tf
from tensorflow.keras.layers import (
    LSTM, Dense, Dropout, LayerNormalization, 
    MultiHeadAttention, GlobalAveragePooling1D, 
    Bidirectional, Input, Concatenate
)
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, 
    ModelCheckpoint, TensorBoard
)
from tensorflow.keras.regularizers import l1_l2
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging
import joblib
from datetime import datetime
import os

from config.ml_config import config

class AttentionLSTMModel(BaseEstimator, RegressorMixin):
    """LSTM model with attention mechanism for manufacturing forecasting"""
    
    def __init__(self, 
                 model_config: Optional[Dict] = None,
                 use_attention: bool = True,
                 use_bidirectional: bool = True,
                 use_layer_norm: bool = True):
        """
        Initialize LSTM with Attention Model
        
        Args:
            model_config: LSTM model configuration
            use_attention: Include attention mechanism
            use_bidirectional: Use bidirectional LSTM
            use_layer_norm: Use layer normalization
        """
        self.model_config = model_config or config.lstm.hyperparameters
        self.use_attention = use_attention
        self.use_bidirectional = use_bidirectional
        self.use_layer_norm = use_layer_norm
        
        # Model components
        self.model = None
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.is_fitted = False
        
        # Training history
        self.history = None
        self.performance_metrics = {}
        
        # Model parameters
        self.sequence_length = self.model_config.get('sequence_length', 60)
        self.hidden_dim = self.model_config.get('hidden_dim', 128)
        self.num_layers = self.model_config.get('num_layers', 3)
        self.dropout = self.model_config.get('dropout', 0.2)
        self.attention_dim = self.model_config.get('attention_dim', 64)
        self.batch_size = self.model_config.get('batch_size', 32)
        self.learning_rate = self.model_config.get('learning_rate', 0.001)
        self.epochs = self.model_config.get('epochs', 100)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _create_sequences(self, X: np.ndarray, y: np.ndarray = None) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Create sequences for LSTM training
        
        Args:
            X: Input features
            y: Target values (optional)
            
        Returns:
            Sequences for training/prediction
        """
        X_seq = []
        y_seq = [] if y is not None else None
        
        for i in range(self.sequence_length, len(X)):
            X_seq.append(X[i-self.sequence_length:i])
            if y is not None:
                y_seq.append(y[i])
        
        X_seq = np.array(X_seq)
        
        if y is not None:
            y_seq = np.array(y_seq)
            return X_seq, y_seq
        
        return X_seq
    
    def _build_model(self, input_shape: Tuple[int, int]) -> Model:
        """
        Build LSTM model with attention mechanism
        
        Args:
            input_shape: Input shape (sequence_length, features)
            
        Returns:
            Compiled Keras model
        """
        # Input layer
        inputs = Input(shape=input_shape, name='input_sequence')
        
        # LSTM layers
        x = inputs
        
        for i in range(self.num_layers):
            return_sequences = (i < self.num_layers - 1) or self.use_attention
            
            if self.use_bidirectional:
                x = Bidirectional(
                    LSTM(
                        self.hidden_dim,
                        return_sequences=return_sequences,
                        dropout=self.dropout,
                        recurrent_dropout=self.dropout,
                        kernel_regularizer=l1_l2(0.01, 0.01),
                        name=f'lstm_{i}'
                    ),
                    name=f'bidirectional_lstm_{i}'
                )(x)
            else:
                x = LSTM(
                    self.hidden_dim,
                    return_sequences=return_sequences,
                    dropout=self.dropout,
                    recurrent_dropout=self.dropout,
                    kernel_regularizer=l1_l2(0.01, 0.01),
                    name=f'lstm_{i}'
                )(x)
            
            if self.use_layer_norm:
                x = LayerNormalization(name=f'layer_norm_{i}')(x)
            
            x = Dropout(self.dropout, name=f'dropout_{i}')(x)
        
        # Attention mechanism
        if self.use_attention:
            # Multi-head attention
            attention_output = MultiHeadAttention(
                num_heads=8,
                key_dim=self.attention_dim,
                dropout=self.dropout,
                name='multi_head_attention'
            )(x, x)
            
            # Add & Norm
            x = tf.keras.layers.Add(name='attention_add')([x, attention_output])
            if self.use_layer_norm:
                x = LayerNormalization(name='attention_norm')(x)
            
            # Global pooling
            x = GlobalAveragePooling1D(name='global_pooling')(x)
        
        # Dense layers
        x = Dense(
            self.hidden_dim // 2,
            activation='relu',
            kernel_regularizer=l1_l2(0.01, 0.01),
            name='dense_1'
        )(x)
        
        if self.use_layer_norm:
            x = LayerNormalization(name='dense_norm')(x)
        
        x = Dropout(self.dropout, name='dense_dropout')(x)
        
        x = Dense(
            self.hidden_dim // 4,
            activation='relu',
            kernel_regularizer=l1_l2(0.01, 0.01),
            name='dense_2'
        )(x)
        
        # Output layer
        outputs = Dense(1, activation='linear', name='output')(x)
        
        # Create model
        model = Model(inputs=inputs, outputs=outputs, name='AttentionLSTM')
        
        # Compile model
        optimizer = Adam(
            learning_rate=self.learning_rate,
            clipnorm=self.model_config.get('gradient_clipping', 1.0)
        )
        
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae', 'mape']
        )
        
        return model
    
    def _create_callbacks(self, validation_split: float = 0.2) -> List:
        """Create training callbacks"""
        callbacks = []
        
        # Early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=self.model_config.get('patience', 15),
            min_delta=self.model_config.get('min_delta', 0.0001),
            restore_best_weights=True,
            verbose=1
        )
        callbacks.append(early_stopping)
        
        # Reduce learning rate
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=10,
            min_lr=1e-7,
            verbose=1
        )
        callbacks.append(reduce_lr)
        
        # Model checkpoint
        checkpoint = ModelCheckpoint(
            filepath='best_model.h5',
            monitor='val_loss',
            save_best_only=True,
            save_weights_only=False,
            verbose=1
        )
        callbacks.append(checkpoint)
        
        # TensorBoard
        tensorboard = TensorBoard(
            log_dir=f'./logs/lstm_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            histogram_freq=1,
            write_graph=True,
            write_images=True
        )
        callbacks.append(tensorboard)
        
        return callbacks
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'AttentionLSTMModel':
        """
        Fit LSTM model to training data
        
        Args:
            X: Feature matrix
            y: Target values
            
        Returns:
            Fitted model
        """
        self.logger.info("Starting LSTM model training...")
        
        # Prepare data
        X_scaled = self.scaler_X.fit_transform(X.values)
        y_scaled = self.scaler_y.fit_transform(y.values.reshape(-1, 1)).flatten()
        
        # Create sequences
        X_seq, y_seq = self._create_sequences(X_scaled, y_scaled)
        
        # Split validation data
        validation_split = self.model_config.get('validation_split', 0.2)
        split_idx = int(len(X_seq) * (1 - validation_split))
        
        X_train, X_val = X_seq[:split_idx], X_seq[split_idx:]
        y_train, y_val = y_seq[:split_idx], y_seq[split_idx:]
        
        # Build model
        self.model = self._build_model(input_shape=(self.sequence_length, X.shape[1]))
        self.logger.info(f"Model architecture: {self.model.summary()}")
        
        # Create callbacks
        callbacks = self._create_callbacks(validation_split)
        
        # Train model
        self.history = self.model.fit(
            X_train, y_train,
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            verbose=1,
            shuffle=False  # Don't shuffle time series data
        )
        
        self.is_fitted = True
        self.logger.info("LSTM model training completed")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using fitted LSTM model
        
        Args:
            X: Feature matrix
            
        Returns:
            Predictions array
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Scale features
        X_scaled = self.scaler_X.transform(X.values)
        
        # Create sequences
        X_seq = self._create_sequences(X_scaled)
        
        # Make predictions
        predictions_scaled = self.model.predict(X_seq, batch_size=self.batch_size)
        
        # Inverse transform predictions
        predictions = self.scaler_y.inverse_transform(predictions_scaled).flatten()
        
        # Handle sequence length offset
        full_predictions = np.full(len(X), np.nan)
        full_predictions[self.sequence_length:] = predictions
        
        return full_predictions
    
    def predict_with_uncertainty(self, X: pd.DataFrame, n_samples: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Make predictions with uncertainty estimation using Monte Carlo Dropout
        
        Args:
            X: Feature matrix
            n_samples: Number of Monte Carlo samples
            
        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Scale features
        X_scaled = self.scaler_X.transform(X.values)
        
        # Create sequences
        X_seq = self._create_sequences(X_scaled)
        
        # Enable dropout during inference
        predictions_samples = []
        
        for _ in range(n_samples):
            # Make prediction with dropout enabled
            predictions_scaled = self.model(X_seq, training=True)
            predictions = self.scaler_y.inverse_transform(predictions_scaled).flatten()
            predictions_samples.append(predictions)
        
        predictions_samples = np.array(predictions_samples)
        
        # Calculate statistics
        mean_predictions = np.mean(predictions_samples, axis=0)
        std_predictions = np.std(predictions_samples, axis=0)
        
        # Calculate confidence intervals (assuming normal distribution)
        lower_bound = mean_predictions - 1.96 * std_predictions
        upper_bound = mean_predictions + 1.96 * std_predictions
        
        # Handle sequence length offset
        full_predictions = np.full(len(X), np.nan)
        full_lower = np.full(len(X), np.nan)
        full_upper = np.full(len(X), np.nan)
        
        full_predictions[self.sequence_length:] = mean_predictions
        full_lower[self.sequence_length:] = lower_bound
        full_upper[self.sequence_length:] = upper_bound
        
        return full_predictions, full_lower, full_upper
    
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
        
        # Remove NaN values for evaluation
        valid_mask = ~np.isnan(predictions)
        y_valid = y.values[valid_mask]
        pred_valid = predictions[valid_mask]
        
        if len(y_valid) == 0:
            return {'error': 'No valid predictions to evaluate'}
        
        metrics = {
            'mae': mean_absolute_error(y_valid, pred_valid),
            'mse': mean_squared_error(y_valid, pred_valid),
            'rmse': np.sqrt(mean_squared_error(y_valid, pred_valid)),
            'r2': r2_score(y_valid, pred_valid),
            'mape': np.mean(np.abs((y_valid - pred_valid) / y_valid)) * 100
        }
        
        self.performance_metrics['evaluation'] = metrics
        
        return metrics
    
    def get_attention_weights(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get attention weights for interpretability
        
        Args:
            X: Feature matrix
            
        Returns:
            Attention weights
        """
        if not self.is_fitted or not self.use_attention:
            raise ValueError("Model must be fitted and use attention mechanism")
        
        # Create a model that outputs attention weights
        attention_layer = self.model.get_layer('multi_head_attention')
        
        # Scale features
        X_scaled = self.scaler_X.transform(X.values)
        
        # Create sequences
        X_seq = self._create_sequences(X_scaled)
        
        # Get attention weights
        # Note: This is a simplified implementation
        # In practice, you'd need to modify the model to output attention weights
        
        return np.zeros((len(X_seq), self.sequence_length))  # Placeholder
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance using gradient-based method
        
        Returns:
            Feature importance dataframe
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        
        # This is a simplified implementation
        # In practice, you'd use techniques like:
        # - Gradient-based feature importance
        # - Permutation importance
        # - SHAP values
        
        importance_data = []
        
        # Get layer weights as proxy for importance
        for layer in self.model.layers:
            if hasattr(layer, 'weights') and layer.weights:
                layer_name = layer.name
                weights = layer.get_weights()[0]  # Get first weight matrix
                
                if len(weights.shape) > 1:
                    # Calculate average absolute weight per input feature
                    avg_weights = np.mean(np.abs(weights), axis=1)
                    
                    for i, weight in enumerate(avg_weights):
                        importance_data.append({
                            'feature': f'{layer_name}_input_{i}',
                            'importance': weight,
                            'layer': layer_name
                        })
        
        return pd.DataFrame(importance_data).sort_values('importance', ascending=False)
    
    def save_model(self, filepath: str):
        """Save LSTM model and preprocessing components"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before saving")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save model
        self.model.save(f"{filepath}_model.h5")
        
        # Save preprocessing components
        model_data = {
            'config': self.model_config,
            'scaler_X': self.scaler_X,
            'scaler_y': self.scaler_y,
            'sequence_length': self.sequence_length,
            'performance_metrics': self.performance_metrics,
            'history': self.history.history if self.history else None
        }
        
        joblib.dump(model_data, f"{filepath}_data.pkl")
        
        self.logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load LSTM model and preprocessing components"""
        # Load model
        self.model = tf.keras.models.load_model(f"{filepath}_model.h5")
        
        # Load preprocessing components
        model_data = joblib.load(f"{filepath}_data.pkl")
        
        self.model_config = model_data['config']
        self.scaler_X = model_data['scaler_X']
        self.scaler_y = model_data['scaler_y']
        self.sequence_length = model_data['sequence_length']
        self.performance_metrics = model_data['performance_metrics']
        
        if model_data['history']:
            # Create a mock history object
            class MockHistory:
                def __init__(self, history_dict):
                    self.history = history_dict
            
            self.history = MockHistory(model_data['history'])
        
        self.is_fitted = True
        self.logger.info(f"Model loaded from {filepath}")
    
    def plot_training_history(self):
        """Plot training history"""
        if not self.history:
            raise ValueError("No training history available")
        
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Loss
        axes[0, 0].plot(self.history.history['loss'], label='Training Loss')
        axes[0, 0].plot(self.history.history['val_loss'], label='Validation Loss')
        axes[0, 0].set_title('Model Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].legend()
        
        # MAE
        axes[0, 1].plot(self.history.history['mae'], label='Training MAE')
        axes[0, 1].plot(self.history.history['val_mae'], label='Validation MAE')
        axes[0, 1].set_title('Mean Absolute Error')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('MAE')
        axes[0, 1].legend()
        
        # MAPE
        axes[1, 0].plot(self.history.history['mape'], label='Training MAPE')
        axes[1, 0].plot(self.history.history['val_mape'], label='Validation MAPE')
        axes[1, 0].set_title('Mean Absolute Percentage Error')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('MAPE')
        axes[1, 0].legend()
        
        # Learning Rate (if available)
        if 'lr' in self.history.history:
            axes[1, 1].plot(self.history.history['lr'], label='Learning Rate')
            axes[1, 1].set_title('Learning Rate')
            axes[1, 1].set_xlabel('Epoch')
            axes[1, 1].set_ylabel('Learning Rate')
            axes[1, 1].legend()
        
        plt.tight_layout()
        plt.show()
        
        return fig