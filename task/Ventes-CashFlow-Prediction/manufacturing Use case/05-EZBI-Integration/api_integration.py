"""
EZBI Platform Integration Module
Handles data synchronization between Railway simulator and Vercel-hosted EZBI platform
"""

import os
import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EZBIConfig:
    """EZBI Platform configuration"""
    api_url: str
    api_key: str
    webhook_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

class EZBIIntegration:
    """Handles all EZBI platform integrations"""
    
    def __init__(self, config: EZBIConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Manufacturing-Simulator/1.0"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def sync_daily_data(self, simulation_date: datetime, data_summary: Dict[str, Any]) -> bool:
        """Sync daily simulation data to EZBI platform"""
        try:
            endpoint = f"{self.config.api_url}/api/v1/manufacturing/daily-data"
            
            payload = {
                "simulation_date": simulation_date.isoformat(),
                "data_summary": data_summary,
                "source": "manufacturing_simulator",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = await self._make_request("POST", endpoint, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Successfully synced data for {simulation_date}")
                return True
            else:
                logger.error(f"Failed to sync data: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error syncing daily data: {e}")
            return False
    
    async def send_financial_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send financial metrics for cash flow prediction"""
        try:
            endpoint = f"{self.config.api_url}/api/v1/analytics/financial-metrics"
            
            # Transform metrics for EZBI format
            ezbi_metrics = {
                "cash_position": metrics.get("current_cash_balance", 0),
                "accounts_receivable": metrics.get("accounts_receivable_total", 0),
                "accounts_payable": metrics.get("accounts_payable_total", 0),
                "revenue_current_month": metrics.get("monthly_revenue", 0),
                "expenses_current_month": metrics.get("monthly_expenses", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "period": "daily"
            }
            
            response = await self._make_request("POST", endpoint, json=ezbi_metrics)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending financial metrics: {e}")
            return False
    
    async def upload_excel_file(self, file_path: str, file_type: str = "daily_export") -> Optional[str]:
        """Upload Excel file to EZBI platform"""
        try:
            endpoint = f"{self.config.api_url}/api/v1/files/upload"
            
            with open(file_path, "rb") as file:
                files = {"file": (os.path.basename(file_path), file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                data = {
                    "file_type": file_type,
                    "source": "manufacturing_simulator",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Use different client for file upload
                async with httpx.AsyncClient(timeout=60) as upload_client:
                    response = await upload_client.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers={"Authorization": f"Bearer {self.config.api_key}"}
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Excel file uploaded successfully: {result.get('file_id')}")
                    return result.get("file_url")
                else:
                    logger.error(f"Failed to upload Excel file: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error uploading Excel file: {e}")
            return None
    
    async def trigger_cash_flow_prediction(self, forecast_days: int = 30) -> Optional[Dict[str, Any]]:
        """Trigger cash flow prediction in EZBI platform"""
        try:
            endpoint = f"{self.config.api_url}/api/v1/predictions/cash-flow"
            
            payload = {
                "forecast_days": forecast_days,
                "include_scenarios": True,
                "source_data": "manufacturing_simulator",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = await self._make_request("POST", endpoint, json=payload)
            
            if response.status_code == 200:
                prediction_result = response.json()
                logger.info(f"Cash flow prediction triggered: {prediction_result.get('prediction_id')}")
                return prediction_result
            else:
                logger.error(f"Failed to trigger prediction: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error triggering cash flow prediction: {e}")
            return None
    
    async def get_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """Fetch current dashboard data from EZBI platform"""
        try:
            endpoint = f"{self.config.api_url}/api/v1/dashboard/manufacturing"
            
            response = await self._make_request("GET", endpoint)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch dashboard data: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            return None
    
    async def send_health_check(self) -> bool:
        """Send health check to EZBI platform"""
        try:
            endpoint = f"{self.config.api_url}/api/v1/integrations/health"
            
            payload = {
                "service": "manufacturing_simulator",
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
            
            response = await self._make_request("POST", endpoint, json=payload)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending health check: {e}")
            return False
    
    async def notify_simulation_complete(self, simulation_report: Dict[str, Any]) -> bool:
        """Notify EZBI platform that daily simulation is complete"""
        try:
            if not self.config.webhook_url:
                logger.warning("No webhook URL configured for simulation notifications")
                return True
            
            payload = {
                "event": "simulation_complete",
                "data": simulation_report,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "manufacturing_simulator"
            }
            
            response = await self._make_request("POST", self.config.webhook_url, json=payload)
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            logger.error(f"Error sending simulation notification: {e}")
            return False
    
    async def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)
                return response
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.config.max_retries} attempts: {e}")
        
        raise last_exception

class EZBIDataFormatter:
    """Formats manufacturing data for EZBI platform consumption"""
    
    @staticmethod
    def format_cash_flow_data(cash_transactions: List[Dict]) -> Dict[str, Any]:
        """Format cash flow data for EZBI charts"""
        daily_flows = {}
        
        for transaction in cash_transactions:
            date_key = transaction['date_recorded'].strftime('%Y-%m-%d')
            
            if date_key not in daily_flows:
                daily_flows[date_key] = {
                    "date": date_key,
                    "inflows": 0,
                    "outflows": 0,
                    "net_flow": 0
                }
            
            amount = float(transaction['amount'])
            if amount > 0:
                daily_flows[date_key]["inflows"] += amount
            else:
                daily_flows[date_key]["outflows"] += abs(amount)
            
            daily_flows[date_key]["net_flow"] += amount
        
        return {
            "daily_cash_flows": list(daily_flows.values()),
            "summary": {
                "total_inflows": sum(day["inflows"] for day in daily_flows.values()),
                "total_outflows": sum(day["outflows"] for day in daily_flows.values()),
                "net_change": sum(day["net_flow"] for day in daily_flows.values())
            }
        }
    
    @staticmethod
    def format_ar_aging_data(ar_records: List[Dict]) -> Dict[str, Any]:
        """Format AR aging data for EZBI visualization"""
        aging_summary = {
            "0-30": 0,
            "31-60": 0,
            "61-90": 0,
            "90+": 0
        }
        
        for record in ar_records:
            bucket = record['aging_bucket']
            aging_summary[bucket] += float(record['amount_outstanding'])
        
        total_ar = sum(aging_summary.values())
        
        return {
            "aging_buckets": [
                {"bucket": bucket, "amount": amount, "percentage": (amount/total_ar*100) if total_ar > 0 else 0}
                for bucket, amount in aging_summary.items()
            ],
            "total_receivables": total_ar,
            "current_ratio": (aging_summary["0-30"] / total_ar * 100) if total_ar > 0 else 0
        }
    
    @staticmethod
    def format_production_metrics(production_orders: List[Dict]) -> Dict[str, Any]:
        """Format production data for EZBI dashboard"""
        status_counts = {}
        total_value = 0
        
        for order in production_orders:
            status = order['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            total_value += float(order.get('cost_of_goods_sold', 0))
        
        return {
            "production_summary": {
                "total_orders": len(production_orders),
                "total_value": total_value,
                "status_breakdown": status_counts
            },
            "efficiency_metrics": {
                "completion_rate": (status_counts.get('Completed', 0) / len(production_orders) * 100) if production_orders else 0,
                "average_order_value": total_value / len(production_orders) if production_orders else 0
            }
        }

# Factory function for easy initialization
def create_ezbi_integration() -> EZBIIntegration:
    """Create EZBI integration instance from environment variables"""
    config = EZBIConfig(
        api_url=os.getenv("EZBI_API_URL", "https://your-ezbi-platform.vercel.app"),
        api_key=os.getenv("EZBI_API_KEY", ""),
        webhook_url=os.getenv("EZBI_WEBHOOK_URL"),
        timeout=int(os.getenv("EZBI_TIMEOUT", "30")),
        max_retries=int(os.getenv("EZBI_MAX_RETRIES", "3"))
    )
    
    return EZBIIntegration(config)