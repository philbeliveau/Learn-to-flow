# 🤖 SPÉCIFICATIONS MODÈLES ML - EZBI ANALYTICS

## 🎯 ARCHITECTURE ML GLOBALE

### Vue d'Ensemble des Modèles
```
🧠 EZBI ML Pipeline Architecture

┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  Excel/CSV    │  ERP APIs     │  Bank APIs    │  External Data  │
│  Upload       │  Integration  │  Integration  │  (Weather, etc) │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   DATA PREPROCESSING                           │
├─────────────────────────────────────────────────────────────────┤
│ • Column Detection    • Data Validation    • Missing Values    │
│ • Format Standardization • Outlier Detection • Feature Eng.   │
│ │• RFM Calculation    • Seasonal Decomposition • Normalization 
└─────────────────────────┬───────────────────────────────────────┘
                          │
      ┌───────────────────┼───────────────────┐
      │                   │                   │
┌─────▼──────┐   ┌────────▼────────┐   ┌─────▼──────┐
│ PROPHET    │   │     LSTM        │   │   ARIMA    │
│ MODEL      │   │    MODEL        │   │   MODEL    │
│            │   │                 │   │            │
│ • Seasonal │   │ • Deep Learning │   │ • Classical│
│ • Trends   │   │ • Sequences     │   │ • Fast     │
│ • Holidays │   │ • Non-linear    │   │ • Baseline │
└─────┬──────┘   └────────┬────────┘   └─────┬──────┘
      │                   │                   │
      └───────────────────┼───────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    ENSEMBLE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│ • Weighted Averaging  • Stacking        • Boosting             │
│ • Cross-validation   • Model Selection  • Confidence Intervals │
│ • Performance Metrics • A/B Testing    • Auto-tuning          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   PREDICTION OUTPUT                            │
├─────────────────────────────────────────────────────────────────┤
│ • Cash Flow Forecast  • Confidence Bands  • Business Insights  │
│ • Client Scoring      • Risk Alerts       • Recommendations    │
│ • Scenario Analysis   • Trend Detection   • Anomaly Detection  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔮 MODÈLE PROPHET - PRÉDICTIONS SAISONNIÈRES

### Configuration Prophet Optimisée
```python
# 📈 Prophet Model for Manufacturing Cash Flow

import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

class ManufacturingProphetModel:
    """
    Prophet model optimized for manufacturing cash flow prediction
    with industry-specific seasonalities and holidays
    """
    
    def __init__(self, 
                 seasonality_mode: str = 'multiplicative',
                 industry_sector: str = 'general',
                 include_holidays: bool = True):
        
        self.industry_sector = industry_sector
        self.seasonality_mode = seasonality_mode
        
        # Initialize Prophet with manufacturing-specific settings
        self.model = Prophet(
            seasonality_mode=seasonality_mode,
            yearly_seasonality=True,
            weekly_seasonality=False,  # Not relevant for B2B monthly data
            daily_seasonality=False,
            holidays_prior_scale=15.0,  # Strong holiday effects in manufacturing
            seasonality_prior_scale=10.0,
            changepoint_prior_scale=0.05,  # Conservative changepoint detection
            changepoint_range=0.8,
            n_changepoints=25
        )
        
        self._add_manufacturing_seasonalities()
        if include_holidays:
            self._add_french_holidays()
    
    def _add_manufacturing_seasonalities(self):
        """Add manufacturing-specific seasonal patterns"""
        
        # Quarterly seasonality (strong in manufacturing)
        self.model.add_seasonality(
            name='quarterly',
            period=91.25,
            fourier_order=8,
            prior_scale=10.0
        )
        
        # Semi-annual seasonality (budget cycles)
        self.model.add_seasonality(
            name='semi_annual',
            period=182.5,
            fourier_order=6,
            prior_scale=8.0
        )
        
        # Industry-specific seasonalities
        if self.industry_sector == 'automotive':
            # Summer shutdown in automotive
            self.model.add_seasonality(
                name='automotive_cycle',
                period=365.25,
                fourier_order=10,
                prior_scale=12.0,
                condition_name='is_automotive_peak'
            )
        
        elif self.industry_sector == 'agriculture':
            # Agricultural machinery seasonal demand
            self.model.add_seasonality(
                name='agricultural_cycle',
                period=365.25,
                fourier_order=12,
                prior_scale=15.0,
                condition_name='is_agricultural_season'
            )
    
    def _add_french_holidays(self):
        """Add French holidays and manufacturing-specific dates"""
        
        import holidays
        fr_holidays = holidays.France(years=range(2020, 2030))
        
        # Convert to Prophet format
        holiday_df = pd.DataFrame([
            {'holiday': 'french_holiday', 'ds': date, 'lower_window': -1, 'upper_window': 1}
            for date in fr_holidays.keys()
        ])
        
        # Add manufacturing-specific holidays
        manufacturing_holidays = pd.DataFrame([
            # Summer shutdown periods (common in French manufacturing)
            {'holiday': 'summer_shutdown', 'ds': pd.to_datetime('2024-08-01'), 'lower_window': -7, 'upper_window': 21},
            {'holiday': 'summer_shutdown', 'ds': pd.to_datetime('2025-08-01'), 'lower_window': -7, 'upper_window': 21},
            
            # End of year inventory closure
            {'holiday': 'year_end_closure', 'ds': pd.to_datetime('2024-12-20'), 'lower_window': -3, 'upper_window': 10},
            {'holiday': 'year_end_closure', 'ds': pd.to_datetime('2025-12-20'), 'lower_window': -3, 'upper_window': 10},
        ])
        
        all_holidays = pd.concat([holiday_df, manufacturing_holidays], ignore_index=True)
        self.model.holidays = all_holidays
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for Prophet training
        
        Args:
            df: DataFrame with columns ['date', 'amount', 'client_id', 'sector']
            
        Returns:
            Prophet-formatted DataFrame with additional regressors
        """
        
        # Aggregate by date (monthly cash flow)
        prophet_df = df.groupby('date').agg({
            'amount': 'sum',
            'client_id': 'nunique'
        }).reset_index()
        
        prophet_df.columns = ['ds', 'y', 'client_count']
        
        # Add external regressors
        prophet_df['month'] = prophet_df['ds'].dt.month
        prophet_df['quarter'] = prophet_df['ds'].dt.quarter
        prophet_df['is_month_end'] = (prophet_df['ds'].dt.day > 25).astype(int)
        
        # Industry-specific conditions
        if self.industry_sector == 'automotive':
            prophet_df['is_automotive_peak'] = (
                (prophet_df['month'].isin([3, 6, 9, 12]))  # Quarter ends
            ).astype(int)
        
        # Add economic indicators (if available)
        prophet_df['economic_indicator'] = self._get_economic_indicator(prophet_df['ds'])
        
        return prophet_df
    
    def _get_economic_indicator(self, dates: pd.Series) -> pd.Series:
        """Get economic indicators for dates (mock implementation)"""
        # In production, this would fetch real economic data
        np.random.seed(42)
        return pd.Series(np.random.normal(100, 10, len(dates)))
    
    def train(self, df: pd.DataFrame) -> Dict:
        """
        Train the Prophet model
        
        Args:
            df: Training data
            
        Returns:
            Training results and metrics
        """
        
        # Prepare data
        prophet_df = self.prepare_data(df)
        
        # Add regressors
        self.model.add_regressor('client_count', prior_scale=0.5)
        self.model.add_regressor('is_month_end', prior_scale=10.0)
        self.model.add_regressor('economic_indicator', prior_scale=0.1)
        
        # Fit model
        self.model.fit(prophet_df)
        
        # Cross-validation for performance metrics
        cv_results = cross_validation(
            self.model, 
            initial='365 days', 
            period='90 days', 
            horizon='180 days'
        )
        
        performance = performance_metrics(cv_results)
        
        return {
            'model_type': 'prophet',
            'training_points': len(prophet_df),
            'cross_validation_mape': performance['mape'].mean(),
            'cross_validation_rmse': performance['rmse'].mean(),
            'seasonal_components': self._extract_seasonal_insights(prophet_df)
        }
    
    def predict(self, df: pd.DataFrame, horizon_days: int = 180) -> Dict:
        """
        Generate predictions
        
        Args:
            df: Historical data for context
            horizon_days: Prediction horizon
            
        Returns:
            Predictions with confidence intervals and insights
        """
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=horizon_days, freq='D')
        
        # Add future regressors (would need forecasting in production)
        future['client_count'] = future['client_count'].fillna(method='ffill')
        future['is_month_end'] = (future['ds'].dt.day > 25).astype(int)
        future['economic_indicator'] = 100  # Simplified assumption
        
        # Generate forecast
        forecast = self.model.predict(future)
        
        # Extract predictions only (not historical fit)
        predictions = forecast.tail(horizon_days)
        
        return {
            'model_type': 'prophet',
            'predictions': predictions[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict('records'),
            'components': {
                'trend': predictions[['ds', 'trend']].to_dict('records'),
                'seasonal': predictions[['ds', 'yearly', 'quarterly']].to_dict('records'),
                'holidays': predictions[['ds', 'holidays']].to_dict('records') if 'holidays' in predictions.columns else []
            },
            'insights': self._generate_insights(predictions),
            'confidence_level': 0.80  # Prophet default
        }
    
    def _extract_seasonal_insights(self, df: pd.DataFrame) -> Dict:
        """Extract seasonal patterns for business insights"""
        
        # Fit temporary model to extract components
        temp_future = self.model.make_future_dataframe(periods=0)
        temp_forecast = self.model.predict(temp_future)
        
        return {
            'strongest_month': temp_forecast.groupby(temp_forecast['ds'].dt.month)['yearly'].mean().idxmax(),
            'weakest_month': temp_forecast.groupby(temp_forecast['ds'].dt.month)['yearly'].mean().idxmin(),
            'seasonal_amplitude': temp_forecast['yearly'].std(),
            'trend_direction': 'increasing' if temp_forecast['trend'].iloc[-1] > temp_forecast['trend'].iloc[0] else 'decreasing'
        }
    
    def _generate_insights(self, predictions: pd.DataFrame) -> List[str]:
        """Generate business insights from predictions"""
        
        insights = []
        
        # Trend analysis
        trend_change = predictions['trend'].iloc[-1] - predictions['trend'].iloc[0]
        if trend_change > 0:
            insights.append(f"Tendance positive détectée: +{trend_change:.0f}€ sur la période")
        else:
            insights.append(f"Tendance négative détectée: {trend_change:.0f}€ sur la période")
        
        # Seasonality insights
        if 'yearly' in predictions.columns:
            seasonal_peak = predictions.loc[predictions['yearly'].idxmax()]
            insights.append(f"Pic saisonnier prévu le {seasonal_peak['ds'].strftime('%d/%m/%Y')}")
        
        # Risk analysis
        risky_periods = predictions[predictions['yhat_lower'] < 0]
        if not risky_periods.empty:
            insights.append(f"⚠️ {len(risky_periods)} périodes à risque de cash flow négatif détectées")
        
        # Confidence analysis
        avg_confidence = (predictions['yhat_upper'] - predictions['yhat_lower']).mean()
        if avg_confidence > predictions['yhat'].mean() * 0.5:
            insights.append("🔍 Prédictions avec forte incertitude - plus de données recommandées")
        
        return insights

# Prophet Model Factory
class ProphetModelFactory:
    """Factory for creating industry-specific Prophet models"""
    
    @staticmethod
    def create_model(industry: str, **kwargs) -> ManufacturingProphetModel:
        """Create industry-optimized Prophet model"""
        
        industry_configs = {
            'metallurgie': {
                'seasonality_mode': 'multiplicative',
                'changepoint_prior_scale': 0.08,  # More volatile
                'holidays_prior_scale': 20.0
            },
            'agroalimentaire': {
                'seasonality_mode': 'multiplicative',
                'changepoint_prior_scale': 0.03,  # More stable
                'holidays_prior_scale': 25.0  # Strong holiday effects
            },
            'automobile': {
                'seasonality_mode': 'multiplicative',
                'changepoint_prior_scale': 0.1,  # Very volatile
                'holidays_prior_scale': 30.0
            },
            'chimie': {
                'seasonality_mode': 'additive',  # More consistent patterns
                'changepoint_prior_scale': 0.04,
                'holidays_prior_scale': 10.0
            }
        }
        
        config = industry_configs.get(industry, {})
        config.update(kwargs)
        config['industry_sector'] = industry
        
        return ManufacturingProphetModel(**config)
```

---

## 🧠 MODÈLE LSTM - DEEP LEARNING

### Architecture LSTM Avancée
```python
# 🧠 Advanced LSTM for Manufacturing Cash Flow

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from typing import Dict, List, Tuple, Optional
import logging

class CashFlowDataset(Dataset):
    """PyTorch Dataset for cash flow time series"""
    
    def __init__(self, 
                 data: np.ndarray, 
                 sequence_length: int = 60,
                 prediction_horizon: int = 30):
        
        self.data = data
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        
        # Create sequences
        self.sequences = []
        self.targets = []
        
        for i in range(len(data) - sequence_length - prediction_horizon + 1):
            seq = data[i:i + sequence_length]
            target = data[i + sequence_length:i + sequence_length + prediction_horizon]
            
            self.sequences.append(seq)
            self.targets.append(target)
        
        self.sequences = np.array(self.sequences)
        self.targets = np.array(self.targets)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return (
            torch.FloatTensor(self.sequences[idx]),
            torch.FloatTensor(self.targets[idx])
        )

class AttentionLSTM(nn.Module):
    """LSTM with Attention Mechanism for Cash Flow Prediction"""
    
    def __init__(self, 
                 input_size: int,
                 hidden_size: int = 128,
                 num_layers: int = 3,
                 output_size: int = 30,
                 dropout: float = 0.2,
                 attention_heads: int = 8):
        
        super(AttentionLSTM, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,  # Bidirectional
            num_heads=attention_heads,
            dropout=dropout,
            batch_first=True
        )
        
        # Feature extraction layers
        self.feature_extractor = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Output layers
        self.output_layer = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 4, output_size)
        )
        
        # Uncertainty estimation
        self.uncertainty_layer = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, output_size),
            nn.Softplus()  # Ensure positive uncertainty
        )
    
    def forward(self, x):
        batch_size = x.size(0)
        
        # LSTM forward pass
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Attention mechanism
        attn_out, attn_weights = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Use last timestep with attention
        last_timestep = attn_out[:, -1, :]
        
        # Feature extraction
        features = self.feature_extractor(last_timestep)
        
        # Predictions and uncertainty
        predictions = self.output_layer(features)
        uncertainty = self.uncertainty_layer(features)
        
        return predictions, uncertainty, attn_weights

class ManufacturingLSTMModel:
    """Advanced LSTM model for manufacturing cash flow prediction"""
    
    def __init__(self,
                 sequence_length: int = 60,
                 prediction_horizon: int = 30,
                 hidden_size: int = 128,
                 num_layers: int = 3,
                 learning_rate: float = 0.001,
                 device: str = 'auto'):
        
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        
        # Device selection
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        self.model = None
        self.scaler_features = MinMaxScaler()
        self.scaler_target = MinMaxScaler()
        self.is_trained = False
        
        # Training history
        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'mape': [],
            'rmse': []
        }
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create advanced features for LSTM"""
        
        features = df.copy()
        
        # Temporal features
        features['day_of_month'] = features['date'].dt.day
        features['month'] = features['date'].dt.month
        features['quarter'] = features['date'].dt.quarter
        features['day_of_week'] = features['date'].dt.dayofweek
        features['is_month_end'] = (features['date'].dt.day > 25).astype(int)
        features['is_quarter_end'] = features['date'].dt.month.isin([3, 6, 9, 12]).astype(int)
        
        # Rolling statistics (multiple windows)
        for window in [7, 14, 30, 90]:
            features[f'rolling_mean_{window}'] = features['amount'].rolling(window=window).mean()
            features[f'rolling_std_{window}'] = features['amount'].rolling(window=window).std()
            features[f'rolling_min_{window}'] = features['amount'].rolling(window=window).min()
            features[f'rolling_max_{window}'] = features['amount'].rolling(window=window).max()
        
        # Lag features
        for lag in [1, 2, 3, 7, 14, 30]:
            features[f'lag_{lag}'] = features['amount'].shift(lag)
        
        # Seasonal decomposition features
        features['trend'] = features['amount'].rolling(window=30, center=True).mean()
        features['seasonal'] = features['amount'] - features['trend']
        features['volatility'] = features['amount'].rolling(window=30).std()
        
        # Economic calendar features (mock)
        features['economic_indicator'] = np.sin(2 * np.pi * features['month'] / 12)
        features['business_cycle'] = np.cos(2 * np.pi * features['month'] / 12)
        
        # Forward fill missing values
        features = features.fillna(method='ffill').fillna(method='bfill')
        
        return features
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM training"""
        
        # Create features
        features_df = self._create_features(df)
        
        # Select feature columns (exclude date and target)
        feature_columns = [col for col in features_df.columns if col not in ['date', 'amount']]
        
        # Prepare features and targets
        X = features_df[feature_columns].values
        y = features_df['amount'].values.reshape(-1, 1)
        
        # Scale features and targets
        X_scaled = self.scaler_features.fit_transform(X)
        y_scaled = self.scaler_target.fit_transform(y)
        
        return X_scaled, y_scaled.flatten()
    
    def train(self, df: pd.DataFrame, validation_split: float = 0.2, epochs: int = 100) -> Dict:
        """Train the LSTM model"""
        
        # Prepare data
        X, y = self.prepare_data(df)
        
        # Train/validation split
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Create datasets
        train_dataset = CashFlowDataset(
            np.column_stack([X_train, y_train]),
            self.sequence_length,
            self.prediction_horizon
        )
        
        val_dataset = CashFlowDataset(
            np.column_stack([X_val, y_val]),
            self.sequence_length,
            self.prediction_horizon
        )
        
        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
        
        # Initialize model
        input_size = X.shape[1] + 1  # Features + target
        self.model = AttentionLSTM(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            output_size=self.prediction_horizon
        ).to(self.device)
        
        # Loss function and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=0.01)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
        
        # Training loop
        best_val_loss = float('inf')
        early_stopping_counter = 0
        early_stopping_patience = 20
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            
            for sequences, targets in train_loader:
                sequences, targets = sequences.to(self.device), targets.to(self.device)
                
                optimizer.zero_grad()
                
                predictions, uncertainty, _ = self.model(sequences)
                loss = criterion(predictions, targets)
                
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                
                train_loss += loss.item()
            
            # Validation phase
            self.model.eval()
            val_loss = 0.0
            val_predictions = []
            val_targets = []
            
            with torch.no_grad():
                for sequences, targets in val_loader:
                    sequences, targets = sequences.to(self.device), targets.to(self.device)
                    
                    predictions, uncertainty, _ = self.model(sequences)
                    loss = criterion(predictions, targets)
                    val_loss += loss.item()
                    
                    val_predictions.extend(predictions.cpu().numpy())
                    val_targets.extend(targets.cpu().numpy())
            
            # Calculate metrics
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            
            val_predictions = np.array(val_predictions)
            val_targets = np.array(val_targets)
            
            mape = mean_absolute_percentage_error(val_targets.flatten(), val_predictions.flatten())
            rmse = np.sqrt(mean_squared_error(val_targets.flatten(), val_predictions.flatten()))
            
            # Update history
            self.training_history['train_loss'].append(avg_train_loss)
            self.training_history['val_loss'].append(avg_val_loss)
            self.training_history['mape'].append(mape)
            self.training_history['rmse'].append(rmse)
            
            # Learning rate scheduling
            scheduler.step(avg_val_loss)
            
            # Early stopping
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                early_stopping_counter = 0
                # Save best model
                torch.save(self.model.state_dict(), 'best_lstm_model.pth')
            else:
                early_stopping_counter += 1
            
            if early_stopping_counter >= early_stopping_patience:
                print(f"Early stopping at epoch {epoch}")
                break
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch}: Train Loss: {avg_train_loss:.6f}, Val Loss: {avg_val_loss:.6f}, MAPE: {mape:.4f}")
        
        # Load best model
        self.model.load_state_dict(torch.load('best_lstm_model.pth'))
        self.is_trained = True
        
        return {
            'model_type': 'lstm_attention',
            'training_epochs': epoch + 1,
            'best_validation_loss': best_val_loss,
            'final_mape': self.training_history['mape'][-1],
            'final_rmse': self.training_history['rmse'][-1],
            'training_history': self.training_history
        }
    
    def predict(self, df: pd.DataFrame, confidence_level: float = 0.95) -> Dict:
        """Generate predictions with uncertainty estimates"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Prepare data
        X, y = self.prepare_data(df)
        
        # Use last sequence for prediction
        last_sequence = X[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        last_sequence = torch.FloatTensor(last_sequence).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            predictions, uncertainty, attention_weights = self.model(last_sequence)
            
            predictions = predictions.cpu().numpy().flatten()
            uncertainty = uncertainty.cpu().numpy().flatten()
            attention_weights = attention_weights.cpu().numpy()
        
        # Inverse transform predictions
        predictions_original = self.scaler_target.inverse_transform(predictions.reshape(-1, 1)).flatten()
        uncertainty_original = uncertainty * self.scaler_target.scale_[0]
        
        # Calculate confidence intervals
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
        lower_bound = predictions_original - z_score * uncertainty_original
        upper_bound = predictions_original + z_score * uncertainty_original
        
        # Create date range for predictions
        last_date = df['date'].max()
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=self.prediction_horizon)
        
        prediction_results = []
        for i, date in enumerate(future_dates):
            prediction_results.append({
                'ds': date,
                'yhat': float(predictions_original[i]),
                'yhat_lower': float(lower_bound[i]),
                'yhat_upper': float(upper_bound[i]),
                'uncertainty': float(uncertainty_original[i])
            })
        
        return {
            'model_type': 'lstm_attention',
            'predictions': prediction_results,
            'attention_weights': attention_weights.tolist(),
            'confidence_level': confidence_level,
            'insights': self._generate_lstm_insights(predictions_original, uncertainty_original)
        }
    
    def _generate_lstm_insights(self, predictions: np.ndarray, uncertainties: np.ndarray) -> List[str]:
        """Generate insights from LSTM predictions"""
        
        insights = []
        
        # Trend analysis
        if len(predictions) > 1:
            trend = np.polyfit(range(len(predictions)), predictions, 1)[0]
            if trend > 0:
                insights.append(f"🔼 Tendance haussière détectée: +{trend:.0f}€/jour")
            else:
                insights.append(f"🔽 Tendance baissière détectée: {trend:.0f}€/jour")
        
        # Uncertainty analysis
        avg_uncertainty = np.mean(uncertainties)
        max_uncertainty = np.max(uncertainties)
        
        if max_uncertainty > predictions.mean() * 0.3:
            insights.append("⚠️ Incertitude élevée détectée - surveillance recommandée")
        
        if avg_uncertainty < predictions.mean() * 0.1:
            insights.append("✅ Prédictions très fiables - faible incertitude")
        
        # Volatility insights
        volatility = np.std(predictions)
        if volatility > np.mean(predictions) * 0.2:
            insights.append("📊 Période de forte volatilité prévue")
        
        return insights
```

---

## 🏆 MODÈLE ENSEMBLE - COMBINAISON OPTIMALE

### Architecture Ensemble Intelligente
```python
# 🏆 Intelligent Ensemble for Maximum Accuracy

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')

class AdaptiveEnsembleModel:
    """
    Adaptive ensemble that combines Prophet, LSTM, and classical ML models
    with intelligent weighting based on recent performance
    """
    
    def __init__(self, 
                 base_models: Optional[List] = None,
                 meta_learner_type: str = 'linear',
                 performance_window: int = 30,
                 min_samples_for_weights: int = 10):
        
        self.base_models = base_models or []
        self.meta_learner_type = meta_learner_type
        self.performance_window = performance_window
        self.min_samples_for_weights = min_samples_for_weights
        
        # Meta-learner for intelligent combination
        if meta_learner_type == 'linear':
            self.meta_learner = LinearRegression()
        elif meta_learner_type == 'rf':
            self.meta_learner = RandomForestRegressor(n_estimators=100, random_state=42)
        elif meta_learner_type == 'gbm':
            self.meta_learner = GradientBoostingRegressor(n_estimators=100, random_state=42)
        
        # Performance tracking
        self.model_performance_history = {}
        self.dynamic_weights = {}
        self.is_trained = False
        
        # Fallback weights (equal by default)
        self.fallback_weights = None
    
    def add_model(self, model, model_name: str):
        """Add a base model to the ensemble"""
        self.base_models.append({'model': model, 'name': model_name})
        self.model_performance_history[model_name] = []
        self.dynamic_weights[model_name] = 1.0 / len(self.base_models)
    
    def _update_performance_history(self, model_name: str, actual: np.ndarray, predicted: np.ndarray):
        """Update performance history for dynamic weighting"""
        
        mape = mean_absolute_percentage_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        
        # Composite score (lower is better)
        composite_score = 0.7 * mape + 0.3 * (rmse / np.mean(actual))
        
        self.model_performance_history[model_name].append({
            'mape': mape,
            'rmse': rmse,
            'composite_score': composite_score,
            'timestamp': pd.Timestamp.now()
        })
        
        # Keep only recent performance data
        if len(self.model_performance_history[model_name]) > self.performance_window:
            self.model_performance_history[model_name] = \
                self.model_performance_history[model_name][-self.performance_window:]
    
    def _calculate_dynamic_weights(self) -> Dict[str, float]:
        """Calculate dynamic weights based on recent performance"""
        
        weights = {}
        total_inverse_score = 0
        
        for model_name, history in self.model_performance_history.items():
            if len(history) >= self.min_samples_for_weights:
                # Use recent performance (exponential decay)
                recent_scores = [h['composite_score'] for h in history[-10:]]
                decay_weights = np.exp(-np.arange(len(recent_scores)) * 0.1)
                weighted_score = np.average(recent_scores, weights=decay_weights)
                
                # Inverse score (lower error = higher weight)
                inverse_score = 1.0 / (weighted_score + 1e-6)
                weights[model_name] = inverse_score
                total_inverse_score += inverse_score
            else:
                # Use fallback weight for models without enough history
                weights[model_name] = 1.0
                total_inverse_score += 1.0
        
        # Normalize weights
        if total_inverse_score > 0:
            for model_name in weights:
                weights[model_name] /= total_inverse_score
        
        return weights
    
    def train(self, df: pd.DataFrame) -> Dict:
        """Train all base models and meta-learner"""
        
        training_results = {}
        base_predictions = []
        
        # Train each base model
        for model_info in self.base_models:
            model = model_info['model']
            model_name = model_info['name']
            
            print(f"Training {model_name}...")
            
            try:
                result = model.train(df)
                training_results[model_name] = result
                
                # Get cross-validation predictions for meta-learner training
                if hasattr(model, 'cross_validate'):
                    cv_predictions = model.cross_validate(df)
                    base_predictions.append(cv_predictions)
                
                print(f"✅ {model_name} trained successfully")
                
            except Exception as e:
                print(f"❌ Failed to train {model_name}: {str(e)}")
                training_results[model_name] = {'error': str(e)}
        
        # Train meta-learner if we have cross-validation predictions
        if len(base_predictions) >= 2:
            X_meta = np.column_stack(base_predictions)
            y_meta = df['amount'].values[-len(base_predictions[0]):]  # Assuming aligned
            
            self.meta_learner.fit(X_meta, y_meta)
            print("✅ Meta-learner trained")
        
        # Set equal initial weights
        num_successful_models = len([r for r in training_results.values() if 'error' not in r])
        self.fallback_weights = {
            model_info['name']: 1.0 / num_successful_models 
            for model_info in self.base_models 
            if training_results.get(model_info['name'], {}).get('error') is None
        }
        
        self.is_trained = True
        
        return {
            'ensemble_type': 'adaptive',
            'base_model_results': training_results,
            'successful_models': num_successful_models,
            'meta_learner_trained': len(base_predictions) >= 2,
            'initial_weights': self.fallback_weights
        }
    
    def predict(self, df: pd.DataFrame, horizon_days: int = 180) -> Dict:
        """Generate ensemble predictions"""
        
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before prediction")
        
        base_predictions = {}
        prediction_arrays = []
        successful_models = []
        
        # Get predictions from each base model
        for model_info in self.base_models:
            model = model_info['model']
            model_name = model_info['name']
            
            try:
                result = model.predict(df, horizon_days)
                base_predictions[model_name] = result
                
                # Extract prediction values
                if 'predictions' in result:
                    pred_values = [p['yhat'] for p in result['predictions']]
                    prediction_arrays.append(pred_values)
                    successful_models.append(model_name)
                
            except Exception as e:
                print(f"⚠️ {model_name} prediction failed: {str(e)}")
                base_predictions[model_name] = {'error': str(e)}
        
        if not prediction_arrays:
            raise ValueError("No base models produced valid predictions")
        
        # Ensure all prediction arrays have the same length
        min_length = min(len(pred) for pred in prediction_arrays)
        prediction_arrays = [pred[:min_length] for pred in prediction_arrays]
        
        # Calculate dynamic weights
        current_weights = self._calculate_dynamic_weights()
        
        # Use fallback weights for models without performance history
        weights = []
        for model_name in successful_models:
            if model_name in current_weights:
                weights.append(current_weights[model_name])
            else:
                weights.append(self.fallback_weights.get(model_name, 1.0 / len(successful_models)))
        
        # Normalize weights
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        # Ensemble prediction using meta-learner or weighted average
        if hasattr(self.meta_learner, 'predict') and len(prediction_arrays) >= 2:
            try:
                # Use meta-learner
                X_meta = np.column_stack(prediction_arrays)
                ensemble_predictions = self.meta_learner.predict(X_meta)
                method_used = 'meta_learner'
            except:
                # Fallback to weighted average
                prediction_matrix = np.array(prediction_arrays)
                ensemble_predictions = np.average(prediction_matrix, axis=0, weights=weights)
                method_used = 'weighted_average'
        else:
            # Weighted average
            prediction_matrix = np.array(prediction_arrays)
            ensemble_predictions = np.average(prediction_matrix, axis=0, weights=weights)
            method_used = 'weighted_average'
        
        # Calculate ensemble confidence intervals
        prediction_matrix = np.array(prediction_arrays)
        ensemble_std = np.std(prediction_matrix, axis=0)
        ensemble_lower = ensemble_predictions - 1.96 * ensemble_std
        ensemble_upper = ensemble_predictions + 1.96 * ensemble_std
        
        # Create date range
        last_date = df['date'].max()
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=min_length)
        
        # Format ensemble results
        ensemble_results = []
        for i, date in enumerate(future_dates):
            ensemble_results.append({
                'ds': date,
                'yhat': float(ensemble_predictions[i]),
                'yhat_lower': float(ensemble_lower[i]),
                'yhat_upper': float(ensemble_upper[i]),
                'ensemble_std': float(ensemble_std[i])
            })
        
        # Generate ensemble insights
        insights = self._generate_ensemble_insights(
            ensemble_predictions, 
            prediction_matrix, 
            weights, 
            successful_models
        )
        
        return {
            'model_type': 'adaptive_ensemble',
            'predictions': ensemble_results,
            'base_predictions': base_predictions,
            'model_weights': dict(zip(successful_models, weights)),
            'method_used': method_used,
            'model_agreement': self._calculate_model_agreement(prediction_matrix),
            'insights': insights,
            'confidence_level': 0.95
        }
    
    def _calculate_model_agreement(self, prediction_matrix: np.ndarray) -> Dict:
        """Calculate agreement metrics between models"""
        
        if prediction_matrix.shape[0] < 2:
            return {'agreement_score': 1.0, 'disagreement_periods': []}
        
        # Calculate coefficient of variation for each time point
        cv = np.std(prediction_matrix, axis=0) / (np.mean(prediction_matrix, axis=0) + 1e-6)
        
        # Overall agreement score (lower CV = higher agreement)
        agreement_score = 1.0 / (1.0 + np.mean(cv))
        
        # Identify periods of high disagreement
        disagreement_threshold = np.percentile(cv, 75)
        disagreement_periods = np.where(cv > disagreement_threshold)[0].tolist()
        
        return {
            'agreement_score': float(agreement_score),
            'disagreement_periods': disagreement_periods,
            'avg_coefficient_variation': float(np.mean(cv)),
            'max_disagreement': float(np.max(cv))
        }
    
    def _generate_ensemble_insights(self, 
                                   ensemble_predictions: np.ndarray,
                                   prediction_matrix: np.ndarray,
                                   weights: np.ndarray,
                                   model_names: List[str]) -> List[str]:
        """Generate insights from ensemble predictions"""
        
        insights = []
        
        # Model contribution analysis
        best_model_idx = np.argmax(weights)
        best_model = model_names[best_model_idx]
        insights.append(f"🏆 Modèle le plus performant: {best_model} (poids: {weights[best_model_idx]:.2f})")
        
        # Prediction confidence
        agreement = self._calculate_model_agreement(prediction_matrix)
        if agreement['agreement_score'] > 0.8:
            insights.append("✅ Forte convergence entre modèles - prédictions fiables")
        elif agreement['agreement_score'] < 0.6:
            insights.append("⚠️ Divergence entre modèles - incertitude élevée")
        
        # Trend analysis
        if len(ensemble_predictions) > 1:
            trend = np.polyfit(range(len(ensemble_predictions)), ensemble_predictions, 1)[0]
            if abs(trend) > np.mean(ensemble_predictions) * 0.01:  # 1% significance
                direction = "hausse" if trend > 0 else "baisse"
                insights.append(f"📈 Tendance {direction} confirmée par l'ensemble")
        
        # Volatility assessment
        volatility = np.std(ensemble_predictions)
        if volatility > np.mean(ensemble_predictions) * 0.2:
            insights.append("📊 Période de forte volatilité anticipée")
        
        # Risk assessment
        negative_periods = np.sum(ensemble_predictions < 0)
        if negative_periods > 0:
            insights.append(f"🚨 {negative_periods} périodes de cash flow négatif prévues")
        
        return insights
    
    def get_model_performance_summary(self) -> Dict:
        """Get performance summary for all models"""
        
        summary = {}
        
        for model_name, history in self.model_performance_history.items():
            if history:
                recent_performance = history[-5:]  # Last 5 predictions
                avg_mape = np.mean([h['mape'] for h in recent_performance])
                avg_rmse = np.mean([h['rmse'] for h in recent_performance])
                
                summary[model_name] = {
                    'avg_mape': avg_mape,
                    'avg_rmse': avg_rmse,
                    'predictions_count': len(history),
                    'current_weight': self.dynamic_weights.get(model_name, 0.0)
                }
        
        return summary

# Ensemble Factory
class EnsembleFactory:
    """Factory for creating industry-optimized ensemble models"""
    
    @staticmethod
    def create_manufacturing_ensemble(industry: str = 'general') -> AdaptiveEnsembleModel:
        """Create a manufacturing-optimized ensemble"""
        
        from .prophet_model import ProphetModelFactory
        from .lstm_model import ManufacturingLSTMModel
        
        # Create base models
        prophet_model = ProphetModelFactory.create_model(industry)
        lstm_model = ManufacturingLSTMModel(
            sequence_length=60,
            prediction_horizon=30,
            hidden_size=128
        )
        
        # Create ensemble
        ensemble = AdaptiveEnsembleModel(
            meta_learner_type='gbm',  # Gradient Boosting for meta-learning
            performance_window=50,
            min_samples_for_weights=5
        )
        
        # Add models
        ensemble.add_model(prophet_model, f'prophet_{industry}')
        ensemble.add_model(lstm_model, f'lstm_attention_{industry}')
        
        return ensemble
    
    @staticmethod
    def create_lightweight_ensemble() -> AdaptiveEnsembleModel:
        """Create a lightweight ensemble for smaller datasets"""
        
        from .prophet_model import ManufacturingProphetModel
        
        # Simplified models for quick deployment
        prophet_simple = ManufacturingProphetModel(
            seasonality_mode='additive',
            industry_sector='general'
        )
        
        ensemble = AdaptiveEnsembleModel(
            meta_learner_type='linear',
            performance_window=20,
            min_samples_for_weights=3
        )
        
        ensemble.add_model(prophet_simple, 'prophet_simple')
        
        return ensemble
```

Cette spécification ML complète définit une architecture sophistiquée avec des modèles spécialisés pour les PME manufacturières, offrant une précision et une fiabilité maximales pour les prédictions de cash flow.