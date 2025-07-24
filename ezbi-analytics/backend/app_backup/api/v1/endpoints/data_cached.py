"""
Cached Data API Endpoints for EZBI Analytics
High-performance manufacturing data endpoints with Redis caching
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import structlog
import pandas as pd
import hashlib
import asyncio
from datetime import datetime, timedelta, date
from sqlalchemy import text, and_, or_

from app.core.database import get_db, get_async_session, AsyncSessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.models.manufacturing import DataUpload, ManufacturingData
from app.services.redis_service import (
    manufacturing_cache, 
    redis_service,
    cache_result,
    cache_invalidate
)
from pydantic import BaseModel, Field

logger = structlog.get_logger()
security = HTTPBearer()

router = APIRouter()

class CachedDataResponse(BaseModel):
    """Response model for cached data endpoints."""
    data: Any
    total: int
    cached: bool = False
    cache_ttl: Optional[int] = None
    processing_time: Optional[float] = None
    from_cache: bool = False

class ManufacturingDataParams(BaseModel):
    """Parameters for manufacturing data queries."""
    machine_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

class KPIParams(BaseModel):
    """Parameters for KPI queries."""
    period: str = Field(default="24h", regex=r"^(1h|24h|7d|30d)$")
    machine_id: Optional[str] = None
    include_trends: bool = True

@router.get("/manufacturing/cached", response_model=CachedDataResponse)
async def get_cached_manufacturing_data(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
):
    """
    Get manufacturing data with intelligent caching.
    
    Features:
    - Automatic query result caching (30 min TTL)
    - Pagination support
    - Machine-specific and date-range filtering
    - Cache statistics in response
    """
    try:
        start_time = datetime.now()
        
        # Generate cache key
        cache_key_parts = [
            f"machine_id:{machine_id or 'all'}",
            f"start_date:{start_date or 'none'}",
            f"end_date:{end_date or 'none'}",
            f"limit:{limit}",
            f"offset:{offset}"
        ]
        cache_key = hashlib.md5(":".join(cache_key_parts).encode()).hexdigest()
        
        # Try to get from cache first
        cached_data = await manufacturing_cache.get_manufacturing_data(
            machine_id or 'all',
            start_date or 'none',
            end_date or 'none',
            limit
        )
        
        if cached_data:
            processing_time = (datetime.now() - start_time).total_seconds()
            return CachedDataResponse(
                data=cached_data,
                total=len(cached_data),
                cached=True,
                cache_ttl=await manufacturing_cache.get_ttl(cache_key, 'manufacturing_data'),
                processing_time=processing_time,
                from_cache=True
            )
        
        # Query database
        async with AsyncSessionLocal() as session:
            # Build dynamic query
            query = """
            SELECT 
                timestamp,
                machine_id,
                production_quantity,
                quality_score,
                efficiency,
                energy_consumption,
                maintenance_indicator,
                temperature,
                pressure,
                vibration,
                raw_data
            FROM manufacturing_data
            WHERE 1=1
            """
            
            params = {}
            
            # Add filters
            if machine_id:
                query += " AND machine_id = :machine_id"
                params["machine_id"] = machine_id
            
            if start_date:
                query += " AND timestamp >= :start_date"
                params["start_date"] = start_date
            
            if end_date:
                query += " AND timestamp <= :end_date"
                params["end_date"] = end_date
            
            # Add ordering and pagination
            query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            # Execute query
            result = await session.execute(text(query), params)
            records = []
            
            for row in result.fetchall():
                record = dict(row._mapping)
                # Convert timestamp to ISO format
                if record.get('timestamp'):
                    record['timestamp'] = record['timestamp'].isoformat()
                records.append(record)
            
            # Get total count for pagination
            count_query = """
            SELECT COUNT(*) as total
            FROM manufacturing_data
            WHERE 1=1
            """
            
            count_params = {}
            if machine_id:
                count_query += " AND machine_id = :machine_id"
                count_params["machine_id"] = machine_id
            
            if start_date:
                count_query += " AND timestamp >= :start_date"
                count_params["start_date"] = start_date
            
            if end_date:
                count_query += " AND timestamp <= :end_date"
                count_params["end_date"] = end_date
            
            total_result = await session.execute(text(count_query), count_params)
            total_count = total_result.scalar()
            
            # Cache the results
            await manufacturing_cache.cache_manufacturing_data(
                machine_id or 'all',
                start_date or 'none',
                end_date or 'none',
                records,
                limit
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return CachedDataResponse(
                data=records,
                total=total_count,
                cached=True,
                cache_ttl=manufacturing_cache.query_cache_ttl,
                processing_time=processing_time,
                from_cache=False
            )
        
    except Exception as e:
        logger.error("Error getting cached manufacturing data", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get manufacturing data: {str(e)}")

@router.get("/kpis/cached", response_model=CachedDataResponse)
async def get_cached_kpis(
    period: str = Query("24h", regex=r"^(1h|24h|7d|30d)$", description="Time period"),
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    include_trends: bool = Query(True, description="Include trend calculations"),
    current_user: User = Depends(get_current_user),
):
    """
    Get manufacturing KPIs with intelligent caching and trend analysis.
    
    Features:
    - Automatic KPI calculation caching (15 min TTL)
    - Trend analysis (optional)
    - Machine-specific filtering
    - Performance optimizations
    """
    try:
        start_time = datetime.now()
        
        # Try to get from cache first
        cache_key = f"{period}:{machine_id or 'all'}:{include_trends}"
        cached_kpis = await manufacturing_cache.get_kpis(cache_key)
        
        if cached_kpis:
            processing_time = (datetime.now() - start_time).total_seconds()
            return CachedDataResponse(
                data=cached_kpis,
                total=1,
                cached=True,
                cache_ttl=await manufacturing_cache.get_ttl(cache_key, 'kpis'),
                processing_time=processing_time,
                from_cache=True
            )
        
        # Calculate KPIs from database
        async with AsyncSessionLocal() as session:
            # Define time interval
            interval_map = {
                "1h": "1 HOUR",
                "24h": "1 DAY",
                "7d": "7 DAY",
                "30d": "30 DAY"
            }
            
            interval = interval_map.get(period, "1 DAY")
            
            # Build KPI query
            kpi_query = f"""
            SELECT 
                AVG(efficiency) as avg_efficiency,
                AVG(quality_score) as avg_quality,
                SUM(production_quantity) as total_production,
                SUM(energy_consumption) as total_energy,
                AVG(maintenance_indicator) as avg_maintenance_indicator,
                AVG(temperature) as avg_temperature,
                AVG(pressure) as avg_pressure,
                AVG(vibration) as avg_vibration,
                COUNT(*) as total_records,
                MIN(timestamp) as period_start,
                MAX(timestamp) as period_end
            FROM manufacturing_data
            WHERE timestamp >= NOW() - INTERVAL '{interval}'
            """
            
            params = {}
            if machine_id:
                kpi_query += " AND machine_id = :machine_id"
                params["machine_id"] = machine_id
            
            result = await session.execute(text(kpi_query), params)
            kpi_data = result.fetchone()
            
            if kpi_data:
                kpis = dict(kpi_data._mapping)
                
                # Calculate derived KPIs
                energy_efficiency = (kpis['total_production'] / kpis['total_energy']) if kpis['total_energy'] and kpis['total_energy'] > 0 else 0
                
                # Calculate quality efficiency
                quality_efficiency = (kpis['avg_quality'] * kpis['avg_efficiency']) / 100 if kpis['avg_quality'] and kpis['avg_efficiency'] else 0
                
                # Format response
                kpi_response = {
                    "period": period,
                    "machine_id": machine_id,
                    "kpis": {
                        "efficiency": {
                            "value": round(kpis['avg_efficiency'] or 0, 2),
                            "unit": "%",
                            "trend": "stable"
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
                        "quality_efficiency": {
                            "value": round(quality_efficiency, 2),
                            "unit": "%",
                            "trend": "stable"
                        },
                        "maintenance_risk": {
                            "value": round(kpis['avg_maintenance_indicator'] or 0, 2),
                            "unit": "%",
                            "trend": "down"
                        },
                        "temperature": {
                            "value": round(kpis['avg_temperature'] or 0, 2),
                            "unit": "°C",
                            "trend": "stable"
                        },
                        "pressure": {
                            "value": round(kpis['avg_pressure'] or 0, 2),
                            "unit": "bar",
                            "trend": "stable"
                        },
                        "vibration": {
                            "value": round(kpis['avg_vibration'] or 0, 2),
                            "unit": "mm/s",
                            "trend": "stable"
                        }
                    },
                    "data_points": kpis['total_records'] or 0,
                    "period_start": kpis['period_start'].isoformat() if kpis['period_start'] else None,
                    "period_end": kpis['period_end'].isoformat() if kpis['period_end'] else None
                }
                
                # Add trend analysis if requested
                if include_trends:
                    kpi_response["trends"] = await _calculate_kpi_trends(session, period, machine_id)
                
                # Cache the results
                await manufacturing_cache.cache_kpis(cache_key, kpi_response)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return CachedDataResponse(
                    data=kpi_response,
                    total=1,
                    cached=True,
                    cache_ttl=manufacturing_cache.kpi_cache_ttl,
                    processing_time=processing_time,
                    from_cache=False
                )
            
            else:
                # No data available
                empty_response = {
                    "period": period,
                    "machine_id": machine_id,
                    "kpis": {},
                    "data_points": 0,
                    "message": "No data available for the specified period"
                }
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return CachedDataResponse(
                    data=empty_response,
                    total=0,
                    cached=False,
                    processing_time=processing_time,
                    from_cache=False
                )
        
    except Exception as e:
        logger.error("Error calculating cached KPIs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPIs: {str(e)}")

@router.get("/aggregations/cached")
async def get_cached_aggregations(
    aggregation_type: str = Query(..., description="Type of aggregation (hourly, daily, weekly)"),
    metric: str = Query(..., description="Metric to aggregate (efficiency, quality, production)"),
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregated manufacturing data with caching.
    
    Features:
    - Flexible aggregation periods (hourly, daily, weekly)
    - Multiple metrics support
    - Optimized for dashboard visualizations
    - Smart caching based on aggregation type
    """
    try:
        start_time = datetime.now()
        
        # Generate cache key
        cache_key = f"{aggregation_type}:{metric}:{machine_id or 'all'}:{days}"
        query_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Try to get from cache
        cached_result = await manufacturing_cache.get_aggregation(query_hash)
        
        if cached_result:
            processing_time = (datetime.now() - start_time).total_seconds()
            return CachedDataResponse(
                data=cached_result,
                total=len(cached_result.get('data', [])),
                cached=True,
                cache_ttl=await manufacturing_cache.get_ttl(query_hash, 'aggregation'),
                processing_time=processing_time,
                from_cache=True
            )
        
        # Calculate aggregations from database
        async with AsyncSessionLocal() as session:
            # Determine aggregation SQL
            aggregation_sql = {
                'hourly': "DATE_TRUNC('hour', timestamp)",
                'daily': "DATE_TRUNC('day', timestamp)",
                'weekly': "DATE_TRUNC('week', timestamp)"
            }
            
            time_group = aggregation_sql.get(aggregation_type, "DATE_TRUNC('day', timestamp)")
            
            # Build aggregation query
            agg_query = f"""
            SELECT 
                {time_group} as period,
                AVG({metric}) as avg_value,
                MIN({metric}) as min_value,
                MAX({metric}) as max_value,
                COUNT(*) as data_points
            FROM manufacturing_data
            WHERE timestamp >= NOW() - INTERVAL '{days} days'
            """
            
            params = {}
            if machine_id:
                agg_query += " AND machine_id = :machine_id"
                params["machine_id"] = machine_id
            
            agg_query += f" GROUP BY {time_group} ORDER BY period"
            
            result = await session.execute(text(agg_query), params)
            aggregations = []
            
            for row in result.fetchall():
                agg_data = dict(row._mapping)
                agg_data['period'] = agg_data['period'].isoformat()
                aggregations.append(agg_data)
            
            # Format response
            response_data = {
                "aggregation_type": aggregation_type,
                "metric": metric,
                "machine_id": machine_id,
                "days": days,
                "data": aggregations,
                "summary": {
                    "total_periods": len(aggregations),
                    "avg_value": sum(a['avg_value'] for a in aggregations if a['avg_value']) / len(aggregations) if aggregations else 0,
                    "min_value": min(a['min_value'] for a in aggregations if a['min_value']) if aggregations else 0,
                    "max_value": max(a['max_value'] for a in aggregations if a['max_value']) if aggregations else 0,
                    "total_data_points": sum(a['data_points'] for a in aggregations)
                }
            }
            
            # Cache the results
            await manufacturing_cache.cache_aggregation(query_hash, response_data)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return CachedDataResponse(
                data=response_data,
                total=len(aggregations),
                cached=True,
                cache_ttl=manufacturing_cache.query_cache_ttl,
                processing_time=processing_time,
                from_cache=False
            )
        
    except Exception as e:
        logger.error("Error getting cached aggregations", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get aggregations: {str(e)}")

@router.get("/uploads/cached")
async def get_cached_uploads(
    limit: int = Query(50, ge=1, le=200, description="Number of uploads to return"),
    status: Optional[str] = Query(None, description="Filter by upload status"),
    current_user: User = Depends(get_current_user),
):
    """
    Get cached upload status information.
    
    Features:
    - Upload status caching (5 min TTL)
    - Status filtering
    - User-specific results
    """
    try:
        start_time = datetime.now()
        
        # Generate cache key
        cache_key = f"uploads:{current_user.id}:{status or 'all'}:{limit}"
        query_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Try to get from cache
        cached_uploads = await manufacturing_cache.get_upload_status(query_hash)
        
        if cached_uploads:
            processing_time = (datetime.now() - start_time).total_seconds()
            return CachedDataResponse(
                data=cached_uploads,
                total=len(cached_uploads.get('uploads', [])),
                cached=True,
                cache_ttl=await manufacturing_cache.get_ttl(query_hash, 'upload_status'),
                processing_time=processing_time,
                from_cache=True
            )
        
        # Query database
        async with AsyncSessionLocal() as session:
            query = """
            SELECT 
                id,
                filename,
                file_size,
                file_type,
                upload_status,
                records_count,
                errors_count,
                uploaded_at,
                processed_at
            FROM data_uploads
            WHERE user_id = :user_id
            """
            
            params = {"user_id": current_user.id}
            
            if status:
                query += " AND upload_status = :status"
                params["status"] = status
            
            query += " ORDER BY uploaded_at DESC LIMIT :limit"
            params["limit"] = limit
            
            result = await session.execute(text(query), params)
            uploads = []
            
            for row in result.fetchall():
                upload = dict(row._mapping)
                upload['uploaded_at'] = upload['uploaded_at'].isoformat()
                if upload['processed_at']:
                    upload['processed_at'] = upload['processed_at'].isoformat()
                uploads.append(upload)
            
            upload_response = {
                "uploads": uploads,
                "total": len(uploads),
                "user_id": current_user.id
            }
            
            # Cache the results
            await manufacturing_cache.cache_upload_status(query_hash, upload_response)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return CachedDataResponse(
                data=upload_response,
                total=len(uploads),
                cached=True,
                cache_ttl=300,  # 5 minutes
                processing_time=processing_time,
                from_cache=False
            )
        
    except Exception as e:
        logger.error("Error getting cached uploads", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get uploads: {str(e)}")

@router.delete("/cache/invalidate")
async def invalidate_cache(
    cache_type: str = Query(..., description="Cache type to invalidate (manufacturing_data, kpis, all)"),
    machine_id: Optional[str] = Query(None, description="Specific machine ID to invalidate"),
    current_user: User = Depends(get_current_user),
):
    """
    Invalidate specific cache entries.
    
    Features:
    - Selective cache invalidation
    - Machine-specific invalidation
    - Admin-only access
    """
    try:
        # Check if user has admin privileges (implement proper authorization)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        invalidated_count = 0
        
        if cache_type == "all":
            # Invalidate all caches
            for prefix in ["manufacturing_data", "kpis", "aggregation", "upload_status"]:
                count = await manufacturing_cache.flush_prefix(prefix)
                invalidated_count += count
        
        elif cache_type == "manufacturing_data":
            invalidated_count = await manufacturing_cache.invalidate_manufacturing_cache(machine_id)
        
        elif cache_type == "kpis":
            invalidated_count = await manufacturing_cache.invalidate_kpi_cache()
        
        else:
            raise HTTPException(status_code=400, detail="Invalid cache type")
        
        return {
            "message": f"Cache invalidated successfully",
            "cache_type": cache_type,
            "machine_id": machine_id,
            "invalidated_keys": invalidated_count
        }
        
    except Exception as e:
        logger.error("Error invalidating cache", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")

@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
):
    """
    Get cache performance statistics.
    
    Features:
    - Cache hit/miss ratios
    - Memory usage statistics
    - Cache size by prefix
    """
    try:
        cache_stats = await manufacturing_cache.get_cache_stats()
        
        return {
            "cache_stats": cache_stats,
            "cache_prefixes": manufacturing_cache.prefixes,
            "cache_ttls": {
                "default": manufacturing_cache.default_ttl,
                "session": manufacturing_cache.session_ttl,
                "query_cache": manufacturing_cache.query_cache_ttl,
                "kpi_cache": manufacturing_cache.kpi_cache_ttl
            }
        }
        
    except Exception as e:
        logger.error("Error getting cache stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

# Helper functions

async def _calculate_kpi_trends(session, period: str, machine_id: Optional[str] = None) -> Dict[str, str]:
    """Calculate KPI trends by comparing current period with previous period."""
    try:
        # Define comparison periods
        interval_map = {
            "1h": ("1 HOUR", "2 HOUR"),
            "24h": ("1 DAY", "2 DAY"),
            "7d": ("7 DAY", "14 DAY"),
            "30d": ("30 DAY", "60 DAY")
        }
        
        current_interval, comparison_interval = interval_map.get(period, ("1 DAY", "2 DAY"))
        
        # Query for current period
        current_query = f"""
        SELECT 
            AVG(efficiency) as avg_efficiency,
            AVG(quality_score) as avg_quality,
            SUM(production_quantity) as total_production
        FROM manufacturing_data
        WHERE timestamp >= NOW() - INTERVAL '{current_interval}'
        """
        
        # Query for comparison period
        comparison_query = f"""
        SELECT 
            AVG(efficiency) as avg_efficiency,
            AVG(quality_score) as avg_quality,
            SUM(production_quantity) as total_production
        FROM manufacturing_data
        WHERE timestamp >= NOW() - INTERVAL '{comparison_interval}'
        AND timestamp < NOW() - INTERVAL '{current_interval}'
        """
        
        params = {}
        if machine_id:
            current_query += " AND machine_id = :machine_id"
            comparison_query += " AND machine_id = :machine_id"
            params["machine_id"] = machine_id
        
        # Execute queries
        current_result = await session.execute(text(current_query), params)
        comparison_result = await session.execute(text(comparison_query), params)
        
        current_data = current_result.fetchone()
        comparison_data = comparison_result.fetchone()
        
        trends = {}
        
        if current_data and comparison_data:
            # Calculate trends
            for metric in ['avg_efficiency', 'avg_quality', 'total_production']:
                current_value = getattr(current_data, metric) or 0
                comparison_value = getattr(comparison_data, metric) or 0
                
                if comparison_value > 0:
                    change = ((current_value - comparison_value) / comparison_value) * 100
                    if change > 2:
                        trends[metric] = "up"
                    elif change < -2:
                        trends[metric] = "down"
                    else:
                        trends[metric] = "stable"
                else:
                    trends[metric] = "stable"
        
        return trends
        
    except Exception as e:
        logger.error("Error calculating KPI trends", error=str(e))
        return {"avg_efficiency": "stable", "avg_quality": "stable", "total_production": "stable"}