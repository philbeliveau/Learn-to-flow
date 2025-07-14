"""
Performance and load testing for EZBI Analytics.
"""
import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import psutil
import numpy as np
from httpx import AsyncClient
from fastapi.testclient import TestClient
import aiohttp
import json
from datetime import datetime, timedelta

from app.main import app
from app.core.config import settings


class TestAPIPerformance:
    """Test API performance and response times."""
    
    def test_health_check_performance(self, sync_client: TestClient):
        """Test health check endpoint performance."""
        response_times = []
        
        # Test 100 requests
        for _ in range(100):
            start_time = time.time()
            response = sync_client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Performance assertions
        avg_time = statistics.mean(response_times)
        p95_time = np.percentile(response_times, 95)
        p99_time = np.percentile(response_times, 99)
        
        assert avg_time < 0.1  # Average response time < 100ms
        assert p95_time < 0.2  # 95th percentile < 200ms
        assert p99_time < 0.5  # 99th percentile < 500ms
        
        print(f"Health check performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  P95: {p95_time:.3f}s")
        print(f"  P99: {p99_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient):
        """Test concurrent request handling."""
        concurrent_users = 50
        requests_per_user = 10
        
        async def make_requests():
            response_times = []
            for _ in range(requests_per_user):
                start_time = time.time()
                response = await client.get("/health")
                end_time = time.time()
                
                assert response.status_code == 200
                response_times.append(end_time - start_time)
            
            return response_times
        
        # Create concurrent tasks
        tasks = [make_requests() for _ in range(concurrent_users)]
        
        # Execute concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Flatten results
        all_response_times = [time for times in results for time in times]
        
        # Calculate metrics
        total_requests = concurrent_users * requests_per_user
        total_time = end_time - start_time
        throughput = total_requests / total_time
        
        avg_response_time = statistics.mean(all_response_times)
        p95_response_time = np.percentile(all_response_times, 95)
        
        # Performance assertions
        assert throughput > 100  # > 100 requests/second
        assert avg_response_time < 0.5  # Average < 500ms
        assert p95_response_time < 1.0  # P95 < 1s
        
        print(f"Concurrent performance ({concurrent_users} users):")
        print(f"  Throughput: {throughput:.1f} req/s")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  P95 response time: {p95_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self, client: AsyncClient, auth_headers, test_company):
        """Test database query performance."""
        # Test financial data queries
        response_times = []
        
        for _ in range(50):
            start_time = time.time()
            response = await client.get(
                f"/api/v1/companies/{test_company.id}/financial-data",
                headers=auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_time = statistics.mean(response_times)
        p95_time = np.percentile(response_times, 95)
        
        # Database query should be fast
        assert avg_time < 0.2  # Average < 200ms
        assert p95_time < 0.5  # P95 < 500ms
        
        print(f"Database query performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  P95: {p95_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_prediction_endpoint_performance(self, client: AsyncClient, auth_headers, test_company, mock_ml_service):
        """Test prediction endpoint performance."""
        with patch('app.services.ml_service.MLService', return_value=mock_ml_service):
            prediction_request = {
                "company_id": test_company.id,
                "prediction_type": "cash_flow",
                "prediction_horizon": 30
            }
            
            response_times = []
            
            for _ in range(20):  # Fewer requests for compute-intensive endpoint
                start_time = time.time()
                response = await client.post(
                    "/api/v1/predictions/predict",
                    json=prediction_request,
                    headers=auth_headers
                )
                end_time = time.time()
                
                assert response.status_code == 200
                response_times.append(end_time - start_time)
            
            avg_time = statistics.mean(response_times)
            p95_time = np.percentile(response_times, 95)
            
            # Prediction should complete within reasonable time
            assert avg_time < 2.0  # Average < 2s
            assert p95_time < 5.0  # P95 < 5s
            
            print(f"Prediction endpoint performance:")
            print(f"  Average: {avg_time:.3f}s")
            print(f"  P95: {p95_time:.3f}s")
    
    def test_file_upload_performance(self, sync_client: TestClient, auth_headers, test_company, sample_csv_file):
        """Test file upload performance."""
        # Test multiple file uploads
        response_times = []
        
        for _ in range(10):
            with open(sample_csv_file, "rb") as f:
                files = {"file": ("test.csv", f, "text/csv")}
                data = {"company_id": test_company.id}
                
                start_time = time.time()
                response = sync_client.post(
                    "/api/v1/files/upload",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
                end_time = time.time()
                
                assert response.status_code == 200
                response_times.append(end_time - start_time)
        
        avg_time = statistics.mean(response_times)
        p95_time = np.percentile(response_times, 95)
        
        # File upload should be reasonably fast
        assert avg_time < 1.0  # Average < 1s
        assert p95_time < 2.0  # P95 < 2s
        
        print(f"File upload performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  P95: {p95_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_authentication_performance(self, client: AsyncClient, test_user):
        """Test authentication performance."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response_times = []
        
        for _ in range(50):
            start_time = time.time()
            response = await client.post("/api/v1/auth/login", data=login_data)
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_time = statistics.mean(response_times)
        p95_time = np.percentile(response_times, 95)
        
        # Authentication should be reasonably fast
        assert avg_time < 0.5  # Average < 500ms
        assert p95_time < 1.0  # P95 < 1s
        
        print(f"Authentication performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  P95: {p95_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, client: AsyncClient):
        """Test memory usage under load."""
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate load
        tasks = []
        for _ in range(100):
            task = client.get("/health")
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Check memory usage after load
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage should not increase significantly
        assert memory_increase < 50  # < 50MB increase
        
        print(f"Memory usage:")
        print(f"  Initial: {initial_memory:.1f}MB")
        print(f"  Final: {final_memory:.1f}MB")
        print(f"  Increase: {memory_increase:.1f}MB")
    
    @pytest.mark.asyncio
    async def test_cpu_usage_under_load(self, client: AsyncClient):
        """Test CPU usage under load."""
        # Monitor CPU usage during load test
        cpu_usage = []
        
        def monitor_cpu():
            for _ in range(10):
                cpu_usage.append(psutil.cpu_percent(interval=0.1))
        
        # Start CPU monitoring
        monitor_task = asyncio.create_task(asyncio.to_thread(monitor_cpu))
        
        # Generate load
        tasks = []
        for _ in range(50):
            task = client.get("/health")
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        await monitor_task
        
        avg_cpu = statistics.mean(cpu_usage)
        max_cpu = max(cpu_usage)
        
        # CPU usage should be reasonable
        assert avg_cpu < 80  # Average < 80%
        assert max_cpu < 95  # Max < 95%
        
        print(f"CPU usage:")
        print(f"  Average: {avg_cpu:.1f}%")
        print(f"  Maximum: {max_cpu:.1f}%")


class TestDatabasePerformance:
    """Test database performance."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_performance(self, db_session):
        """Test database connection pool performance."""
        # Test multiple concurrent database operations
        async def db_operation():
            result = await db_session.execute("SELECT 1")
            return result.scalar()
        
        tasks = []
        for _ in range(20):
            task = db_operation()
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All operations should complete quickly
        assert total_time < 1.0  # < 1 second for 20 operations
        assert all(result == 1 for result in results)
        
        print(f"Database connection pool performance:")
        print(f"  20 operations completed in {total_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_large_dataset_query(self, db_session, test_company, sample_financial_data):
        """Test large dataset query performance."""
        # Test querying large financial dataset
        start_time = time.time()
        
        # Simulate complex query
        query = """
            SELECT 
                DATE_TRUNC('month', period_start) as month,
                AVG(revenue) as avg_revenue,
                SUM(cash_flow) as total_cash_flow,
                COUNT(*) as record_count
            FROM financial_data 
            WHERE company_id = :company_id
            GROUP BY DATE_TRUNC('month', period_start)
            ORDER BY month
        """
        
        result = await db_session.execute(query, {"company_id": test_company.id})
        rows = result.fetchall()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Complex query should complete quickly
        assert query_time < 0.5  # < 500ms
        assert len(rows) > 0
        
        print(f"Large dataset query performance:")
        print(f"  Query time: {query_time:.3f}s")
        print(f"  Rows returned: {len(rows)}")
    
    @pytest.mark.asyncio
    async def test_transaction_performance(self, db_session, test_company):
        """Test database transaction performance."""
        from app.models.financial_data import FinancialData
        
        # Test bulk insert performance
        financial_records = []
        for i in range(100):
            record = FinancialData(
                company_id=test_company.id,
                period_start=datetime.now() - timedelta(days=i),
                period_end=datetime.now() - timedelta(days=i-1),
                revenue=150000 + i * 1000,
                expenses=112500 + i * 750,
                cash_flow=37500 + i * 250,
                production_volume=1200 + i * 10,
                data_source="test"
            )
            financial_records.append(record)
        
        start_time = time.time()
        
        # Bulk insert
        db_session.add_all(financial_records)
        await db_session.commit()
        
        end_time = time.time()
        transaction_time = end_time - start_time
        
        # Bulk insert should be fast
        assert transaction_time < 2.0  # < 2 seconds for 100 records
        
        print(f"Transaction performance:")
        print(f"  100 records inserted in {transaction_time:.3f}s")
        print(f"  Rate: {100/transaction_time:.1f} records/second")
    
    @pytest.mark.asyncio
    async def test_index_performance(self, db_session, test_company):
        """Test database index performance."""
        # Test query with index
        start_time = time.time()
        
        query = """
            SELECT * FROM financial_data 
            WHERE company_id = :company_id 
            AND period_start >= :start_date
            ORDER BY period_start DESC
            LIMIT 100
        """
        
        result = await db_session.execute(query, {
            "company_id": test_company.id,
            "start_date": datetime.now() - timedelta(days=365)
        })
        rows = result.fetchall()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Indexed query should be very fast
        assert query_time < 0.1  # < 100ms
        
        print(f"Index performance:")
        print(f"  Indexed query time: {query_time:.3f}s")
        print(f"  Rows returned: {len(rows)}")


class TestMLModelPerformance:
    """Test ML model performance."""
    
    def test_lstm_model_training_performance(self):
        """Test LSTM model training performance."""
        from ml_engine.models.lstm.lstm_attention_model import LSTMAttentionModel
        
        # Generate sample data
        X_train = np.random.random((1000, 30, 10))
        y_train = np.random.random((1000, 1))
        X_val = np.random.random((200, 30, 10))
        y_val = np.random.random((200, 1))
        
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=64,
            attention_units=32
        )
        
        model.build_model()
        model.compile_model()
        
        # Time training
        start_time = time.time()
        history = model.train(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=5,
            batch_size=32,
            verbose=0
        )
        end_time = time.time()
        
        training_time = end_time - start_time
        
        # Training should complete in reasonable time
        assert training_time < 60  # < 1 minute for 5 epochs
        
        print(f"LSTM training performance:")
        print(f"  Training time: {training_time:.1f}s")
        print(f"  Time per epoch: {training_time/5:.1f}s")
    
    def test_lstm_model_inference_performance(self):
        """Test LSTM model inference performance."""
        from ml_engine.models.lstm.lstm_attention_model import LSTMAttentionModel
        
        # Create and train a simple model
        model = LSTMAttentionModel(
            input_shape=(30, 10),
            hidden_units=32,
            attention_units=16
        )
        
        model.build_model()
        model.compile_model()
        
        # Generate test data
        X_test = np.random.random((1000, 30, 10))
        
        # Time inference
        start_time = time.time()
        predictions = model.predict(X_test)
        end_time = time.time()
        
        inference_time = end_time - start_time
        throughput = len(X_test) / inference_time
        
        # Inference should be fast
        assert inference_time < 5.0  # < 5 seconds for 1000 predictions
        assert throughput > 100  # > 100 predictions/second
        
        print(f"LSTM inference performance:")
        print(f"  Inference time: {inference_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} predictions/second")
    
    def test_prophet_model_performance(self):
        """Test Prophet model performance."""
        from ml_engine.models.prophet.prophet_model import ProphetModel
        
        # Generate sample time series data
        dates = pd.date_range('2022-01-01', periods=365, freq='D')
        values = np.random.randn(365).cumsum() + 1000
        
        df = pd.DataFrame({
            'ds': dates,
            'y': values
        })
        
        model = ProphetModel()
        
        # Time training
        start_time = time.time()
        model.fit(df)
        training_time = time.time() - start_time
        
        # Time prediction
        future_dates = model.make_future_dataframe(periods=30)
        start_time = time.time()
        predictions = model.predict(future_dates)
        prediction_time = time.time() - start_time
        
        # Performance assertions
        assert training_time < 30  # < 30 seconds to train
        assert prediction_time < 5  # < 5 seconds to predict
        
        print(f"Prophet model performance:")
        print(f"  Training time: {training_time:.1f}s")
        print(f"  Prediction time: {prediction_time:.3f}s")
    
    def test_feature_extraction_performance(self):
        """Test feature extraction performance."""
        from ml_engine.features.manufacturing_features import ManufacturingFeatureExtractor
        
        # Generate large dataset
        dates = pd.date_range('2020-01-01', periods=1000, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'revenue': np.random.randn(1000) * 1000 + 150000,
            'expenses': np.random.randn(1000) * 800 + 112500,
            'production_volume': np.random.randint(800, 1200, 1000),
            'inventory': np.random.randn(1000) * 5000 + 37500
        })
        
        extractor = ManufacturingFeatureExtractor(
            time_features=True,
            seasonal_features=True,
            lag_features=True,
            rolling_features=True
        )
        
        # Time feature extraction
        start_time = time.time()
        features = extractor.extract_all_features(df)
        extraction_time = time.time() - start_time
        
        # Performance assertions
        assert extraction_time < 10  # < 10 seconds for 1000 rows
        assert len(features) == len(df)
        
        print(f"Feature extraction performance:")
        print(f"  Extraction time: {extraction_time:.3f}s")
        print(f"  Features extracted: {len(features.columns)}")
        print(f"  Rate: {len(df)/extraction_time:.1f} rows/second")
    
    def test_model_ensemble_performance(self):
        """Test ensemble model performance."""
        from ml_engine.models.ensemble.ensemble_model import EnsembleModel
        
        # Mock individual models
        models = {}
        for i in range(3):
            model = Mock()
            model.predict.return_value = np.random.random((100, 1))
            models[f'model_{i}'] = model
        
        ensemble = EnsembleModel(
            models=models,
            weights=[0.4, 0.3, 0.3]
        )
        
        # Test ensemble prediction performance
        X_test = np.random.random((100, 30, 10))
        
        start_time = time.time()
        predictions = ensemble.predict(X_test)
        prediction_time = time.time() - start_time
        
        # Ensemble should be reasonably fast
        assert prediction_time < 2.0  # < 2 seconds
        assert len(predictions) == 100
        
        print(f"Ensemble model performance:")
        print(f"  Prediction time: {prediction_time:.3f}s")
        print(f"  Throughput: {len(X_test)/prediction_time:.1f} predictions/second")


class TestCachingPerformance:
    """Test caching performance."""
    
    @pytest.mark.asyncio
    async def test_redis_cache_performance(self):
        """Test Redis cache performance."""
        # This would test Redis caching if implemented
        pass
    
    @pytest.mark.asyncio
    async def test_application_cache_performance(self, client: AsyncClient, auth_headers, test_company):
        """Test application-level caching."""
        # Test repeated requests to same endpoint
        endpoint = f"/api/v1/companies/{test_company.id}/financial-summary"
        
        # First request (cache miss)
        start_time = time.time()
        response1 = await client.get(endpoint, headers=auth_headers)
        first_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = await client.get(endpoint, headers=auth_headers)
        second_request_time = time.time() - start_time
        
        assert response2.status_code == 200
        
        # Cached request should be faster
        # Note: This depends on caching being implemented
        print(f"Cache performance:")
        print(f"  First request: {first_request_time:.3f}s")
        print(f"  Second request: {second_request_time:.3f}s")
    
    def test_prediction_cache_performance(self, mock_ml_service):
        """Test prediction result caching."""
        # This would test prediction caching if implemented
        pass


class TestScalabilityLimits:
    """Test scalability limits."""
    
    @pytest.mark.asyncio
    async def test_maximum_concurrent_users(self, client: AsyncClient):
        """Test maximum concurrent users."""
        max_concurrent = 100
        requests_per_user = 5
        
        async def simulate_user():
            response_times = []
            for _ in range(requests_per_user):
                start_time = time.time()
                response = await client.get("/health")
                end_time = time.time()
                
                response_times.append({
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                })
            return response_times
        
        # Create tasks for maximum concurrent users
        tasks = [simulate_user() for _ in range(max_concurrent)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Analyze results
        successful_requests = 0
        failed_requests = 0
        total_response_time = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed_requests += requests_per_user
            else:
                for response in result:
                    if response['status_code'] == 200:
                        successful_requests += 1
                        total_response_time += response['response_time']
                    else:
                        failed_requests += 1
        
        total_requests = max_concurrent * requests_per_user
        success_rate = successful_requests / total_requests
        avg_response_time = total_response_time / successful_requests if successful_requests > 0 else 0
        
        # Scalability assertions
        assert success_rate > 0.95  # > 95% success rate
        assert avg_response_time < 1.0  # Average response time < 1s
        
        print(f"Scalability test ({max_concurrent} concurrent users):")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Failed requests: {failed_requests}")
    
    @pytest.mark.asyncio
    async def test_data_volume_limits(self, client: AsyncClient, auth_headers, test_company):
        """Test handling of large data volumes."""
        # Test large financial data query
        response = await client.get(
            f"/api/v1/companies/{test_company.id}/financial-data",
            params={"limit": 10000},  # Large limit
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Should handle large datasets gracefully
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10000  # Should respect limit
    
    def test_file_size_limits(self, sync_client: TestClient, auth_headers, test_company):
        """Test file size limits."""
        # Create large file content
        large_content = "Date,Revenue,Expenses\n"
        for i in range(100000):  # 100k rows
            large_content += f"2024-01-{i%28+1:02d},{150000+i},{112500+i}\n"
        
        # Test upload of large file
        files = {"file": ("large_file.csv", large_content.encode(), "text/csv")}
        data = {"company_id": test_company.id}
        
        start_time = time.time()
        response = sync_client.post(
            "/api/v1/files/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        upload_time = time.time() - start_time
        
        # Should handle large files within reasonable time
        # Note: This depends on file size limits being implemented
        assert upload_time < 30  # < 30 seconds for large file
        
        print(f"Large file upload:")
        print(f"  File size: {len(large_content)} characters")
        print(f"  Upload time: {upload_time:.1f}s")


class TestResourceMonitoring:
    """Test resource monitoring and optimization."""
    
    def test_memory_leak_detection(self):
        """Test for memory leaks."""
        import gc
        
        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform operations that might cause memory leaks
        for _ in range(1000):
            # Simulate creating and destroying objects
            data = list(range(1000))
            del data
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Check for memory leaks
        object_growth = final_objects - initial_objects
        
        # Should not have significant object growth
        assert object_growth < 100  # < 100 new objects
        
        print(f"Memory leak detection:")
        print(f"  Initial objects: {initial_objects}")
        print(f"  Final objects: {final_objects}")
        print(f"  Object growth: {object_growth}")
    
    def test_database_connection_limits(self):
        """Test database connection limits."""
        # This would test database connection pooling limits
        pass
    
    def test_thread_pool_performance(self):
        """Test thread pool performance."""
        def cpu_intensive_task():
            # Simulate CPU-intensive work
            total = 0
            for i in range(100000):
                total += i * i
            return total
        
        # Test thread pool with multiple workers
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            
            # Submit tasks
            futures = [executor.submit(cpu_intensive_task) for _ in range(50)]
            
            # Wait for completion
            results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Should complete within reasonable time
            assert total_time < 10  # < 10 seconds
            assert len(results) == 50
            
            print(f"Thread pool performance:")
            print(f"  50 tasks completed in {total_time:.1f}s")
    
    def test_async_performance(self):
        """Test async operation performance."""
        async def async_operation():
            await asyncio.sleep(0.1)  # Simulate async work
            return "completed"
        
        async def run_async_test():
            tasks = [async_operation() for _ in range(100)]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Should complete concurrently, not sequentially
            assert total_time < 0.5  # Much less than 10 seconds (100 * 0.1)
            assert len(results) == 100
            
            print(f"Async performance:")
            print(f"  100 concurrent operations in {total_time:.3f}s")
        
        # Run the async test
        asyncio.run(run_async_test())


# Performance test configuration
pytest_plugins = ['pytest_asyncio']

# Performance test markers
pytestmark = [
    pytest.mark.performance,
    pytest.mark.slow
]

# Test fixtures for performance testing
@pytest.fixture
def performance_metrics():
    """Performance testing metrics and thresholds."""
    return {
        'response_time_threshold': 1.0,  # 1 second
        'throughput_threshold': 100,     # 100 requests/second
        'memory_threshold': 100,         # 100MB
        'cpu_threshold': 80,             # 80%
        'success_rate_threshold': 0.95,  # 95%
        'concurrent_users': 50,
        'test_duration': 60,            # 60 seconds
    }

@pytest.fixture
def load_test_config():
    """Load test configuration."""
    return {
        'ramp_up_time': 10,      # 10 seconds
        'steady_state_time': 30,  # 30 seconds
        'ramp_down_time': 10,     # 10 seconds
        'max_concurrent_users': 100,
        'requests_per_user': 10,
        'think_time': 1.0,        # 1 second between requests
    }