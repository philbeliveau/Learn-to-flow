"""
API endpoints for data management and uploads.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import logging
import pandas as pd
import io
import json
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.manufacturing import DataUpload, ManufacturingData
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter()

class DataValidationResult(BaseModel):
    """Result of data validation."""
    is_valid: bool
    total_rows: int
    valid_rows: int
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    column_mapping: Dict[str, str]

class DataUploadResponse(BaseModel):
    """Response for data upload."""
    upload_id: str
    filename: str
    status: str
    validation_result: Optional[DataValidationResult]
    message: str

@router.post("/upload", response_model=DataUploadResponse)
async def upload_data_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and validate manufacturing or financial data files.
    
    Supports CSV and Excel files with automatic column detection and validation.
    The data is processed asynchronously after upload.
    """
    try:
        # Validate file type
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = '.' + file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size (max 50MB)
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size: 50MB")
        
        # Parse file content
        try:
            if file_extension == '.csv':
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            else:
                df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
        
        # Validate data structure
        validation_result = validate_manufacturing_data(df)
        
        # Create upload record
        upload_record = DataUpload(
            filename=file.filename,
            file_size=len(content),
            file_type=file_extension[1:],  # Remove the dot
            upload_status="processing" if validation_result.is_valid else "failed",
            records_count=validation_result.total_rows,
            errors_count=len(validation_result.errors),
            validation_results=validation_result.dict(),
            user_id=current_user.id
        )
        
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)
        
        # Process data in background if valid
        if validation_result.is_valid and background_tasks:
            background_tasks.add_task(
                process_uploaded_data,
                upload_record.id,
                df,
                validation_result.column_mapping,
                current_user.id
            )
        
        return DataUploadResponse(
            upload_id=upload_record.id,
            filename=file.filename,
            status=upload_record.upload_status,
            validation_result=validation_result,
            message="File uploaded successfully" if validation_result.is_valid else "File uploaded but validation failed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@router.get("/uploads")
async def list_uploads(
    limit: int = Query(50, ge=1, le=200, description="Number of uploads to return"),
    status: Optional[str] = Query(None, description="Filter by upload status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List data uploads for the current user.
    """
    try:
        query = db.query(DataUpload).filter(DataUpload.user_id == current_user.id)
        
        if status:
            query = query.filter(DataUpload.upload_status == status)
        
        uploads = query.order_by(DataUpload.uploaded_at.desc()).limit(limit).all()
        
        return {
            "uploads": [
                {
                    "id": upload.id,
                    "filename": upload.filename,
                    "file_size": upload.file_size,
                    "file_type": upload.file_type,
                    "upload_status": upload.upload_status,
                    "records_count": upload.records_count,
                    "errors_count": upload.errors_count,
                    "uploaded_at": upload.uploaded_at.isoformat(),
                    "processed_at": upload.processed_at.isoformat() if upload.processed_at else None
                }
                for upload in uploads
            ],
            "total": len(uploads)
        }
        
    except Exception as e:
        logger.error(f"Error listing uploads: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list uploads: {str(e)}")

@router.get("/uploads/{upload_id}")
async def get_upload_details(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific upload.
    """
    try:
        upload = db.query(DataUpload).filter(
            DataUpload.id == upload_id,
            DataUpload.user_id == current_user.id
        ).first()
        
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        return {
            "id": upload.id,
            "filename": upload.filename,
            "file_size": upload.file_size,
            "file_type": upload.file_type,
            "upload_status": upload.upload_status,
            "records_count": upload.records_count,
            "errors_count": upload.errors_count,
            "validation_results": upload.validation_results,
            "processing_log": upload.processing_log,
            "uploaded_at": upload.uploaded_at.isoformat(),
            "processed_at": upload.processed_at.isoformat() if upload.processed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting upload details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get upload details: {str(e)}")

@router.get("/manufacturing")
async def get_manufacturing_data(
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get manufacturing data with optional filtering.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            query = """
            SELECT timestamp, machine_id, production_quantity, quality_score,
                   efficiency, energy_consumption, maintenance_indicator,
                   temperature, pressure, vibration
            FROM manufacturing_data
            WHERE 1=1
            """
            params = {}
            
            if machine_id:
                query += " AND machine_id = :machine_id"
                params["machine_id"] = machine_id
            
            if start_date:
                query += " AND timestamp >= :start_date"
                params["start_date"] = start_date
            
            if end_date:
                query += " AND timestamp <= :end_date"
                params["end_date"] = end_date
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit
            
            result = await session.execute(text(query), params)
            records = [dict(row._mapping) for row in result.fetchall()]
            
            return {
                "data": records,
                "total": len(records)
            }
        
    except Exception as e:
        logger.error(f"Error getting manufacturing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get manufacturing data: {str(e)}")

@router.get("/kpis")
async def get_manufacturing_kpis(
    period: str = Query("24h", description="Time period: 1h, 24h, 7d, 30d"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get calculated manufacturing KPIs for the specified period.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        # Define time interval
        interval_map = {
            "1h": "1 HOUR",
            "24h": "1 DAY", 
            "7d": "7 DAY",
            "30d": "30 DAY"
        }
        
        interval = interval_map.get(period, "1 DAY")
        
        async with AsyncSessionLocal() as session:
            # Calculate KPIs from manufacturing data
            kpi_query = f"""
            SELECT 
                AVG(efficiency) as avg_efficiency,
                AVG(quality_score) as avg_quality,
                SUM(production_quantity) as total_production,
                SUM(energy_consumption) as total_energy,
                AVG(maintenance_indicator) as avg_maintenance_indicator,
                COUNT(*) as total_records
            FROM manufacturing_data
            WHERE timestamp >= NOW() - INTERVAL '{interval}'
            """
            
            result = await session.execute(text(kpi_query))
            kpi_data = result.fetchone()
            
            if kpi_data:
                kpis = dict(kpi_data._mapping)
                
                # Calculate derived KPIs
                energy_efficiency = (kpis['total_production'] / kpis['total_energy']) if kpis['total_energy'] > 0 else 0
                
                return {
                    "period": period,
                    "kpis": {
                        "efficiency": {
                            "value": round(kpis['avg_efficiency'] or 0, 2),
                            "unit": "%",
                            "trend": "stable"  # TODO: Calculate actual trend
                        },
                        "quality": {
                            "value": round(kpis['avg_quality'] or 0, 2),
                            "unit": "%",
                            "trend": "stable"
                        },
                        "production": {
                            "value": round(kpis['total_production'] or 0, 2),
                            "unit": "units",
                            "trend": "up"
                        },
                        "energy_efficiency": {
                            "value": round(energy_efficiency, 4),
                            "unit": "units/kWh",
                            "trend": "stable"
                        },
                        "maintenance_risk": {
                            "value": round(kpis['avg_maintenance_indicator'] or 0, 2),
                            "unit": "%",
                            "trend": "down"
                        }
                    },
                    "data_points": kpis['total_records'] or 0
                }
            else:
                return {
                    "period": period,
                    "kpis": {},
                    "data_points": 0,
                    "message": "No data available for the specified period"
                }
        
    except Exception as e:
        logger.error(f"Error calculating KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPIs: {str(e)}")

# Helper functions

def validate_manufacturing_data(df: pd.DataFrame) -> DataValidationResult:
    """Validate uploaded manufacturing data."""
    errors = []
    warnings = []
    
    # Required columns (flexible mapping)
    required_columns = {
        'timestamp': ['timestamp', 'date', 'datetime', 'time'],
        'machine_id': ['machine_id', 'machine', 'equipment_id', 'line'],
        'production': ['production', 'quantity', 'output', 'units'],
        'quality': ['quality', 'quality_score', 'defect_rate'],
        'efficiency': ['efficiency', 'oee', 'performance']
    }
    
    # Map columns
    column_mapping = {}
    for required, variants in required_columns.items():
        found = False
        for variant in variants:
            matching_cols = [col for col in df.columns if variant.lower() in col.lower()]
            if matching_cols:
                column_mapping[required] = matching_cols[0]
                found = True
                break
        
        if not found:
            errors.append({
                "type": "missing_column",
                "message": f"Required column '{required}' not found. Expected one of: {variants}",
                "severity": "error"
            })
    
    # Validate data types and ranges
    if 'timestamp' in column_mapping:
        try:
            pd.to_datetime(df[column_mapping['timestamp']])
        except:
            errors.append({
                "type": "invalid_timestamp",
                "message": f"Column '{column_mapping['timestamp']}' contains invalid timestamp values",
                "severity": "error"
            })
    
    # Check for numeric columns
    numeric_columns = ['production', 'quality', 'efficiency']
    for col in numeric_columns:
        if col in column_mapping:
            if not pd.api.types.is_numeric_dtype(df[column_mapping[col]]):
                warnings.append({
                    "type": "non_numeric",
                    "message": f"Column '{column_mapping[col]}' should be numeric",
                    "severity": "warning"
                })
    
    # Check data quality
    total_rows = len(df)
    empty_rows = df.isnull().all(axis=1).sum()
    
    if empty_rows > 0:
        warnings.append({
            "type": "empty_rows",
            "message": f"Found {empty_rows} empty rows out of {total_rows}",
            "severity": "warning"
        })
    
    # Check for duplicates
    if 'timestamp' in column_mapping and 'machine_id' in column_mapping:
        duplicates = df.duplicated(subset=[column_mapping['timestamp'], column_mapping['machine_id']]).sum()
        if duplicates > 0:
            warnings.append({
                "type": "duplicates",
                "message": f"Found {duplicates} duplicate records",
                "severity": "warning"
            })
    
    valid_rows = total_rows - empty_rows
    is_valid = len(errors) == 0 and valid_rows > 0
    
    return DataValidationResult(
        is_valid=is_valid,
        total_rows=total_rows,
        valid_rows=valid_rows,
        errors=errors,
        warnings=warnings,
        column_mapping=column_mapping
    )

async def process_uploaded_data(upload_id: str, df: pd.DataFrame, 
                              column_mapping: Dict[str, str], user_id: str):
    """Background task to process uploaded data."""
    try:
        from app.core.database import AsyncSessionLocal
        
        logger.info(f"Processing uploaded data for upload {upload_id}")
        
        processed_count = 0
        error_count = 0
        
        async with AsyncSessionLocal() as session:
            for _, row in df.iterrows():
                try:
                    # Create manufacturing data record
                    manufacturing_data = ManufacturingData(
                        timestamp=pd.to_datetime(row[column_mapping.get('timestamp', df.columns[0])]),
                        machine_id=str(row[column_mapping.get('machine_id', 'unknown')]),
                        production_quantity=float(row[column_mapping.get('production', 0)]) if column_mapping.get('production') else 0,
                        quality_score=float(row[column_mapping.get('quality', 85)]) if column_mapping.get('quality') else 85,
                        efficiency=float(row[column_mapping.get('efficiency', 80)]) if column_mapping.get('efficiency') else 80,
                        energy_consumption=float(row.get('energy', 0)) if 'energy' in row else 0,
                        maintenance_indicator=float(row.get('maintenance', 20)) if 'maintenance' in row else 20,
                        temperature=float(row.get('temperature', 25)) if 'temperature' in row else 25,
                        pressure=float(row.get('pressure', 1)) if 'pressure' in row else 1,
                        vibration=float(row.get('vibration', 0)) if 'vibration' in row else 0,
                        raw_data=row.to_dict()
                    )
                    
                    session.add(manufacturing_data)
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing row: {str(e)}")
                    error_count += 1
            
            # Update upload record
            from sqlalchemy import text
            update_query = text("""
                UPDATE data_uploads 
                SET upload_status = :status, processed_at = NOW(), 
                    records_count = :processed_count, errors_count = :error_count,
                    processing_log = :log
                WHERE id = :upload_id
            """)
            
            await session.execute(update_query, {
                "status": "completed" if error_count == 0 else "completed_with_errors",
                "processed_count": processed_count,
                "error_count": error_count,
                "log": f"Processed {processed_count} records, {error_count} errors",
                "upload_id": upload_id
            })
            
            await session.commit()
            
        logger.info(f"Data processing completed for upload {upload_id}: {processed_count} processed, {error_count} errors")
        
    except Exception as e:
        logger.error(f"Error processing uploaded data: {str(e)}")
        # Update upload status to failed
        try:
            async with AsyncSessionLocal() as session:
                update_query = text("""
                    UPDATE data_uploads 
                    SET upload_status = 'failed', processed_at = NOW(),
                        processing_log = :error_log
                    WHERE id = :upload_id
                """)
                
                await session.execute(update_query, {
                    "error_log": f"Processing failed: {str(e)}",
                    "upload_id": upload_id
                })
                
                await session.commit()
        except Exception as update_error:
            logger.error(f"Failed to update upload status: {str(update_error)}")