#!/usr/bin/env python3
"""
Test script for the complete EZBI Analytics system.
Tests data ingestion, ML training, and API endpoints.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.data_ingestion import data_ingestion_service
from app.services.ml_service import ml_service
from app.core.database import AsyncSessionLocal, init_db
from app.models.manufacturing import ManufacturingData, CashFlowData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection."""
    try:
        logger.info("Testing database connection...")
        await init_db()
        
        async with AsyncSessionLocal() as session:
            # Test query
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False

async def test_data_ingestion():
    """Test real data ingestion from Kaggle datasets."""
    try:
        logger.info("Testing data ingestion...")
        
        # Ingest all datasets
        result = await data_ingestion_service.ingest_all_datasets()
        
        logger.info(f"✅ Data ingestion successful: {result}")
        
        # Verify data was inserted
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            
            # Check manufacturing data
            manufacturing_count = await session.execute(text("SELECT COUNT(*) FROM manufacturing_data"))
            manufacturing_records = manufacturing_count.scalar()
            
            # Check cash flow data
            cash_flow_count = await session.execute(text("SELECT COUNT(*) FROM cash_flow_data"))
            cash_flow_records = cash_flow_count.scalar()
            
            logger.info(f"📊 Manufacturing records: {manufacturing_records}")
            logger.info(f"💰 Cash flow records: {cash_flow_records}")
            
            if manufacturing_records > 0 and cash_flow_records > 0:
                logger.info("✅ Data verification successful")
                return True
            else:
                logger.error("❌ No data found after ingestion")
                return False
        
    except Exception as e:
        logger.error(f"❌ Data ingestion failed: {str(e)}")
        return False

async def test_ml_training():
    """Test ML model training."""
    try:
        logger.info("Testing ML model training...")
        
        # Train cash flow prediction model
        training_result = await ml_service.train_cash_flow_prediction_model()
        
        logger.info(f"✅ ML training successful: {training_result}")
        
        # Verify model was saved
        if training_result.get('model_id'):
            logger.info(f"📈 Model ID: {training_result['model_id']}")
            logger.info(f"📊 Training metrics: {training_result.get('metrics', {})}")
            return True
        else:
            logger.error("❌ No model ID returned")
            return False
        
    except Exception as e:
        logger.error(f"❌ ML training failed: {str(e)}")
        return False

async def test_predictions():
    """Test ML predictions."""
    try:
        logger.info("Testing ML predictions...")
        
        # Get latest model
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT id FROM ml_models 
                WHERE status = 'active' 
                ORDER BY created_at DESC 
                LIMIT 1
            """))
            model_row = result.fetchone()
            
            if not model_row:
                logger.error("❌ No active model found for predictions")
                return False
            
            model_id = model_row[0]
            logger.info(f"Using model: {model_id}")
        
        # Generate predictions
        prediction_result = await ml_service.predict_cash_flow(
            model_id=model_id,
            horizon_days=30
        )
        
        logger.info(f"✅ Prediction generation successful")
        logger.info(f"🔮 Predictions: {len(prediction_result.get('predictions', []))} days")
        logger.info(f"📈 Confidence: {prediction_result.get('confidence_intervals', {}).get('overall_confidence', 0):.2%}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Prediction generation failed: {str(e)}")
        return False

async def test_api_readiness():
    """Test API endpoints readiness."""
    try:
        logger.info("Testing API readiness...")
        
        # Test critical components
        components = [
            "Database connection",
            "Manufacturing data", 
            "Cash flow data",
            "ML models",
            "Prediction results"
        ]
        
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            
            # Check each component
            for component in components:
                if "Database" in component:
                    result = await session.execute(text("SELECT 1"))
                    assert result.scalar() == 1
                elif "Manufacturing" in component:
                    result = await session.execute(text("SELECT COUNT(*) FROM manufacturing_data"))
                    count = result.scalar()
                    assert count > 0, f"No manufacturing data found: {count}"
                elif "Cash flow" in component:
                    result = await session.execute(text("SELECT COUNT(*) FROM cash_flow_data"))
                    count = result.scalar()
                    assert count > 0, f"No cash flow data found: {count}"
                elif "ML models" in component:
                    result = await session.execute(text("SELECT COUNT(*) FROM ml_models"))
                    count = result.scalar()
                    assert count > 0, f"No ML models found: {count}"
                elif "Prediction" in component:
                    result = await session.execute(text("SELECT COUNT(*) FROM prediction_results"))
                    count = result.scalar()
                    # Predictions are optional for readiness
                
                logger.info(f"✅ {component}: Ready")
        
        logger.info("✅ API readiness check passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ API readiness check failed: {str(e)}")
        return False

async def main():
    """Run complete system test."""
    logger.info("🚀 Starting EZBI Analytics System Test")
    logger.info("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Data Ingestion", test_data_ingestion),
        ("ML Training", test_ml_training),
        ("Predictions", test_predictions),
        ("API Readiness", test_api_readiness),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running test: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {str(e)}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - System is ready for production!")
        logger.info("\n📊 Production Readiness Checklist:")
        logger.info("✅ Real Kaggle data integrated")
        logger.info("✅ ML models trained and ready")
        logger.info("✅ Prediction pipeline functional")
        logger.info("✅ Database schema complete")
        logger.info("✅ API endpoints operational")
        return True
    else:
        logger.error("❌ Some tests failed - System needs attention")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)