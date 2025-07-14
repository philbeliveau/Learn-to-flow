"""
Model Monitoring and Retraining System
Comprehensive monitoring for model performance and data drift
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
import logging
from datetime import datetime, timedelta
import json
import joblib
import sqlite3
from pathlib import Path
import threading
import time
from dataclasses import dataclass, asdict
from enum import Enum
import warnings
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Email and alerting
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Model imports
from models.prophet.prophet_model import ManufacturingProphetModel
from models.lstm.lstm_attention_model import AttentionLSTMModel
from models.ensemble.ensemble_model import ManufacturingEnsembleModel
from features.manufacturing_features import ManufacturingFeatureEngine
from training.ml_training_pipeline import MLTrainingPipeline
from config.ml_config import config

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    timestamp: datetime
    model_name: str
    mae: float
    mse: float
    rmse: float
    r2: float
    mape: float
    prediction_count: int
    avg_confidence: float
    processing_time_ms: float

@dataclass
class DriftMetrics:
    """Data drift metrics"""
    timestamp: datetime
    feature_name: str
    drift_score: float
    p_value: float
    is_drift: bool
    reference_mean: float
    current_mean: float
    reference_std: float
    current_std: float

@dataclass
class Alert:
    """Alert information"""
    timestamp: datetime
    level: AlertLevel
    message: str
    metric_type: str
    model_name: str
    threshold: float
    current_value: float
    details: Dict[str, Any]

class ModelMonitor:
    """Comprehensive model monitoring system"""
    
    def __init__(self, 
                 models_dir: str = './models',
                 monitoring_db: str = './monitoring.db',
                 monitoring_interval: int = 300,  # 5 minutes
                 drift_window: int = 100,
                 performance_window: int = 50,
                 enable_alerts: bool = True,
                 enable_auto_retrain: bool = True):
        """
        Initialize Model Monitor
        
        Args:
            models_dir: Directory containing trained models
            monitoring_db: SQLite database for metrics storage
            monitoring_interval: Monitoring interval in seconds
            drift_window: Window size for drift detection
            performance_window: Window size for performance tracking
            enable_alerts: Enable alerting system
            enable_auto_retrain: Enable automatic retraining
        """
        self.models_dir = Path(models_dir)
        self.monitoring_db = monitoring_db
        self.monitoring_interval = monitoring_interval
        self.drift_window = drift_window
        self.performance_window = performance_window
        self.enable_alerts = enable_alerts
        self.enable_auto_retrain = enable_auto_retrain
        
        # Monitoring thresholds
        self.thresholds = config.monitoring.get('alert_thresholds', {
            'accuracy_drop': 0.05,
            'prediction_drift': 0.1,
            'latency_increase': 2.0,
            'drift_p_value': 0.05,
            'min_confidence': 0.7
        })
        
        # Models and data
        self.models = {}
        self.feature_engines = {}
        self.reference_data = {}
        self.current_predictions = []
        self.current_actuals = []
        
        # Monitoring state
        self.monitoring_thread = None
        self.is_monitoring = False
        self.last_metrics = {}
        
        # Alerting
        self.alerts = []
        self.alert_callbacks = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._initialize_database()
        
        # Load models
        self._load_models()
        
        # Start monitoring
        self.start_monitoring()
    
    def _initialize_database(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.monitoring_db)
        cursor = conn.cursor()
        
        # Model metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                model_name TEXT,
                mae REAL,
                mse REAL,
                rmse REAL,
                r2 REAL,
                mape REAL,
                prediction_count INTEGER,
                avg_confidence REAL,
                processing_time_ms REAL
            )
        ''')
        
        # Drift metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drift_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                feature_name TEXT,
                drift_score REAL,
                p_value REAL,
                is_drift BOOLEAN,
                reference_mean REAL,
                current_mean REAL,
                reference_std REAL,
                current_std REAL
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                level TEXT,
                message TEXT,
                metric_type TEXT,
                model_name TEXT,
                threshold REAL,
                current_value REAL,
                details TEXT
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                model_name TEXT,
                prediction REAL,
                actual REAL,
                confidence REAL,
                processing_time_ms REAL,
                features TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("Database initialized successfully")
    
    def _load_models(self):
        """Load models for monitoring"""
        self.logger.info("Loading models for monitoring...")
        
        # Load model files
        for model_path in self.models_dir.glob('*'):
            if model_path.suffix in ['.pkl', '.h5'] and 'feature_engine' not in model_path.name:
                try:
                    model_name = model_path.stem
                    
                    # Load model
                    if 'prophet' in model_name.lower():
                        model = ManufacturingProphetModel()
                        model.load_model(str(model_path.parent / model_name))
                    elif 'lstm' in model_name.lower():
                        model = AttentionLSTMModel()
                        model.load_model(str(model_path.parent / model_name))
                    elif 'ensemble' in model_name.lower():
                        model = ManufacturingEnsembleModel()
                        model.load_model(str(model_path.parent / model_name))
                    else:
                        model = joblib.load(model_path)
                    
                    self.models[model_name] = model
                    
                    # Load feature engine
                    feature_engine_path = model_path.parent / f"{model_name}.feature_engine.pkl"
                    if feature_engine_path.exists():
                        self.feature_engines[model_name] = joblib.load(feature_engine_path)
                    
                    self.logger.info(f"Loaded model: {model_name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load model {model_path}: {str(e)}")
        
        self.logger.info(f"Loaded {len(self.models)} models for monitoring")
    
    def set_reference_data(self, model_name: str, reference_data: pd.DataFrame):
        """Set reference data for drift detection"""
        self.reference_data[model_name] = reference_data
        self.logger.info(f"Set reference data for {model_name}: {len(reference_data)} samples")
    
    def log_prediction(self, 
                      model_name: str,
                      prediction: float,
                      actual: float = None,
                      confidence: float = None,
                      processing_time_ms: float = None,
                      features: Dict[str, Any] = None):
        """Log a prediction for monitoring"""
        
        # Store in memory for batch processing
        self.current_predictions.append({
            'timestamp': datetime.now(),
            'model_name': model_name,
            'prediction': prediction,
            'actual': actual,
            'confidence': confidence,
            'processing_time_ms': processing_time_ms,
            'features': json.dumps(features) if features else None
        })
        
        # Store in database
        conn = sqlite3.connect(self.monitoring_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions 
            (timestamp, model_name, prediction, actual, confidence, processing_time_ms, features)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), model_name, prediction, actual, confidence, processing_time_ms, 
              json.dumps(features) if features else None))
        conn.commit()
        conn.close()
    
    def calculate_model_metrics(self, model_name: str) -> Optional[ModelMetrics]:
        """Calculate model performance metrics"""
        
        # Get recent predictions
        conn = sqlite3.connect(self.monitoring_db)
        query = '''
            SELECT timestamp, prediction, actual, confidence, processing_time_ms
            FROM predictions 
            WHERE model_name = ? AND actual IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(model_name, self.performance_window))
        conn.close()
        
        if len(df) < 10:  # Need minimum samples
            return None
        
        # Calculate metrics
        predictions = df['prediction'].values
        actuals = df['actual'].values
        
        try:
            mae = mean_absolute_error(actuals, predictions)
            mse = mean_squared_error(actuals, predictions)
            rmse = np.sqrt(mse)
            r2 = r2_score(actuals, predictions)
            mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100
            
            metrics = ModelMetrics(
                timestamp=datetime.now(),
                model_name=model_name,
                mae=mae,
                mse=mse,
                rmse=rmse,
                r2=r2,
                mape=mape,
                prediction_count=len(df),
                avg_confidence=df['confidence'].mean() if 'confidence' in df.columns else 0.0,
                processing_time_ms=df['processing_time_ms'].mean() if 'processing_time_ms' in df.columns else 0.0
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics for {model_name}: {str(e)}")
            return None
    
    def detect_data_drift(self, 
                         current_data: pd.DataFrame,
                         reference_data: pd.DataFrame,
                         feature_name: str) -> DriftMetrics:
        """Detect data drift for a specific feature"""
        
        current_values = current_data[feature_name].dropna()
        reference_values = reference_data[feature_name].dropna()
        
        # Two-sample Kolmogorov-Smirnov test
        ks_statistic, p_value = stats.ks_2samp(reference_values, current_values)
        
        # Calculate drift score (normalized KS statistic)
        drift_score = ks_statistic
        
        # Determine if drift is significant
        is_drift = p_value < self.thresholds['drift_p_value']
        
        drift_metrics = DriftMetrics(
            timestamp=datetime.now(),
            feature_name=feature_name,
            drift_score=drift_score,
            p_value=p_value,
            is_drift=is_drift,
            reference_mean=reference_values.mean(),
            current_mean=current_values.mean(),
            reference_std=reference_values.std(),
            current_std=current_values.std()
        )
        
        return drift_metrics
    
    def check_model_performance(self, model_name: str):
        """Check model performance and generate alerts"""
        
        current_metrics = self.calculate_model_metrics(model_name)
        if not current_metrics:
            return
        
        # Store metrics in database
        conn = sqlite3.connect(self.monitoring_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO model_metrics 
            (timestamp, model_name, mae, mse, rmse, r2, mape, prediction_count, avg_confidence, processing_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_metrics.timestamp, current_metrics.model_name, current_metrics.mae,
              current_metrics.mse, current_metrics.rmse, current_metrics.r2, current_metrics.mape,
              current_metrics.prediction_count, current_metrics.avg_confidence, current_metrics.processing_time_ms))
        conn.commit()
        conn.close()
        
        # Compare with previous metrics
        if model_name in self.last_metrics:
            last_metrics = self.last_metrics[model_name]
            
            # Check for accuracy drop
            accuracy_drop = last_metrics.r2 - current_metrics.r2
            if accuracy_drop > self.thresholds['accuracy_drop']:
                self._create_alert(
                    AlertLevel.WARNING,
                    f"Model {model_name} accuracy dropped by {accuracy_drop:.3f}",
                    "performance",
                    model_name,
                    self.thresholds['accuracy_drop'],
                    accuracy_drop,
                    {'previous_r2': last_metrics.r2, 'current_r2': current_metrics.r2}
                )
            
            # Check for latency increase
            latency_increase = current_metrics.processing_time_ms / last_metrics.processing_time_ms
            if latency_increase > self.thresholds['latency_increase']:
                self._create_alert(
                    AlertLevel.WARNING,
                    f"Model {model_name} latency increased by {latency_increase:.1f}x",
                    "performance",
                    model_name,
                    self.thresholds['latency_increase'],
                    latency_increase,
                    {'previous_latency': last_metrics.processing_time_ms, 'current_latency': current_metrics.processing_time_ms}
                )
        
        # Check confidence levels
        if current_metrics.avg_confidence < self.thresholds['min_confidence']:
            self._create_alert(
                AlertLevel.WARNING,
                f"Model {model_name} confidence below threshold: {current_metrics.avg_confidence:.3f}",
                "confidence",
                model_name,
                self.thresholds['min_confidence'],
                current_metrics.avg_confidence,
                {'avg_confidence': current_metrics.avg_confidence}
            )
        
        # Store current metrics
        self.last_metrics[model_name] = current_metrics
    
    def check_data_drift(self, model_name: str):
        """Check for data drift"""
        
        if model_name not in self.reference_data:
            return
        
        # Get recent predictions data
        conn = sqlite3.connect(self.monitoring_db)
        query = '''
            SELECT features FROM predictions 
            WHERE model_name = ? AND features IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(model_name, self.drift_window))
        conn.close()
        
        if len(df) < 10:
            return
        
        # Parse features
        features_list = []
        for features_json in df['features']:
            try:
                features = json.loads(features_json)
                features_list.append(features)
            except:
                continue
        
        if not features_list:
            return
        
        current_data = pd.DataFrame(features_list)
        reference_data = self.reference_data[model_name]
        
        # Check drift for each feature
        for feature in current_data.columns:
            if feature in reference_data.columns:
                try:
                    drift_metrics = self.detect_data_drift(current_data, reference_data, feature)
                    
                    # Store drift metrics
                    conn = sqlite3.connect(self.monitoring_db)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO drift_metrics 
                        (timestamp, feature_name, drift_score, p_value, is_drift, 
                         reference_mean, current_mean, reference_std, current_std)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (drift_metrics.timestamp, drift_metrics.feature_name, drift_metrics.drift_score,
                          drift_metrics.p_value, drift_metrics.is_drift, drift_metrics.reference_mean,
                          drift_metrics.current_mean, drift_metrics.reference_std, drift_metrics.current_std))
                    conn.commit()
                    conn.close()
                    
                    # Create alert if drift detected
                    if drift_metrics.is_drift:
                        self._create_alert(
                            AlertLevel.WARNING,
                            f"Data drift detected for feature {feature} in model {model_name}",
                            "drift",
                            model_name,
                            self.thresholds['drift_p_value'],
                            drift_metrics.p_value,
                            {'feature': feature, 'drift_score': drift_metrics.drift_score}
                        )
                        
                except Exception as e:
                    self.logger.error(f"Error detecting drift for feature {feature}: {str(e)}")
    
    def _create_alert(self, 
                     level: AlertLevel,
                     message: str,
                     metric_type: str,
                     model_name: str,
                     threshold: float,
                     current_value: float,
                     details: Dict[str, Any]):
        """Create and store alert"""
        
        alert = Alert(
            timestamp=datetime.now(),
            level=level,
            message=message,
            metric_type=metric_type,
            model_name=model_name,
            threshold=threshold,
            current_value=current_value,
            details=details
        )
        
        self.alerts.append(alert)
        
        # Store in database
        conn = sqlite3.connect(self.monitoring_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alerts 
            (timestamp, level, message, metric_type, model_name, threshold, current_value, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (alert.timestamp, alert.level.value, alert.message, alert.metric_type,
              alert.model_name, alert.threshold, alert.current_value, json.dumps(alert.details)))
        conn.commit()
        conn.close()
        
        # Log alert
        self.logger.warning(f"ALERT [{level.value.upper()}]: {message}")
        
        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {str(e)}")
        
        # Check if retraining is needed
        if (level == AlertLevel.CRITICAL and 
            self.enable_auto_retrain and 
            metric_type in ['performance', 'drift']):
            self._trigger_retraining(model_name)
    
    def _trigger_retraining(self, model_name: str):
        """Trigger automatic model retraining"""
        self.logger.info(f"Triggering retraining for model {model_name}")
        
        try:
            # Create retraining pipeline
            pipeline = MLTrainingPipeline(
                model_type=model_name.split('_')[0],  # Extract model type from name
                output_dir=str(self.models_dir),
                enable_hyperparameter_tuning=True,
                enable_cross_validation=True
            )
            
            # Get recent training data
            # In practice, you'd implement data retrieval logic here
            
            # Schedule retraining in background
            retraining_thread = threading.Thread(
                target=self._retrain_model,
                args=(pipeline, model_name),
                daemon=True
            )
            retraining_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error triggering retraining: {str(e)}")
    
    def _retrain_model(self, pipeline: MLTrainingPipeline, model_name: str):
        """Retrain model in background"""
        try:
            # This is a placeholder - implement actual retraining logic
            self.logger.info(f"Retraining model {model_name}...")
            
            # After retraining, reload the model
            self._load_models()
            
            # Create success alert
            self._create_alert(
                AlertLevel.INFO,
                f"Model {model_name} successfully retrained",
                "retraining",
                model_name,
                0.0,
                1.0,
                {'status': 'success'}
            )
            
        except Exception as e:
            self.logger.error(f"Error retraining model {model_name}: {str(e)}")
            
            # Create failure alert
            self._create_alert(
                AlertLevel.CRITICAL,
                f"Failed to retrain model {model_name}: {str(e)}",
                "retraining",
                model_name,
                0.0,
                0.0,
                {'status': 'failed', 'error': str(e)}
            )
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Check each model
                for model_name in self.models.keys():
                    self.check_model_performance(model_name)
                    self.check_data_drift(model_name)
                
                # Sleep until next check
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(self.monitoring_interval)
    
    def start_monitoring(self):
        """Start monitoring thread"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring thread"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            self.logger.info("Monitoring stopped")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def get_model_metrics_history(self, model_name: str, hours: int = 24) -> pd.DataFrame:
        """Get model metrics history"""
        conn = sqlite3.connect(self.monitoring_db)
        query = '''
            SELECT * FROM model_metrics 
            WHERE model_name = ? AND timestamp > ?
            ORDER BY timestamp DESC
        '''
        
        since = datetime.now() - timedelta(hours=hours)
        df = pd.read_sql_query(query, conn, params=(model_name, since))
        conn.close()
        
        return df
    
    def get_drift_metrics_history(self, hours: int = 24) -> pd.DataFrame:
        """Get drift metrics history"""
        conn = sqlite3.connect(self.monitoring_db)
        query = '''
            SELECT * FROM drift_metrics 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        '''
        
        since = datetime.now() - timedelta(hours=hours)
        df = pd.read_sql_query(query, conn, params=(since,))
        conn.close()
        
        return df
    
    def get_alerts_history(self, hours: int = 24) -> pd.DataFrame:
        """Get alerts history"""
        conn = sqlite3.connect(self.monitoring_db)
        query = '''
            SELECT * FROM alerts 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        '''
        
        since = datetime.now() - timedelta(hours=hours)
        df = pd.read_sql_query(query, conn, params=(since,))
        conn.close()
        
        return df
    
    def create_monitoring_dashboard(self, model_name: str = None) -> go.Figure:
        """Create monitoring dashboard"""
        
        if model_name:
            # Single model dashboard
            metrics_df = self.get_model_metrics_history(model_name)
            
            if metrics_df.empty:
                return go.Figure().add_annotation(text="No data available")
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("Model Performance", "Processing Time", "Confidence", "Prediction Count"),
                specs=[[{"secondary_y": True}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Performance metrics
            fig.add_trace(
                go.Scatter(x=metrics_df['timestamp'], y=metrics_df['mae'], name='MAE'),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=metrics_df['timestamp'], y=metrics_df['r2'], name='R2'),
                row=1, col=1, secondary_y=True
            )
            
            # Processing time
            fig.add_trace(
                go.Scatter(x=metrics_df['timestamp'], y=metrics_df['processing_time_ms'], name='Latency'),
                row=1, col=2
            )
            
            # Confidence
            fig.add_trace(
                go.Scatter(x=metrics_df['timestamp'], y=metrics_df['avg_confidence'], name='Confidence'),
                row=2, col=1
            )
            
            # Prediction count
            fig.add_trace(
                go.Scatter(x=metrics_df['timestamp'], y=metrics_df['prediction_count'], name='Predictions'),
                row=2, col=2
            )
            
            fig.update_layout(title=f"Model Monitoring Dashboard - {model_name}")
            
        else:
            # Multi-model dashboard
            fig = go.Figure()
            fig.add_annotation(text="Multi-model dashboard - select a specific model")
        
        return fig
    
    def generate_monitoring_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'period_hours': hours,
            'models': {},
            'alerts': [],
            'drift_summary': {},
            'recommendations': []
        }
        
        # Model performance summary
        for model_name in self.models.keys():
            metrics_df = self.get_model_metrics_history(model_name, hours)
            
            if not metrics_df.empty:
                latest_metrics = metrics_df.iloc[0]
                report['models'][model_name] = {
                    'latest_mae': latest_metrics['mae'],
                    'latest_r2': latest_metrics['r2'],
                    'avg_confidence': latest_metrics['avg_confidence'],
                    'prediction_count': metrics_df['prediction_count'].sum(),
                    'avg_processing_time': metrics_df['processing_time_ms'].mean()
                }
        
        # Alerts summary
        alerts_df = self.get_alerts_history(hours)
        report['alerts'] = alerts_df.to_dict('records') if not alerts_df.empty else []
        
        # Drift summary
        drift_df = self.get_drift_metrics_history(hours)
        if not drift_df.empty:
            drift_summary = drift_df.groupby('feature_name').agg({
                'is_drift': 'sum',
                'drift_score': 'mean'
            }).to_dict()
            report['drift_summary'] = drift_summary
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate monitoring recommendations"""
        recommendations = []
        
        # Check for models with poor performance
        for model_name, metrics in report['models'].items():
            if metrics['latest_r2'] < 0.8:
                recommendations.append(f"Consider retraining {model_name} - R2 score is {metrics['latest_r2']:.3f}")
            
            if metrics['avg_confidence'] < 0.7:
                recommendations.append(f"Review {model_name} confidence - average is {metrics['avg_confidence']:.3f}")
        
        # Check for drift
        if report['drift_summary']:
            for feature, stats in report['drift_summary'].items():
                if stats['is_drift'] > 0:
                    recommendations.append(f"Address data drift in feature {feature}")
        
        # Check alerts
        critical_alerts = [a for a in report['alerts'] if a['level'] == 'critical']
        if critical_alerts:
            recommendations.append("Address critical alerts immediately")
        
        return recommendations