# 🔄 DATA ENGINEERING - EZBI ANALYTICS

## 🎯 PHILOSOPHIE DATA ENGINEERING

### Vision Data-Driven
```
📊 "From Raw Data to Intelligent Insights"

Principes Directeurs:
├── Manufacturing-First: Optimisé pour données industrielles
├── Real-time Processing: Ingestion et traitement temps réel
├── Data Quality: Validation et nettoyage automatique
├── Scalable Architecture: Croissance horizontale
└── Privacy by Design: RGPD native et sécurisé
```

### Pipeline Overview
```
🔄 Data Flow Architecture

Excel Files → Smart Parser → Validation → Enrichment → Storage → ML Pipeline → Predictions

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                DATA SOURCES                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Excel Files  │  ERP Systems  │  Bank APIs  │  Manual Input  │  External APIs     │
│  (Upload)     │  (Sage, SAP)  │  (Open Banking) │  (Forms)    │  (Economic Data) │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                            ┌───────────▼───────────┐
                            │    INGESTION LAYER    │
                            │  - File Processing    │
                            │  - API Connectors     │
                            │  - Real-time Streams  │
                            │  - Batch Processing   │
                            └───────────┬───────────┘
                                        │
                            ┌───────────▼───────────┐
                            │   VALIDATION LAYER    │
                            │  - Schema Validation  │
                            │  - Data Quality       │
                            │  - Business Rules     │
                            │  - Anomaly Detection  │
                            └───────────┬───────────┘
                                        │
                            ┌───────────▼───────────┐
                            │  TRANSFORMATION LAYER │
                            │  - Data Enrichment    │
                            │  - Feature Engineering│
                            │  - Normalization      │
                            │  - Aggregation        │
                            └───────────┬───────────┘
                                        │
                            ┌───────────▼───────────┐
                            │    STORAGE LAYER      │
                            │  - PostgreSQL (OLTP)  │
                            │  - InfluxDB (Time Series) │
                            │  - S3 (Data Lake)     │
                            │  - Redis (Cache)      │
                            └───────────┬───────────┘
                                        │
                            ┌───────────▼───────────┐
                            │    ML PIPELINE        │
                            │  - Feature Store      │
                            │  - Model Training     │
                            │  - Inference Engine   │
                            │  - Model Monitoring   │
                            └───────────────────────┘
```

---

## 📊 MODÈLE DE DONNÉES

### Schéma Principal
```sql
-- 🏭 Manufacturing Data Model pour EZBI

-- Companies & Users
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    size_category VARCHAR(50) NOT NULL, -- 'PME', 'ETI', 'Grand Groupe'
    siret VARCHAR(14) UNIQUE NOT NULL,
    address JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'admin', 'user', 'viewer'
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Core Financial Data
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    transaction_date DATE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'sale', 'purchase', 'expense', 'payment'
    category VARCHAR(100) NOT NULL,
    description TEXT,
    customer_id UUID REFERENCES customers(id),
    supplier_id UUID REFERENCES suppliers(id),
    payment_terms INTEGER, -- Days
    payment_method VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'EUR',
    tax_rate DECIMAL(5,2),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_transactions_company_date (company_id, transaction_date),
    INDEX idx_transactions_type (type),
    INDEX idx_transactions_category (category)
);

-- Manufacturing-Specific Tables
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'B2B', 'B2C', 'Government'
    sector VARCHAR(100),
    payment_terms INTEGER DEFAULT 30,
    credit_limit DECIMAL(15,2),
    risk_score DECIMAL(3,2), -- 0.0 to 1.0
    historical_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customers_company (company_id),
    INDEX idx_customers_risk (risk_score)
);

CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL, -- 'raw_materials', 'equipment', 'services'
    payment_terms INTEGER DEFAULT 30,
    reliability_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Manufacturing Production Data
CREATE TABLE production_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    cycle_start DATE NOT NULL,
    cycle_end DATE,
    production_volume INTEGER,
    product_category VARCHAR(100),
    cost_per_unit DECIMAL(10,2),
    efficiency_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_production_company_date (company_id, cycle_start)
);

-- Predictions & ML Results
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    prediction_date DATE NOT NULL,
    target_date DATE NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'prophet', 'lstm', 'ensemble'
    model_version VARCHAR(20) NOT NULL,
    predicted_value DECIMAL(15,2) NOT NULL,
    confidence_interval_lower DECIMAL(15,2),
    confidence_interval_upper DECIMAL(15,2),
    confidence_score DECIMAL(3,2),
    actual_value DECIMAL(15,2), -- Filled when actual data arrives
    prediction_accuracy DECIMAL(5,2), -- Calculated post-facto
    features_used JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_predictions_company_target (company_id, target_date),
    INDEX idx_predictions_model (model_type, model_version),
    INDEX idx_predictions_accuracy (prediction_accuracy)
);

-- Time Series Data (InfluxDB Schema)
CREATE TABLE time_series_metrics (
    time TIMESTAMP NOT NULL,
    company_id UUID NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'daily_sales', 'cash_flow', 'receivables'
    value DECIMAL(15,2) NOT NULL,
    metadata JSONB DEFAULT '{}',
    PRIMARY KEY (time, company_id, metric_type)
);

-- Feature Store
CREATE TABLE feature_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(15,4),
    feature_type VARCHAR(50) NOT NULL, -- 'numeric', 'categorical', 'boolean'
    computation_date DATE NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_features_company_name (company_id, feature_name),
    INDEX idx_features_date (computation_date)
);
```

### Manufacturing-Specific Features
```python
# 🏭 Manufacturing Feature Engineering

class ManufacturingFeatureEngine:
    """Engine de features spécialisé pour PME manufacturières"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.feature_definitions = {
            # Cyclicité Manufacturing
            'seasonal_production_factor': self._calculate_seasonal_factor,
            'manufacturing_cycle_position': self._get_cycle_position,
            'order_backlog_ratio': self._calculate_backlog_ratio,
            
            # Flux de Trésorerie Manufacturing
            'working_capital_velocity': self._calculate_wc_velocity,
            'payment_terms_weighted_avg': self._calculate_payment_terms,
            'supplier_payment_optimization': self._calculate_supplier_optimization,
            
            # Risque Client Manufacturing
            'customer_concentration_risk': self._calculate_concentration_risk,
            'sector_exposure_risk': self._calculate_sector_exposure,
            'geographic_risk_distribution': self._calculate_geographic_risk,
            
            # Performance Opérationnelle
            'production_efficiency_trend': self._calculate_efficiency_trend,
            'capacity_utilization_rate': self._calculate_capacity_utilization,
            'inventory_turnover_optimization': self._calculate_inventory_turnover,
            
            # Indicateurs Prédictifs
            'lead_time_variability': self._calculate_lead_time_variability,
            'demand_forecast_accuracy': self._calculate_demand_accuracy,
            'supply_chain_stability': self._calculate_supply_stability
        }
    
    def compute_all_features(self, company_id: str, date: datetime) -> Dict[str, float]:
        """Compute all manufacturing features for a company"""
        features = {}
        
        for feature_name, compute_func in self.feature_definitions.items():
            try:
                features[feature_name] = compute_func(company_id, date)
            except Exception as e:
                logger.error(f"Error computing {feature_name}: {e}")
                features[feature_name] = None
        
        return features
    
    def _calculate_seasonal_factor(self, company_id: str, date: datetime) -> float:
        """Calculate seasonal production factor"""
        query = """
        SELECT 
            EXTRACT(MONTH FROM cycle_start) as month,
            AVG(production_volume) as avg_volume
        FROM production_cycles
        WHERE company_id = %s
        AND cycle_start >= %s - INTERVAL '3 years'
        GROUP BY EXTRACT(MONTH FROM cycle_start)
        """
        
        monthly_data = self.db.execute(query, (company_id, date))
        current_month = date.month
        
        if not monthly_data:
            return 1.0
        
        current_month_avg = next(
            (data['avg_volume'] for data in monthly_data if data['month'] == current_month),
            None
        )
        
        if current_month_avg is None:
            return 1.0
        
        yearly_avg = sum(data['avg_volume'] for data in monthly_data) / len(monthly_data)
        
        return current_month_avg / yearly_avg if yearly_avg > 0 else 1.0
    
    def _calculate_working_capital_velocity(self, company_id: str, date: datetime) -> float:
        """Calculate working capital velocity"""
        query = """
        SELECT 
            SUM(CASE WHEN type IN ('sale') THEN amount ELSE 0 END) as sales,
            SUM(CASE WHEN type IN ('purchase') THEN amount ELSE 0 END) as purchases,
            AVG(CASE WHEN type IN ('sale') THEN payment_terms ELSE NULL END) as avg_payment_terms
        FROM transactions
        WHERE company_id = %s
        AND transaction_date >= %s - INTERVAL '90 days'
        AND transaction_date <= %s
        """
        
        result = self.db.execute(query, (company_id, date, date))[0]
        
        if not result['sales'] or not result['purchases']:
            return 0.0
        
        working_capital = result['sales'] - result['purchases']
        payment_cycle = result['avg_payment_terms'] or 30
        
        return (working_capital / payment_cycle) * 365 if payment_cycle > 0 else 0.0
    
    def _calculate_customer_concentration_risk(self, company_id: str, date: datetime) -> float:
        """Calculate customer concentration risk (Herfindahl Index)"""
        query = """
        SELECT 
            customer_id,
            SUM(amount) as total_amount
        FROM transactions
        WHERE company_id = %s
        AND type = 'sale'
        AND transaction_date >= %s - INTERVAL '12 months'
        AND transaction_date <= %s
        GROUP BY customer_id
        """
        
        customer_sales = self.db.execute(query, (company_id, date, date))
        
        if not customer_sales:
            return 0.0
        
        total_sales = sum(sale['total_amount'] for sale in customer_sales)
        
        if total_sales == 0:
            return 0.0
        
        # Herfindahl Index
        herfindahl = sum(
            (sale['total_amount'] / total_sales) ** 2 
            for sale in customer_sales
        )
        
        return herfindahl
    
    def _calculate_production_efficiency_trend(self, company_id: str, date: datetime) -> float:
        """Calculate production efficiency trend"""
        query = """
        SELECT 
            efficiency_score,
            cycle_start
        FROM production_cycles
        WHERE company_id = %s
        AND cycle_start >= %s - INTERVAL '6 months'
        AND cycle_start <= %s
        ORDER BY cycle_start
        """
        
        efficiency_data = self.db.execute(query, (company_id, date, date))
        
        if len(efficiency_data) < 2:
            return 0.0
        
        # Linear regression slope
        x = list(range(len(efficiency_data)))
        y = [data['efficiency_score'] for data in efficiency_data]
        
        n = len(x)
        slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / \
                (n * sum(x[i] ** 2 for i in range(n)) - sum(x) ** 2)
        
        return slope
```

---

## 🔄 PIPELINE DE DONNÉES

### Architecture ETL
```python
# 🔄 ETL Pipeline pour EZBI Analytics

import asyncio
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

class DataSourceType(Enum):
    EXCEL_UPLOAD = "excel_upload"
    ERP_CONNECTOR = "erp_connector"
    BANK_API = "bank_api"
    MANUAL_INPUT = "manual_input"
    EXTERNAL_API = "external_api"

@dataclass
class DataQualityMetrics:
    completeness: float
    accuracy: float
    consistency: float
    timeliness: float
    validity: float
    overall_score: float

class EZBIDataPipeline:
    """Pipeline de données principal pour EZBI Analytics"""
    
    def __init__(self, db_connection, redis_client, s3_client):
        self.db = db_connection
        self.redis = redis_client
        self.s3 = s3_client
        self.logger = logging.getLogger(__name__)
    
    async def process_data_source(self, source_type: DataSourceType, 
                                 data: bytes, metadata: Dict) -> Dict:
        """Process data from various sources"""
        
        pipeline_id = f"pipeline_{datetime.now().isoformat()}"
        
        try:
            # 1. Ingestion
            raw_data = await self._ingest_data(source_type, data, metadata)
            
            # 2. Validation
            validation_results = await self._validate_data(raw_data, source_type)
            
            if not validation_results['is_valid']:
                return {
                    'success': False,
                    'pipeline_id': pipeline_id,
                    'error': 'Data validation failed',
                    'validation_results': validation_results
                }
            
            # 3. Transformation
            transformed_data = await self._transform_data(raw_data, source_type)
            
            # 4. Feature Engineering
            enriched_data = await self._enrich_data(transformed_data, metadata)
            
            # 5. Storage
            storage_results = await self._store_data(enriched_data, metadata)
            
            # 6. Quality Metrics
            quality_metrics = await self._calculate_quality_metrics(enriched_data)
            
            # 7. Trigger ML Pipeline
            if quality_metrics.overall_score >= 0.8:
                await self._trigger_ml_pipeline(metadata['company_id'])
            
            return {
                'success': True,
                'pipeline_id': pipeline_id,
                'records_processed': len(enriched_data),
                'quality_metrics': quality_metrics,
                'storage_results': storage_results
            }
            
        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")
            return {
                'success': False,
                'pipeline_id': pipeline_id,
                'error': str(e)
            }
    
    async def _ingest_data(self, source_type: DataSourceType, 
                          data: bytes, metadata: Dict) -> pd.DataFrame:
        """Ingest data from various sources"""
        
        if source_type == DataSourceType.EXCEL_UPLOAD:
            return await self._ingest_excel(data, metadata)
        
        elif source_type == DataSourceType.ERP_CONNECTOR:
            return await self._ingest_erp(data, metadata)
        
        elif source_type == DataSourceType.BANK_API:
            return await self._ingest_bank_api(data, metadata)
        
        elif source_type == DataSourceType.EXTERNAL_API:
            return await self._ingest_external_api(data, metadata)
        
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    async def _ingest_excel(self, data: bytes, metadata: Dict) -> pd.DataFrame:
        """Smart Excel ingestion with AI-powered structure detection"""
        
        # Save to S3 for backup
        file_key = f"raw_data/{metadata['company_id']}/excel_{datetime.now().isoformat()}.xlsx"
        await self.s3.put_object(Bucket='ezbi-data-lake', Key=file_key, Body=data)
        
        # Load Excel file
        excel_data = pd.read_excel(io.BytesIO(data), sheet_name=None)
        
        # Smart sheet detection
        main_sheet = await self._detect_main_sheet(excel_data)
        df = excel_data[main_sheet]
        
        # Smart column mapping
        column_mapping = await self._detect_column_mapping(df)
        df = df.rename(columns=column_mapping)
        
        # Data type inference
        df = await self._infer_data_types(df)
        
        return df
    
    async def _detect_main_sheet(self, excel_data: Dict[str, pd.DataFrame]) -> str:
        """Detect the main data sheet using AI"""
        
        sheet_scores = {}
        
        for sheet_name, df in excel_data.items():
            score = 0
            
            # More rows = higher score
            score += min(len(df) / 100, 10)
            
            # More columns = higher score
            score += min(len(df.columns) / 5, 5)
            
            # Manufacturing keywords
            manufacturing_keywords = [
                'date', 'montant', 'amount', 'client', 'customer',
                'fournisseur', 'supplier', 'vente', 'sale', 'achat',
                'facture', 'invoice', 'paiement', 'payment'
            ]
            
            text_content = ' '.join(df.columns.astype(str)).lower()
            keyword_matches = sum(1 for keyword in manufacturing_keywords 
                                if keyword in text_content)
            score += keyword_matches * 2
            
            # Avoid summary sheets
            if 'summary' in sheet_name.lower() or 'résumé' in sheet_name.lower():
                score -= 5
            
            sheet_scores[sheet_name] = score
        
        return max(sheet_scores, key=sheet_scores.get)
    
    async def _detect_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detect column mapping using NLP"""
        
        mapping = {}
        
        # Standard mappings for French manufacturing
        column_patterns = {
            'transaction_date': [
                'date', 'date_transaction', 'date_facture', 'date_operation',
                'transaction_date', 'invoice_date', 'operation_date'
            ],
            'amount': [
                'montant', 'amount', 'valeur', 'value', 'total', 'prix', 'price'
            ],
            'customer_name': [
                'client', 'customer', 'nom_client', 'customer_name',
                'destinataire', 'recipient'
            ],
            'supplier_name': [
                'fournisseur', 'supplier', 'nom_fournisseur', 'supplier_name',
                'vendeur', 'vendor'
            ],
            'description': [
                'description', 'libelle', 'label', 'designation',
                'produit', 'product', 'service'
            ],
            'payment_terms': [
                'delai_paiement', 'payment_terms', 'terms', 'echeance',
                'due_date', 'payment_delay'
            ]
        }
        
        for col in df.columns:
            col_lower = col.lower()
            
            for standard_name, patterns in column_patterns.items():
                for pattern in patterns:
                    if pattern in col_lower:
                        mapping[col] = standard_name
                        break
                if col in mapping:
                    break
        
        return mapping
    
    async def _validate_data(self, df: pd.DataFrame, 
                           source_type: DataSourceType) -> Dict:
        """Comprehensive data validation"""
        
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        # Required columns check
        required_columns = ['transaction_date', 'amount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"Missing required columns: {missing_columns}")
        
        # Data type validation
        if 'transaction_date' in df.columns:
            try:
                df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            except:
                validation_results['is_valid'] = False
                validation_results['errors'].append("Invalid date format in transaction_date")
        
        if 'amount' in df.columns:
            try:
                df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
                null_amounts = df['amount'].isnull().sum()
                if null_amounts > 0:
                    validation_results['warnings'].append(f"{null_amounts} invalid amounts converted to NULL")
            except:
                validation_results['is_valid'] = False
                validation_results['errors'].append("Invalid numeric format in amount")
        
        # Business rules validation
        if 'amount' in df.columns:
            # Check for unrealistic amounts
            extreme_amounts = df[df['amount'].abs() > 10000000]  # 10M EUR
            if len(extreme_amounts) > 0:
                validation_results['warnings'].append(f"{len(extreme_amounts)} extreme amounts detected")
        
        # Date range validation
        if 'transaction_date' in df.columns:
            future_dates = df[df['transaction_date'] > datetime.now()]
            if len(future_dates) > 0:
                validation_results['warnings'].append(f"{len(future_dates)} future dates detected")
        
        # Stats
        validation_results['stats'] = {
            'total_records': len(df),
            'null_values': df.isnull().sum().to_dict(),
            'date_range': {
                'min': df['transaction_date'].min() if 'transaction_date' in df.columns else None,
                'max': df['transaction_date'].max() if 'transaction_date' in df.columns else None
            }
        }
        
        return validation_results
    
    async def _transform_data(self, df: pd.DataFrame, 
                            source_type: DataSourceType) -> pd.DataFrame:
        """Transform data to standard format"""
        
        # Standardize transaction types
        if 'description' in df.columns:
            df['type'] = df['description'].apply(self._classify_transaction_type)
        else:
            df['type'] = 'unknown'
        
        # Standardize currency
        if 'currency' not in df.columns:
            df['currency'] = 'EUR'
        
        # Add metadata
        df['data_source'] = source_type.value
        df['ingestion_timestamp'] = datetime.now()
        
        # Clean and normalize text fields
        text_columns = ['description', 'customer_name', 'supplier_name']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].str.strip().str.title()
        
        return df
    
    def _classify_transaction_type(self, description: str) -> str:
        """Classify transaction type from description"""
        
        if pd.isna(description):
            return 'unknown'
        
        desc_lower = description.lower()
        
        # Sale indicators
        sale_keywords = ['vente', 'facture', 'sale', 'invoice', 'revenus', 'revenue']
        if any(keyword in desc_lower for keyword in sale_keywords):
            return 'sale'
        
        # Purchase indicators
        purchase_keywords = ['achat', 'purchase', 'fournisseur', 'supplier', 'commande']
        if any(keyword in desc_lower for keyword in purchase_keywords):
            return 'purchase'
        
        # Expense indicators
        expense_keywords = ['charge', 'expense', 'frais', 'cost', 'salaire', 'salary']
        if any(keyword in desc_lower for keyword in expense_keywords):
            return 'expense'
        
        # Payment indicators
        payment_keywords = ['paiement', 'payment', 'règlement', 'settlement']
        if any(keyword in desc_lower for keyword in payment_keywords):
            return 'payment'
        
        return 'unknown'
    
    async def _enrich_data(self, df: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        """Enrich data with additional features"""
        
        # Add company information
        df['company_id'] = metadata['company_id']
        
        # Manufacturing seasonality
        if 'transaction_date' in df.columns:
            df['month'] = df['transaction_date'].dt.month
            df['quarter'] = df['transaction_date'].dt.quarter
            df['day_of_week'] = df['transaction_date'].dt.dayofweek
            df['is_month_end'] = (df['transaction_date'].dt.day >= 25)
        
        # Business day indicators
        df['is_business_day'] = df['transaction_date'].dt.dayofweek < 5
        
        # Amount categorization
        if 'amount' in df.columns:
            df['amount_category'] = pd.cut(
                df['amount'].abs(), 
                bins=[0, 1000, 10000, 100000, float('inf')],
                labels=['small', 'medium', 'large', 'enterprise']
            )
        
        return df
    
    async def _store_data(self, df: pd.DataFrame, metadata: Dict) -> Dict:
        """Store processed data in multiple storage systems"""
        
        results = {}
        
        # 1. PostgreSQL (OLTP)
        try:
            # Insert into transactions table
            df.to_sql('transactions', self.db, if_exists='append', index=False)
            results['postgresql'] = {'success': True, 'records': len(df)}
        except Exception as e:
            results['postgresql'] = {'success': False, 'error': str(e)}
        
        # 2. InfluxDB (Time Series)
        try:
            await self._store_time_series(df, metadata)
            results['influxdb'] = {'success': True, 'records': len(df)}
        except Exception as e:
            results['influxdb'] = {'success': False, 'error': str(e)}
        
        # 3. S3 Data Lake
        try:
            processed_key = f"processed_data/{metadata['company_id']}/transactions_{datetime.now().isoformat()}.parquet"
            df.to_parquet(f"s3://ezbi-data-lake/{processed_key}")
            results['s3'] = {'success': True, 'key': processed_key}
        except Exception as e:
            results['s3'] = {'success': False, 'error': str(e)}
        
        # 4. Redis Cache
        try:
            # Cache recent data for fast access
            cache_key = f"recent_data:{metadata['company_id']}"
            recent_data = df.tail(100).to_json()
            await self.redis.setex(cache_key, 3600, recent_data)  # 1 hour TTL
            results['redis'] = {'success': True, 'cached_records': 100}
        except Exception as e:
            results['redis'] = {'success': False, 'error': str(e)}
        
        return results
    
    async def _calculate_quality_metrics(self, df: pd.DataFrame) -> DataQualityMetrics:
        """Calculate comprehensive data quality metrics"""
        
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        
        # Completeness
        completeness = 1 - (null_cells / total_cells) if total_cells > 0 else 0
        
        # Accuracy (based on business rules)
        accuracy_score = 1.0
        if 'amount' in df.columns:
            invalid_amounts = df[df['amount'] == 0].shape[0]
            accuracy_score -= (invalid_amounts / len(df)) * 0.5
        
        # Consistency
        consistency_score = 1.0
        if 'customer_name' in df.columns:
            # Check for duplicate customers with different names
            customer_variations = df['customer_name'].nunique() / len(df)
            if customer_variations > 0.8:  # Too many unique names
                consistency_score -= 0.2
        
        # Timeliness
        timeliness_score = 1.0
        if 'transaction_date' in df.columns:
            # Check if data is recent
            latest_date = df['transaction_date'].max()
            days_old = (datetime.now() - latest_date).days
            if days_old > 30:
                timeliness_score -= min(days_old / 365, 0.5)
        
        # Validity
        validity_score = 1.0
        if 'amount' in df.columns:
            negative_amounts = df[df['amount'] < 0].shape[0]
            validity_score -= (negative_amounts / len(df)) * 0.3
        
        overall_score = (completeness + accuracy_score + consistency_score + 
                        timeliness_score + validity_score) / 5
        
        return DataQualityMetrics(
            completeness=completeness,
            accuracy=accuracy_score,
            consistency=consistency_score,
            timeliness=timeliness_score,
            validity=validity_score,
            overall_score=overall_score
        )
    
    async def _trigger_ml_pipeline(self, company_id: str):
        """Trigger ML pipeline for updated data"""
        
        # Add to processing queue
        await self.redis.lpush('ml_processing_queue', company_id)
        
        # Update feature store
        await self._update_feature_store(company_id)
        
        self.logger.info(f"ML pipeline triggered for company {company_id}")
```

---

## 📊 DATA LAKE ARCHITECTURE

### S3 Data Lake Structure
```
📁 EZBI Data Lake Structure

s3://ezbi-data-lake/
├── raw_data/                    # Raw ingestion data
│   ├── company_id/
│   │   ├── excel_uploads/
│   │   ├── erp_exports/
│   │   ├── bank_api_data/
│   │   └── external_api_data/
│   └── partitioned_by_date/
│       ├── year=2024/
│       │   ├── month=01/
│       │   │   └── day=01/
│       │   └── month=02/
│       └── year=2025/
│
├── processed_data/              # Cleaned and validated data
│   ├── transactions/
│   │   ├── company_id/
│   │   └── partitioned_by_date/
│   ├── customers/
│   ├── suppliers/
│   └── production_cycles/
│
├── feature_store/               # ML features
│   ├── company_features/
│   ├── time_series_features/
│   └── aggregated_features/
│
├── ml_models/                   # Trained models
│   ├── prophet_models/
│   ├── lstm_models/
│   ├── ensemble_models/
│   └── model_artifacts/
│
├── exports/                     # User exports
│   ├── pdf_reports/
│   ├── excel_exports/
│   └── api_responses/
│
└── backups/                     # System backups
    ├── database_backups/
    ├── model_backups/
    └── configuration_backups/
```

### Data Lifecycle Management
```python
# 📊 Data Lifecycle Management

class DataLifecycleManager:
    """Manage data lifecycle and retention policies"""
    
    def __init__(self, s3_client, db_connection):
        self.s3 = s3_client
        self.db = db_connection
        self.retention_policies = {
            'raw_data': 2555,      # 7 years (legal requirement)
            'processed_data': 1825, # 5 years
            'feature_store': 1095,  # 3 years
            'ml_models': 365,       # 1 year
            'exports': 90,          # 3 months
            'logs': 30             # 1 month
        }
    
    async def apply_retention_policies(self):
        """Apply data retention policies"""
        
        for data_type, retention_days in self.retention_policies.items():
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # S3 cleanup
            await self._cleanup_s3_data(data_type, cutoff_date)
            
            # Database cleanup
            await self._cleanup_database_data(data_type, cutoff_date)
        
        # Update data catalog
        await self._update_data_catalog()
    
    async def _cleanup_s3_data(self, data_type: str, cutoff_date: datetime):
        """Clean up S3 data based on retention policy"""
        
        prefix = f"{data_type}/"
        
        # List objects older than cutoff
        objects_to_delete = []
        paginator = self.s3.get_paginator('list_objects_v2')
        
        for page in paginator.paginate(Bucket='ezbi-data-lake', Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        objects_to_delete.append({'Key': obj['Key']})
        
        # Delete in batches
        if objects_to_delete:
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i+1000]
                await self.s3.delete_objects(
                    Bucket='ezbi-data-lake',
                    Delete={'Objects': batch}
                )
    
    async def optimize_storage(self):
        """Optimize storage costs and performance"""
        
        # Transition to cheaper storage classes
        await self._transition_to_ia()  # Infrequent Access
        await self._transition_to_glacier()  # Glacier
        
        # Compress old data
        await self._compress_old_data()
        
        # Update partitioning
        await self._optimize_partitioning()
    
    async def _transition_to_ia(self):
        """Transition data to Infrequent Access storage"""
        
        # Data older than 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        
        # Lifecycle rule for automatic transition
        lifecycle_config = {
            'Rules': [
                {
                    'ID': 'TransitionToIA',
                    'Status': 'Enabled',
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'STANDARD_IA'
                        },
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER'
                        },
                        {
                            'Days': 365,
                            'StorageClass': 'DEEP_ARCHIVE'
                        }
                    ]
                }
            ]
        }
        
        await self.s3.put_bucket_lifecycle_configuration(
            Bucket='ezbi-data-lake',
            LifecycleConfiguration=lifecycle_config
        )
```

Cette spécification complète de Data Engineering fournit une base solide pour l'ingestion, le traitement, et le stockage des données pour EZBI Analytics, avec un focus sur les PME manufacturières françaises.