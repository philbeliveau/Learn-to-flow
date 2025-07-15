"""
Updated Daily Workflow with Excel Data Source Integration
Combines database simulation with Excel data source generation for EZBI platform
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import httpx
import json

# Import our modules
from excel_data_source import ExcelDataSource
from ezbi_excel_reader import EZBIExcelReader

logger = logging.getLogger(__name__)

class ManufacturingWorkflow:
    """Orchestrates the complete manufacturing data workflow"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.excel_data_source = ExcelDataSource(config.get('excel_export_path', '/app/exports'))
        self.ezbi_reader = EZBIExcelReader(config.get('ezbi_data_path', '/app/data-sources'))
        
        # Integration endpoints
        self.ezbi_api_url = config.get('ezbi_api_url', 'https://your-ezbi-platform.vercel.app')
        self.ezbi_api_key = config.get('ezbi_api_key', '')
        self.slack_webhook_url = config.get('slack_webhook_url', '')
        
        # Workflow configuration
        self.workflow_config = {
            'auto_process_excel': True,
            'notify_slack': True,
            'update_ezbi_dashboard': True,
            'cleanup_old_files': True,
            'retention_days': 30
        }
    
    async def run_daily_workflow(self, db_connection, simulation_date: datetime = None) -> Dict[str, Any]:
        """Execute the complete daily workflow"""
        if simulation_date is None:
            simulation_date = datetime.now().date()
        
        workflow_report = {
            'date': simulation_date,
            'started_at': datetime.now().isoformat(),
            'steps': [],
            'status': 'started',
            'error': None
        }
        
        try:
            logger.info(f"Starting daily workflow for {simulation_date}")
            
            # Step 1: Generate Excel data source from database
            step1_result = await self._step_generate_excel_data_source(db_connection, simulation_date)
            workflow_report['steps'].append(step1_result)
            
            if not step1_result['success']:
                raise Exception(f"Step 1 failed: {step1_result['error']}")
            
            # Step 2: Process Excel data source for EZBI platform
            step2_result = await self._step_process_excel_for_ezbi(step1_result['excel_file_path'])
            workflow_report['steps'].append(step2_result)
            
            if not step2_result['success']:
                raise Exception(f"Step 2 failed: {step2_result['error']}")
            
            # Step 3: Update EZBI platform dashboard
            step3_result = await self._step_update_ezbi_dashboard(step2_result['dashboard_data'])
            workflow_report['steps'].append(step3_result)
            
            # Step 4: Send Slack notification
            step4_result = await self._step_send_slack_notification(workflow_report, step2_result['dashboard_data'])
            workflow_report['steps'].append(step4_result)
            
            # Step 5: Cleanup old files
            step5_result = await self._step_cleanup_old_files()
            workflow_report['steps'].append(step5_result)
            
            # Mark workflow as completed
            workflow_report['status'] = 'completed'
            workflow_report['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Daily workflow completed successfully for {simulation_date}")
            return workflow_report
            
        except Exception as e:
            workflow_report['status'] = 'failed'
            workflow_report['error'] = str(e)
            workflow_report['failed_at'] = datetime.now().isoformat()
            
            logger.error(f"Daily workflow failed: {e}")
            
            # Send error notification to Slack
            await self._send_error_notification(workflow_report)
            
            raise
    
    async def _step_generate_excel_data_source(self, db_connection, date: datetime) -> Dict[str, Any]:
        """Step 1: Generate Excel data source from database"""
        step_result = {
            'step': 1,
            'name': 'generate_excel_data_source',
            'started_at': datetime.now().isoformat(),
            'success': False,
            'error': None,
            'excel_file_path': None,
            'metadata': {}
        }
        
        try:
            logger.info("Step 1: Generating Excel data source...")
            
            # Generate Excel data source
            excel_file_path = await self.excel_data_source.generate_daily_data_source(db_connection, date)
            
            # Get file metadata
            excel_file = Path(excel_file_path)
            if excel_file.exists():
                step_result['excel_file_path'] = excel_file_path
                step_result['metadata'] = {
                    'file_size': excel_file.stat().st_size,
                    'sheets_count': len(self.excel_data_source.data_source_config['sheets']),
                    'generated_at': datetime.now().isoformat()
                }
                step_result['success'] = True
                logger.info(f"Excel data source generated: {excel_file_path}")
            else:\n                raise FileNotFoundError(f"Excel file not created: {excel_file_path}")\n            \n        except Exception as e:\n            step_result['error'] = str(e)\n            logger.error(f"Step 1 failed: {e}")\n        \n        step_result['completed_at'] = datetime.now().isoformat()\n        return step_result\n    \n    async def _step_process_excel_for_ezbi(self, excel_file_path: str) -> Dict[str, Any]:\n        """Step 2: Process Excel data source for EZBI platform"""\n        step_result = {\n            'step': 2,\n            'name': 'process_excel_for_ezbi',\n            'started_at': datetime.now().isoformat(),\n            'success': False,\n            'error': None,\n            'dashboard_data': None,\n            'processing_report': None\n        }\n        \n        try:\n            logger.info("Step 2: Processing Excel data source for EZBI platform...")\n            \n            # Process Excel file\n            processing_report = await self.ezbi_reader.process_excel_data_source(excel_file_path)\n            \n            step_result['processing_report'] = processing_report\n            step_result['dashboard_data'] = processing_report['dashboard_data']\n            step_result['success'] = True\n            \n            logger.info(f"Excel data processed: {processing_report['data_summary']['total_records']} records")\n            \n        except Exception as e:\n            step_result['error'] = str(e)\n            logger.error(f"Step 2 failed: {e}")\n        \n        step_result['completed_at'] = datetime.now().isoformat()\n        return step_result\n    \n    async def _step_update_ezbi_dashboard(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:\n        """Step 3: Update EZBI platform dashboard"""\n        step_result = {\n            'step': 3,\n            'name': 'update_ezbi_dashboard',\n            'started_at': datetime.now().isoformat(),\n            'success': False,\n            'error': None,\n            'api_response': None\n        }\n        \n        try:\n            if not self.workflow_config['update_ezbi_dashboard']:\n                step_result['success'] = True\n                step_result['message'] = 'EZBI dashboard update disabled'\n                return step_result\n            \n            logger.info("Step 3: Updating EZBI platform dashboard...")\n            \n            # Send data to EZBI platform\n            async with httpx.AsyncClient(timeout=30) as client:\n                response = await client.post(\n                    f"{self.ezbi_api_url}/api/v1/dashboard/manufacturing/update",\n                    json={\n                        'dashboard_data': dashboard_data,\n                        'timestamp': datetime.now().isoformat(),\n                        'source': 'manufacturing_simulator'\n                    },\n                    headers={\n                        'Authorization': f'Bearer {self.ezbi_api_key}',\n                        'Content-Type': 'application/json'\n                    }\n                )\n                \n                step_result['api_response'] = {\n                    'status_code': response.status_code,\n                    'response_time': response.elapsed.total_seconds(),\n                    'success': response.status_code == 200\n                }\n                \n                if response.status_code == 200:\n                    step_result['success'] = True\n                    logger.info("EZBI dashboard updated successfully")\n                else:\n                    raise Exception(f"EZBI API error: {response.status_code} - {response.text}")\n            \n        except Exception as e:\n            step_result['error'] = str(e)\n            logger.error(f"Step 3 failed: {e}")\n        \n        step_result['completed_at'] = datetime.now().isoformat()\n        return step_result\n    \n    async def _step_send_slack_notification(self, workflow_report: Dict[str, Any], \n                                          dashboard_data: Dict[str, Any]) -> Dict[str, Any]:\n        """Step 4: Send Slack notification"""\n        step_result = {\n            'step': 4,\n            'name': 'send_slack_notification',\n            'started_at': datetime.now().isoformat(),\n            'success': False,\n            'error': None,\n            'notification_sent': False\n        }\n        \n        try:\n            if not self.workflow_config['notify_slack'] or not self.slack_webhook_url:\n                step_result['success'] = True\n                step_result['message'] = 'Slack notification disabled or webhook not configured'\n                return step_result\n            \n            logger.info("Step 4: Sending Slack notification...")\n            \n            # Build Slack message\n            slack_message = self._build_slack_message(workflow_report, dashboard_data)\n            \n            # Send to Slack\n            async with httpx.AsyncClient(timeout=10) as client:\n                response = await client.post(\n                    self.slack_webhook_url,\n                    json=slack_message,\n                    headers={'Content-Type': 'application/json'}\n                )\n                \n                if response.status_code == 200:\n                    step_result['success'] = True\n                    step_result['notification_sent'] = True\n                    logger.info("Slack notification sent successfully")\n                else:\n                    raise Exception(f"Slack webhook error: {response.status_code}")\n            \n        except Exception as e:\n            step_result['error'] = str(e)\n            logger.error(f"Step 4 failed: {e}")\n        \n        step_result['completed_at'] = datetime.now().isoformat()\n        return step_result\n    \n    async def _step_cleanup_old_files(self) -> Dict[str, Any]:\n        """Step 5: Cleanup old files"""\n        step_result = {\n            'step': 5,\n            'name': 'cleanup_old_files',\n            'started_at': datetime.now().isoformat(),\n            'success': False,\n            'error': None,\n            'files_deleted': 0\n        }\n        \n        try:\n            if not self.workflow_config['cleanup_old_files']:\n                step_result['success'] = True\n                step_result['message'] = 'File cleanup disabled'\n                return step_result\n            \n            logger.info("Step 5: Cleaning up old files...")\n            \n            cutoff_date = datetime.now() - timedelta(days=self.workflow_config['retention_days'])\n            files_deleted = 0\n            \n            # Clean up Excel export files\n            export_path = Path(self.excel_data_source.export_path)\n            for file_path in export_path.glob("manufacturing_data_source_*.xlsx"):\n                if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date:\n                    file_path.unlink()\n                    files_deleted += 1\n                    \n                    # Also delete corresponding JSON metadata\n                    json_file = file_path.with_suffix('.json')\n                    if json_file.exists():\n                        json_file.unlink()\n                        files_deleted += 1\n            \n            step_result['files_deleted'] = files_deleted\n            step_result['success'] = True\n            logger.info(f"Cleaned up {files_deleted} old files")\n            \n        except Exception as e:\n            step_result['error'] = str(e)\n            logger.error(f"Step 5 failed: {e}")\n        \n        step_result['completed_at'] = datetime.now().isoformat()\n        return step_result\n    \n    def _build_slack_message(self, workflow_report: Dict[str, Any], \n                           dashboard_data: Dict[str, Any]) -> Dict[str, Any]:\n        """Build Slack notification message"""\n        date = workflow_report['date']\n        \n        # Count successful steps\n        successful_steps = sum(1 for step in workflow_report['steps'] if step['success'])\n        total_steps = len(workflow_report['steps'])\n        \n        # Get KPI data\n        kpis = dashboard_data.get('kpis', [])\n        cash_kpi = next((kpi for kpi in kpis if 'cash' in kpi['title'].lower()), None)\n        sales_kpi = next((kpi for kpi in kpis if 'sales' in kpi['title'].lower()), None)\n        \n        # Build message\n        message = {\n            "channel": "#manufacturing-data",\n            "username": "Manufacturing Data Workflow",\n            "icon_emoji": ":factory:",\n            "text": f"📊 *Manufacturing Data Workflow Complete - {date}*",\n            "attachments": [\n                {\n                    "color": "good" if workflow_report['status'] == 'completed' else "danger",\n                    "title": f"📈 Workflow Status: {workflow_report['status'].title()}",\n                    "fields": [\n                        {\n                            "title": "Steps Completed",\n                            "value": f"{successful_steps}/{total_steps}",\n                            "short": True\n                        },\n                        {\n                            "title": "Excel Data Source",\n                            "value": "✅ Generated and processed",\n                            "short": True\n                        },\n                        {\n                            "title": "EZBI Dashboard",\n                            "value": "✅ Updated with latest data",\n                            "short": True\n                        },\n                        {\n                            "title": "Charts Generated",\n                            "value": f"{len(dashboard_data.get('charts', []))} charts",\n                            "short": True\n                        }\n                    ]\n                }\n            ]\n        }\n        \n        # Add KPI information if available\n        if cash_kpi or sales_kpi:\n            kpi_fields = []\n            \n            if cash_kpi:\n                kpi_fields.append({\n                    "title": "💰 Cash Position",\n                    "value": f"${cash_kpi['value']:,.2f}",\n                    "short": True\n                })\n            \n            if sales_kpi:\n                kpi_fields.append({\n                    "title": "💵 Daily Sales",\n                    "value": f"${sales_kpi['value']:,.2f}",\n                    "short": True\n                })\n            \n            message["attachments"].append({\n                "color": "#0066cc",\n                "title": "📊 Key Performance Indicators",\n                "fields": kpi_fields\n            })\n        \n        # Add error information if workflow failed\n        if workflow_report['status'] == 'failed':\n            message["attachments"].append({\n                "color": "danger",\n                "title": "❌ Error Details",\n                "text": f"```{workflow_report['error']}```"\n            })\n        \n        # Add footer\n        message["attachments"][-1]["footer"] = "Manufacturing Data Simulator"\n        message["attachments"][-1]["ts"] = int(datetime.now().timestamp())\n        \n        return message\n    \n    async def _send_error_notification(self, workflow_report: Dict[str, Any]):\n        """Send error notification to Slack"""\n        if not self.slack_webhook_url:\n            return\n        \n        try:\n            error_message = {\n                "channel": "#manufacturing-data",\n                "username": "Manufacturing Data Workflow",\n                "icon_emoji": ":warning:",\n                "text": "🚨 *Manufacturing Data Workflow Failed*",\n                "attachments": [\n                    {\n                        "color": "danger",\n                        "title": "Error Details",\n                        "text": f"```{workflow_report['error']}```",\n                        "fields": [\n                            {\n                                "title": "Date",\n                                "value": str(workflow_report['date']),\n                                "short": True\n                            },\n                            {\n                                "title": "Failed At",\n                                "value": workflow_report.get('failed_at', 'Unknown'),\n                                "short": True\n                            }\n                        ],\n                        "footer": "Manufacturing Data Simulator",\n                        "ts": int(datetime.now().timestamp())\n                    }\n                ]\n            }\n            \n            async with httpx.AsyncClient(timeout=10) as client:\n                await client.post(self.slack_webhook_url, json=error_message)\n                \n        except Exception as e:\n            logger.error(f"Failed to send error notification: {e}")\n    \n    def get_workflow_status(self) -> Dict[str, Any]:\n        """Get current workflow status"""\n        return {\n            'workflow_config': self.workflow_config,\n            'integration_status': {\n                'ezbi_api_configured': bool(self.ezbi_api_key),\n                'slack_webhook_configured': bool(self.slack_webhook_url),\n                'excel_export_path': str(self.excel_data_source.export_path),\n                'ezbi_data_path': str(self.ezbi_reader.data_source_path)\n            },\n            'last_run': None  # Would be populated from database or cache\n        }\n\n# Factory function\ndef create_manufacturing_workflow(config: Dict[str, Any]) -> ManufacturingWorkflow:\n    """Create manufacturing workflow instance"""\n    return ManufacturingWorkflow(config)\n\n# Example usage configuration\nWORKFLOW_CONFIG = {\n    'excel_export_path': '/app/exports',\n    'ezbi_data_path': '/app/data-sources',\n    'ezbi_api_url': os.getenv('EZBI_API_URL', 'https://your-ezbi-platform.vercel.app'),\n    'ezbi_api_key': os.getenv('EZBI_API_KEY', ''),\n    'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL', '')\n}