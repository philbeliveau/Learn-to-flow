"""
Data ingestion service for real manufacturing and cash flow data.
Handles Kaggle datasets integration and data preprocessing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.models.manufacturing import ManufacturingData, CashFlowData
import pickle
import os

logger = logging.getLogger(__name__)

class DataIngestionService:
    """Service for ingesting and processing real manufacturing data from Kaggle."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.processed_cache = {}
    
    async def ingest_manufacturing_process_data(self) -> List[Dict]:
        """
        Ingest continuous factory process data from Kaggle.
        Returns structured manufacturing data for ML training.
        """
        try:
            logger.info("Starting manufacturing process data ingestion...")
            
            # Load the continuous factory process dataset
            file_path = self.data_dir / "continuous_factory_process.csv"
            if not file_path.exists():
                raise FileNotFoundError(f"Dataset not found: {file_path}")
            
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from manufacturing process dataset")
            
            # Process the data
            processed_data = self._process_manufacturing_data(df)
            
            # Store in database
            await self._store_manufacturing_data(processed_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error ingesting manufacturing data: {str(e)}")
            raise
    
    def _process_manufacturing_data(self, df: pd.DataFrame) -> List[Dict]:
        """Process raw manufacturing data into structured format."""
        processed_records = []
        
        # Convert timestamp to datetime
        df['time_stamp'] = pd.to_datetime(df['time_stamp'])
        
        # Sample every 10th row to reduce data volume (for demo purposes)
        df_sampled = df.iloc[::10].copy()
        
        for _, row in df_sampled.iterrows():
            # Extract key metrics for each machine/stage
            record = {
                'timestamp': row['time_stamp'],
                'machine_1': {
                    'temperature_zone1': row.get('Machine1.Zone1Temperature.C.Actual', 0),
                    'temperature_zone2': row.get('Machine1.Zone2Temperature.C.Actual', 0),
                    'motor_amperage': row.get('Machine1.MotorAmperage.U.Actual', 0),
                    'motor_rpm': row.get('Machine1.MotorRPM.C.Actual', 0),
                    'material_pressure': row.get('Machine1.MaterialPressure.U.Actual', 0),
                    'efficiency': self._calculate_efficiency(row, 'Machine1'),
                },
                'machine_2': {
                    'temperature_zone1': row.get('Machine2.Zone1Temperature.C.Actual', 0),
                    'temperature_zone2': row.get('Machine2.Zone2Temperature.C.Actual', 0),
                    'motor_amperage': row.get('Machine2.MotorAmperage.U.Actual', 0),
                    'motor_rpm': row.get('Machine2.MotorRPM.C.Actual', 0),
                    'material_pressure': row.get('Machine2.MaterialPressure.U.Actual', 0),
                    'efficiency': self._calculate_efficiency(row, 'Machine2'),
                },
                'machine_3': {
                    'temperature_zone1': row.get('Machine3.Zone1Temperature.C.Actual', 0),
                    'temperature_zone2': row.get('Machine3.Zone2Temperature.C.Actual', 0),
                    'motor_amperage': row.get('Machine3.MotorAmperage.U.Actual', 0),
                    'motor_rpm': row.get('Machine3.MotorRPM.C.Actual', 0),
                    'material_pressure': row.get('Machine3.MaterialPressure.U.Actual', 0),
                    'efficiency': self._calculate_efficiency(row, 'Machine3'),
                },
                'ambient_conditions': {
                    'humidity': row.get('AmbientConditions.AmbientHumidity.U.Actual', 0),
                    'temperature': row.get('AmbientConditions.AmbientTemperature.U.Actual', 0),
                },
                'stage1_output': self._extract_stage_outputs(row, 'Stage1'),
                'stage2_output': self._extract_stage_outputs(row, 'Stage2'),
                'quality_score': self._calculate_quality_score(row),
                'production_rate': self._calculate_production_rate(row),
                'energy_consumption': self._calculate_energy_consumption(row),
                'maintenance_indicator': self._calculate_maintenance_indicator(row),
            }
            
            processed_records.append(record)
        
        logger.info(f"Processed {len(processed_records)} manufacturing records")
        return processed_records
    
    def _calculate_efficiency(self, row: pd.Series, machine_prefix: str) -> float:
        """Calculate machine efficiency based on operating parameters."""
        try:
            rpm = row.get(f'{machine_prefix}.MotorRPM.C.Actual', 0)
            amperage = row.get(f'{machine_prefix}.MotorAmperage.U.Actual', 0)
            pressure = row.get(f'{machine_prefix}.MaterialPressure.U.Actual', 0)
            
            # Normalized efficiency calculation (0-100%)
            if rpm > 0 and amperage > 0:
                efficiency = min(100, (rpm * pressure) / (amperage * 100))
                return max(0, efficiency)
            return 0
        except:
            return 0
    
    def _extract_stage_outputs(self, row: pd.Series, stage_prefix: str) -> Dict:
        """Extract stage output measurements."""
        outputs = {}
        for i in range(15):  # 0-14 measurements
            actual_key = f'{stage_prefix}.Output.Measurement{i}.U.Actual'
            setpoint_key = f'{stage_prefix}.Output.Measurement{i}.U.Setpoint'
            outputs[f'measurement_{i}'] = {
                'actual': row.get(actual_key, 0),
                'setpoint': row.get(setpoint_key, 0),
                'deviation': abs(row.get(actual_key, 0) - row.get(setpoint_key, 0))
            }
        return outputs
    
    def _calculate_quality_score(self, row: pd.Series) -> float:
        """Calculate overall quality score based on deviations from setpoints."""
        try:
            deviations = []
            for stage in ['Stage1', 'Stage2']:
                for i in range(15):
                    actual = row.get(f'{stage}.Output.Measurement{i}.U.Actual', 0)
                    setpoint = row.get(f'{stage}.Output.Measurement{i}.U.Setpoint', 0)
                    if setpoint > 0:
                        deviation = abs(actual - setpoint) / setpoint
                        deviations.append(deviation)
            
            if deviations:
                avg_deviation = np.mean(deviations)
                quality_score = max(0, 100 - (avg_deviation * 100))
                return min(100, quality_score)
            return 85  # Default quality score
        except:
            return 85
    
    def _calculate_production_rate(self, row: pd.Series) -> float:
        """Calculate production rate based on machine speeds."""
        try:
            rpms = [
                row.get('Machine1.MotorRPM.C.Actual', 0),
                row.get('Machine2.MotorRPM.C.Actual', 0),
                row.get('Machine3.MotorRPM.C.Actual', 0),
            ]
            avg_rpm = np.mean([rpm for rpm in rpms if rpm > 0])
            # Convert to units per hour (normalized)
            return avg_rpm * 0.1 if avg_rpm > 0 else 0
        except:
            return 0
    
    def _calculate_energy_consumption(self, row: pd.Series) -> float:
        """Calculate total energy consumption."""
        try:
            amperages = [
                row.get('Machine1.MotorAmperage.U.Actual', 0),
                row.get('Machine2.MotorAmperage.U.Actual', 0),
                row.get('Machine3.MotorAmperage.U.Actual', 0),
            ]
            # Approximate energy consumption in kWh
            total_amperage = sum(amperages)
            voltage = 380  # Typical industrial voltage
            energy_kw = (total_amperage * voltage) / 1000
            return energy_kw
        except:
            return 0
    
    def _calculate_maintenance_indicator(self, row: pd.Series) -> float:
        """Calculate maintenance indicator (0-100, higher = more maintenance needed)."""
        try:
            # Based on temperature variations and motor load
            temps = [
                row.get('Machine1.Zone1Temperature.C.Actual', 0),
                row.get('Machine1.Zone2Temperature.C.Actual', 0),
                row.get('Machine2.Zone1Temperature.C.Actual', 0),
                row.get('Machine2.Zone2Temperature.C.Actual', 0),
                row.get('Machine3.Zone1Temperature.C.Actual', 0),
                row.get('Machine3.Zone2Temperature.C.Actual', 0),
            ]
            
            amperages = [
                row.get('Machine1.MotorAmperage.U.Actual', 0),
                row.get('Machine2.MotorAmperage.U.Actual', 0),
                row.get('Machine3.MotorAmperage.U.Actual', 0),
            ]
            
            # High temperature or high current indicates maintenance need
            temp_factor = max(0, (max(temps) - 70) / 30) if temps else 0
            current_factor = max(0, (max(amperages) - 50) / 100) if amperages else 0
            
            maintenance_score = (temp_factor + current_factor) * 50
            return min(100, maintenance_score)
        except:
            return 20
    
    async def ingest_cash_flow_data(self) -> List[Dict]:
        """Ingest cash flow data from Chinese companies dataset."""
        try:
            logger.info("Starting cash flow data ingestion...")
            
            file_path = self.data_dir / "cash_flow.csv"
            if not file_path.exists():
                raise FileNotFoundError(f"Dataset not found: {file_path}")
            
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from cash flow dataset")
            
            # Process the data
            processed_data = self._process_cash_flow_data(df)
            
            # Store in database
            await self._store_cash_flow_data(processed_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error ingesting cash flow data: {str(e)}")
            raise
    
    def _process_cash_flow_data(self, df: pd.DataFrame) -> List[Dict]:
        """Process raw cash flow data into structured format."""
        processed_records = []
        
        # Convert date and clean data
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.dropna(subset=['net cash flow-net cash flow'])
        
        # Sample data for demo (take every 5th row)
        df_sampled = df.iloc[::5].copy()
        
        for _, row in df_sampled.iterrows():
            record = {
                'date': row['Date'],
                'company_ticker': row['ticker'],
                'net_cash_flow': float(row['net cash flow-net cash flow']) if pd.notna(row['net cash flow-net cash flow']) else 0,
                'cash_flow_growth': float(row['net cash flow growth']) if pd.notna(row['net cash flow growth']) else 0,
                'operating_cash_flow': float(row['operating cash flow-net operating cash flow']) if pd.notna(row['operating cash flow-net operating cash flow']) else 0,
                'operating_cash_flow_ratio': float(row['operating cash flow-cash flow ratio']) if pd.notna(row['operating cash flow-cash flow ratio']) else 0,
                'investment_cash_flow': float(row['investment cash flow-net investment cash flow']) if pd.notna(row['investment cash flow-net investment cash flow']) else 0,
                'investment_cash_flow_ratio': float(row['investment cash flow-cash flow ratio']) if pd.notna(row['investment cash flow-cash flow ratio']) else 0,
                'financing_cash_flow': float(row['Cash flow from financing-net cash flow']) if pd.notna(row['Cash flow from financing-net cash flow']) else 0,
                'financing_cash_flow_ratio': float(row['Cash flow from financing-cash flow ratio']) if pd.notna(row['Cash flow from financing-cash flow ratio']) else 0,
            }
            
            processed_records.append(record)
        
        logger.info(f"Processed {len(processed_records)} cash flow records")
        return processed_records
    
    async def ingest_manufacturing_costs(self) -> List[Dict]:
        """Ingest manufacturing cost data."""
        try:
            logger.info("Starting manufacturing cost data ingestion...")
            
            file_path = self.data_dir / "EconomiesOfScale.csv"
            if not file_path.exists():
                raise FileNotFoundError(f"Dataset not found: {file_path}")
            
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from manufacturing cost dataset")
            
            # Process the data
            processed_data = []
            base_date = datetime.now() - timedelta(days=len(df))
            
            for i, (_, row) in enumerate(df.iterrows()):
                record = {
                    'date': base_date + timedelta(days=i),
                    'units_produced': float(row['Number of Units']),
                    'manufacturing_cost': float(row['Manufacturing Cost']),
                    'cost_per_unit': float(row['Manufacturing Cost']) / float(row['Number of Units']) if float(row['Number of Units']) > 0 else 0,
                }
                processed_data.append(record)
            
            logger.info(f"Processed {len(processed_data)} cost records")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error ingesting cost data: {str(e)}")
            raise
    
    async def _store_manufacturing_data(self, data: List[Dict]):
        """Store processed manufacturing data in database."""
        try:
            async with AsyncSessionLocal() as session:
                for record in data:
                    # Create manufacturing data record
                    manufacturing_record = ManufacturingData(
                        timestamp=record['timestamp'],
                        machine_id="multi_stage_line",
                        production_quantity=record['production_rate'],
                        quality_score=record['quality_score'],
                        efficiency=np.mean([
                            record['machine_1']['efficiency'],
                            record['machine_2']['efficiency'],
                            record['machine_3']['efficiency']
                        ]),
                        energy_consumption=record['energy_consumption'],
                        maintenance_indicator=record['maintenance_indicator'],
                        temperature=np.mean([
                            record['machine_1']['temperature_zone1'],
                            record['machine_2']['temperature_zone1'],
                            record['machine_3']['temperature_zone1']
                        ]),
                        pressure=np.mean([
                            record['machine_1']['material_pressure'],
                            record['machine_2']['material_pressure'],
                            record['machine_3']['material_pressure']
                        ]),
                        vibration=0,  # Not available in this dataset
                        raw_data=record
                    )
                    session.add(manufacturing_record)
                
                await session.commit()
                logger.info(f"Stored {len(data)} manufacturing records in database")
        except Exception as e:
            logger.error(f"Error storing manufacturing data: {str(e)}")
            raise
    
    async def _store_cash_flow_data(self, data: List[Dict]):
        """Store processed cash flow data in database."""
        try:
            async with AsyncSessionLocal() as session:
                for record in data:
                    # Create cash flow data record
                    cash_flow_record = CashFlowData(
                        date=record['date'],
                        company_identifier=record['company_ticker'],
                        net_cash_flow=record['net_cash_flow'],
                        operating_cash_flow=record['operating_cash_flow'],
                        investment_cash_flow=record['investment_cash_flow'],
                        financing_cash_flow=record['financing_cash_flow'],
                        cash_flow_growth_rate=record['cash_flow_growth'],
                        operating_ratio=record['operating_cash_flow_ratio'],
                        investment_ratio=record['investment_cash_flow_ratio'],
                        financing_ratio=record['financing_cash_flow_ratio']
                    )
                    session.add(cash_flow_record)
                
                await session.commit()
                logger.info(f"Stored {len(data)} cash flow records in database")
        except Exception as e:
            logger.error(f"Error storing cash flow data: {str(e)}")
            raise
    
    async def ingest_all_datasets(self) -> Dict[str, int]:
        """Ingest all available datasets."""
        results = {}
        
        try:
            # Ingest manufacturing process data
            manufacturing_data = await self.ingest_manufacturing_process_data()
            results['manufacturing_records'] = len(manufacturing_data)
            
            # Ingest cash flow data
            cash_flow_data = await self.ingest_cash_flow_data()
            results['cash_flow_records'] = len(cash_flow_data)
            
            # Ingest cost data
            cost_data = await self.ingest_manufacturing_costs()
            results['cost_records'] = len(cost_data)
            
            logger.info(f"Successfully ingested all datasets: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error during complete data ingestion: {str(e)}")
            raise

# Create singleton instance
data_ingestion_service = DataIngestionService()