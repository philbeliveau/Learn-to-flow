"""
Time Feature Extraction for Manufacturing Data
Specialized for French business calendar and manufacturing schedules
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import holidays
from sklearn.base import BaseEstimator, TransformerMixin
from config.ml_config import config

class TimeFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract time-based features for manufacturing forecasting"""
    
    def __init__(self, 
                 include_holidays: bool = True,
                 include_business_calendar: bool = True,
                 include_manufacturing_shifts: bool = True,
                 include_cyclical_encoding: bool = True):
        """
        Initialize time feature extractor
        
        Args:
            include_holidays: Include French holiday indicators
            include_business_calendar: Include business day features
            include_manufacturing_shifts: Include shift pattern features
            include_cyclical_encoding: Include cyclical encodings for time components
        """
        self.include_holidays = include_holidays
        self.include_business_calendar = include_business_calendar
        self.include_manufacturing_shifts = include_manufacturing_shifts
        self.include_cyclical_encoding = include_cyclical_encoding
        
        # French holidays
        self.french_holidays = holidays.France()
        
        # Manufacturing configuration
        self.manufacturing_config = config.manufacturing
    
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        """Fit the transformer (no-op for time features)"""
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform dataframe by adding time-based features
        
        Args:
            X: Input dataframe with datetime index or datetime column
            
        Returns:
            Transformed dataframe with time features
        """
        if not isinstance(X.index, pd.DatetimeIndex):
            raise ValueError("Input must have datetime index")
        
        result = X.copy()
        
        # Basic time features
        result['hour'] = X.index.hour
        result['day_of_week'] = X.index.dayofweek
        result['day_of_month'] = X.index.day
        result['month'] = X.index.month
        result['quarter'] = X.index.quarter
        result['week_of_year'] = X.index.week
        result['day_of_year'] = X.index.dayofyear
        
        # Weekend indicators
        result['is_weekend'] = (X.index.dayofweek >= 5).astype(int)
        result['is_monday'] = (X.index.dayofweek == 0).astype(int)
        result['is_friday'] = (X.index.dayofweek == 4).astype(int)
        
        # Business calendar features
        if self.include_business_calendar:
            result = self._add_business_features(result)
        
        # Holiday features
        if self.include_holidays:
            result = self._add_holiday_features(result)
        
        # Manufacturing shift features
        if self.include_manufacturing_shifts:
            result = self._add_shift_features(result)
        
        # Cyclical encoding
        if self.include_cyclical_encoding:
            result = self._add_cyclical_features(result)
        
        return result
    
    def _add_business_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add business calendar features"""
        # Business day indicator
        df['is_business_day'] = df.index.map(lambda x: x.weekday() < 5).astype(int)
        
        # Days since/until weekend
        df['days_since_weekend'] = df.index.map(self._days_since_weekend)
        df['days_until_weekend'] = df.index.map(self._days_until_weekend)
        
        # Month start/end indicators
        df['is_month_start'] = df.index.map(lambda x: x.day <= 5).astype(int)
        df['is_month_end'] = df.index.map(lambda x: x.day >= 25).astype(int)
        
        # Quarter start/end indicators
        df['is_quarter_start'] = df.index.map(
            lambda x: x.month in [1, 4, 7, 10] and x.day <= 5
        ).astype(int)
        df['is_quarter_end'] = df.index.map(
            lambda x: x.month in [3, 6, 9, 12] and x.day >= 25
        ).astype(int)
        
        return df
    
    def _add_holiday_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add French holiday features"""
        # Holiday indicator
        df['is_holiday'] = df.index.map(
            lambda x: x.date() in self.french_holidays
        ).astype(int)
        
        # Days since/until holiday
        df['days_since_holiday'] = df.index.map(self._days_since_holiday)
        df['days_until_holiday'] = df.index.map(self._days_until_holiday)
        
        # Holiday proximity (within 3 days)
        df['near_holiday'] = ((df['days_since_holiday'] <= 3) | 
                              (df['days_until_holiday'] <= 3)).astype(int)
        
        # Specific holiday types
        df['is_christmas_period'] = df.index.map(
            lambda x: x.month == 12 and x.day >= 20
        ).astype(int)
        df['is_new_year_period'] = df.index.map(
            lambda x: x.month == 1 and x.day <= 10
        ).astype(int)
        df['is_summer_holiday'] = df.index.map(
            lambda x: x.month in [7, 8]
        ).astype(int)
        
        return df
    
    def _add_shift_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add manufacturing shift features"""
        shifts = self.manufacturing_config['business_hours']['shifts']
        
        # Current shift
        df['current_shift'] = df.index.map(self._get_current_shift)
        
        # Shift indicators
        for shift in shifts:
            df[f'is_{shift["name"]}_shift'] = (
                df['current_shift'] == shift['name']
            ).astype(int)
        
        # Production hours indicator
        business_hours = self.manufacturing_config['business_hours']
        df['is_production_hours'] = df.index.map(
            lambda x: business_hours['start'] <= x.hour < business_hours['end']
        ).astype(int)
        
        # Shift transitions (productivity changes)
        df['is_shift_start'] = df.index.map(
            lambda x: x.hour in [6, 14, 22] and x.minute == 0
        ).astype(int)
        
        # Maintenance windows
        df['is_maintenance_window'] = df.index.map(
            self._is_maintenance_window
        ).astype(int)
        
        return df
    
    def _add_cyclical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add cyclical encodings for time components"""
        # Hour cyclical encoding
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Day of week cyclical encoding
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Month cyclical encoding
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Day of year cyclical encoding
        df['doy_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['doy_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        
        return df
    
    def _days_since_weekend(self, dt: datetime) -> int:
        """Calculate days since last weekend"""
        days_since = (dt.weekday() + 1) % 7
        return days_since if days_since <= 6 else 0
    
    def _days_until_weekend(self, dt: datetime) -> int:
        """Calculate days until next weekend"""
        return (5 - dt.weekday()) % 7
    
    def _days_since_holiday(self, dt: datetime) -> int:
        """Calculate days since last holiday"""
        for i in range(1, 31):  # Check last 30 days
            check_date = dt - timedelta(days=i)
            if check_date.date() in self.french_holidays:
                return i
        return 30  # Default if no holiday found
    
    def _days_until_holiday(self, dt: datetime) -> int:
        """Calculate days until next holiday"""
        for i in range(1, 31):  # Check next 30 days
            check_date = dt + timedelta(days=i)
            if check_date.date() in self.french_holidays:
                return i
        return 30  # Default if no holiday found
    
    def _get_current_shift(self, dt: datetime) -> str:
        """Determine current manufacturing shift"""
        hour = dt.hour
        
        if 6 <= hour < 14:
            return 'morning'
        elif 14 <= hour < 22:
            return 'afternoon'
        else:
            return 'night'
    
    def _is_maintenance_window(self, dt: datetime) -> bool:
        """Check if timestamp is in maintenance window"""
        maintenance_windows = self.manufacturing_config['maintenance_windows']
        
        for window in maintenance_windows:
            if window['day'] == 'sunday' and dt.weekday() == 6:
                return window['start'] <= dt.hour < window['end']
            elif window['day'] == 'saturday' and dt.weekday() == 5:
                return window['start'] <= dt.hour < window['end']
        
        return False

class LagFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract lag features for time series data"""
    
    def __init__(self, lag_config: Dict[str, List[int]]):
        """
        Initialize lag feature extractor
        
        Args:
            lag_config: Dictionary mapping column names to lag periods
        """
        self.lag_config = lag_config
    
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        """Fit the transformer"""
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform dataframe by adding lag features"""
        result = X.copy()
        
        for column, lags in self.lag_config.items():
            if column in X.columns:
                for lag in lags:
                    result[f'{column}_lag_{lag}'] = X[column].shift(lag)
        
        return result

class RollingFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract rolling window features"""
    
    def __init__(self, rolling_config: Dict[str, Dict]):
        """
        Initialize rolling feature extractor
        
        Args:
            rolling_config: Dictionary with rolling window configurations
        """
        self.rolling_config = rolling_config
    
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        """Fit the transformer"""
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform dataframe by adding rolling features"""
        result = X.copy()
        
        for column, config in self.rolling_config.items():
            if column in X.columns:
                for window in config['windows']:
                    rolling_data = X[column].rolling(window=window)
                    
                    for func in config['functions']:
                        if func == 'mean':
                            result[f'{column}_rolling_{window}_mean'] = rolling_data.mean()
                        elif func == 'std':
                            result[f'{column}_rolling_{window}_std'] = rolling_data.std()
                        elif func == 'min':
                            result[f'{column}_rolling_{window}_min'] = rolling_data.min()
                        elif func == 'max':
                            result[f'{column}_rolling_{window}_max'] = rolling_data.max()
                        elif func == 'trend':
                            # Simple trend calculation
                            result[f'{column}_rolling_{window}_trend'] = (
                                rolling_data.mean() - rolling_data.mean().shift(window)
                            )
        
        return result