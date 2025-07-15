"""
Data Models for Manufacturing Data Simulator
Pydantic models for data validation and API responses
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

# ===============================
# ENUMS
# ===============================

class InvoiceStatus(str, Enum):
    OPEN = "Open"
    PAID = "Paid"
    OVERDUE = "Overdue"
    PARTIAL = "Partial"

class ProductionStatus(str, Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"

class PaymentStatus(str, Enum):
    OUTSTANDING = "Outstanding"
    PAID = "Paid"
    PARTIAL = "Partial"

class TransactionType(str, Enum):
    SALE = "Sale"
    PURCHASE = "Purchase"
    PAYROLL = "Payroll"
    LOAN_PAYMENT = "Loan Payment"
    INTEREST = "Interest"
    PAYMENT_RECEIVED = "Payment Received"
    VENDOR_PAYMENT = "Vendor Payment"
    FIXED_EXPENSE = "Fixed Expense"

class AgingBucket(str, Enum):
    CURRENT = "0-30"
    THIRTY_SIXTY = "31-60"
    SIXTY_NINETY = "61-90"
    OVER_NINETY = "90+"

class EmployeeStatus(str, Enum):
    ACTIVE = "Active"
    TERMINATED = "Terminated"
    ON_LEAVE = "On Leave"

# ===============================
# CORE BUSINESS MODELS
# ===============================

class Customer(BaseModel):
    customer_id: Optional[int] = None
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    payment_terms: int = Field(30, ge=1, le=365)
    credit_limit: Decimal = Field(Decimal('50000.00'), ge=0)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class Invoice(BaseModel):
    invoice_id: Optional[int] = None
    customer_id: int
    invoice_number: str = Field(..., max_length=50)
    date_issued: date
    due_date: date
    amount: Decimal = Field(..., ge=0)
    status: InvoiceStatus = InvoiceStatus.OPEN
    payment_date: Optional[date] = None
    
    @validator('due_date')
    def due_date_must_be_after_issued(cls, v, values):
        if 'date_issued' in values and v <= values['date_issued']:
            raise ValueError('Due date must be after issue date')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class Product(BaseModel):
    product_id: Optional[int] = None
    product_code: str = Field(..., max_length=50)
    product_name: str = Field(..., max_length=255)
    base_cost: Decimal = Field(..., ge=0)
    labor_hours: Decimal = Field(..., ge=0)
    material_cost: Decimal = Field(..., ge=0)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class ProductionOrder(BaseModel):
    order_id: Optional[int] = None
    order_number: str = Field(..., max_length=50)
    product_id: int
    customer_id: int
    start_date: date
    completion_date: Optional[date] = None
    expected_completion: date
    status: ProductionStatus = ProductionStatus.PLANNED
    units_ordered: int = Field(..., ge=1)
    units_produced: int = Field(0, ge=0)
    cost_of_goods_sold: Optional[Decimal] = Field(None, ge=0)
    labor_cost: Optional[Decimal] = Field(None, ge=0)
    material_cost: Optional[Decimal] = Field(None, ge=0)
    
    @validator('units_produced')
    def units_produced_not_exceed_ordered(cls, v, values):
        if 'units_ordered' in values and v > values['units_ordered']:
            raise ValueError('Units produced cannot exceed units ordered')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class Vendor(BaseModel):
    vendor_id: Optional[int] = None
    vendor_name: str = Field(..., max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    payment_terms: int = Field(30, ge=1, le=365)
    vendor_type: str = Field(..., max_length=50)
    
    class Config:
        use_enum_values = True

class Purchase(BaseModel):
    purchase_id: Optional[int] = None
    vendor_id: int
    purchase_number: str = Field(..., max_length=50)
    category: str = Field(..., max_length=50)
    amount: Decimal = Field(..., ge=0)
    date_purchased: date
    due_date: date
    payment_status: PaymentStatus = PaymentStatus.OUTSTANDING
    payment_date: Optional[date] = None
    description: Optional[str] = None
    
    @validator('due_date')
    def due_date_must_be_after_purchased(cls, v, values):
        if 'date_purchased' in values and v <= values['date_purchased']:
            raise ValueError('Due date must be after purchase date')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class CashTransaction(BaseModel):
    transaction_id: Optional[int] = None
    transaction_number: str = Field(..., max_length=50)
    date_recorded: date
    amount: Decimal  # Positive = inflow, Negative = outflow
    transaction_type: TransactionType
    counterparty: Optional[str] = Field(None, max_length=255)
    reference_id: Optional[int] = None
    reference_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    running_balance: Optional[Decimal] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class AccountsReceivable(BaseModel):
    ar_id: Optional[int] = None
    invoice_id: int
    customer_id: int
    amount_outstanding: Decimal = Field(..., ge=0)
    days_outstanding: int
    aging_bucket: AgingBucket
    as_of_date: date
    
    @validator('aging_bucket')
    def aging_bucket_matches_days(cls, v, values):
        if 'days_outstanding' not in values:
            return v
        
        days = values['days_outstanding']
        if days <= 30 and v != AgingBucket.CURRENT:
            raise ValueError('Days 0-30 should be in Current bucket')
        elif 31 <= days <= 60 and v != AgingBucket.THIRTY_SIXTY:
            raise ValueError('Days 31-60 should be in 31-60 bucket')
        elif 61 <= days <= 90 and v != AgingBucket.SIXTY_NINETY:
            raise ValueError('Days 61-90 should be in 61-90 bucket')
        elif days > 90 and v != AgingBucket.OVER_NINETY:
            raise ValueError('Days 90+ should be in 90+ bucket')
        
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class Employee(BaseModel):
    employee_id: Optional[int] = None
    employee_number: str = Field(..., max_length=20)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    department: str = Field(..., max_length=50)
    position: str = Field(..., max_length=100)
    hire_date: date
    annual_salary: Decimal = Field(..., ge=0)
    pay_frequency: str = Field("Bi-weekly", max_length=20)
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class PayrollRecord(BaseModel):
    payroll_id: Optional[int] = None
    employee_id: int
    pay_period_start: date
    pay_period_end: date
    pay_date: date
    gross_pay: Decimal = Field(..., ge=0)
    deductions: Decimal = Field(Decimal('0.00'), ge=0)
    net_pay: Decimal = Field(..., ge=0)
    bonus: Decimal = Field(Decimal('0.00'), ge=0)
    overtime_hours: Decimal = Field(Decimal('0.00'), ge=0)
    overtime_pay: Decimal = Field(Decimal('0.00'), ge=0)
    
    @validator('pay_period_end')
    def pay_period_end_after_start(cls, v, values):
        if 'pay_period_start' in values and v <= values['pay_period_start']:
            raise ValueError('Pay period end must be after start')
        return v
    
    @validator('net_pay')
    def net_pay_calculation(cls, v, values):
        if 'gross_pay' in values and 'deductions' in values:
            expected_net = values['gross_pay'] - values['deductions']
            if abs(float(v) - float(expected_net)) > 0.01:  # Allow for small rounding differences
                raise ValueError('Net pay must equal gross pay minus deductions')
        return v
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ===============================
# SIMULATION MODELS
# ===============================

class SimulationReport(BaseModel):
    """Daily simulation execution report"""
    simulation_date: date
    invoices_created: int = 0
    production_orders_created: int = 0
    purchases_created: int = 0
    payments_received: int = 0
    vendor_payments_made: int = 0
    payroll_processed: bool = False
    fixed_expenses_processed: int = 0
    total_transactions: int = 0
    ending_cash_balance: Decimal = Field(Decimal('0.00'))
    execution_time_seconds: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class SimulationConfig(BaseModel):
    """Configuration for simulation parameters"""
    daily_invoice_range: tuple[int, int] = (1, 3)
    daily_production_range: tuple[int, int] = (0, 2)
    daily_purchase_range: tuple[int, int] = (2, 5)
    payment_delay_probability: float = Field(0.15, ge=0, le=1)
    overdue_probability: float = Field(0.05, ge=0, le=1)
    vendor_payment_probability: float = Field(0.95, ge=0, le=1)
    overtime_probability: float = Field(0.10, ge=0, le=1)
    
    @validator('daily_invoice_range', 'daily_production_range', 'daily_purchase_range')
    def range_validation(cls, v):
        if v[0] > v[1]:
            raise ValueError('Range minimum cannot be greater than maximum')
        if v[0] < 0:
            raise ValueError('Range minimum cannot be negative')
        return v

# ===============================
# API MODELS
# ===============================

class HealthCheckResponse(BaseModel):
    status: str
    database: str
    scheduler: str
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DataSummaryResponse(BaseModel):
    total_invoices: int
    total_production_orders: int
    total_purchases: int
    total_cash_transactions: int
    total_payroll_records: int
    current_cash_balance: float
    accounts_receivable_total: float
    accounts_payable_total: float
    last_updated: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CashFlowSummary(BaseModel):
    date: date
    opening_balance: Decimal
    total_inflows: Decimal
    total_outflows: Decimal
    net_flow: Decimal
    closing_balance: Decimal
    transaction_count: int
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class ARAgingSummary(BaseModel):
    current_0_30: Decimal = Field(Decimal('0.00'))
    past_due_31_60: Decimal = Field(Decimal('0.00'))
    past_due_61_90: Decimal = Field(Decimal('0.00'))
    over_90: Decimal = Field(Decimal('0.00'))
    total_receivables: Decimal = Field(Decimal('0.00'))
    current_percentage: float = 0.0
    as_of_date: date
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class ProductionMetrics(BaseModel):
    total_orders: int
    completed_orders: int
    in_progress_orders: int
    planned_orders: int
    completion_rate: float
    average_order_value: Decimal
    total_production_value: Decimal
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ===============================
# EXPORT MODELS
# ===============================

class ExcelExportRequest(BaseModel):
    export_date: date
    include_charts: bool = True
    include_summary: bool = True
    file_format: str = Field("xlsx", regex="^(xlsx|csv)$")

class ExcelExportResponse(BaseModel):
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    sheets_created: List[str] = Field(default_factory=list)
    export_time: datetime
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ===============================
# INTEGRATION MODELS
# ===============================

class EZBIDataSync(BaseModel):
    """Model for EZBI platform data synchronization"""
    simulation_date: date
    cash_position: Decimal
    accounts_receivable: Decimal
    accounts_payable: Decimal
    revenue_current_month: Decimal
    expenses_current_month: Decimal
    production_orders_active: int
    invoice_count_current_month: int
    timestamp: datetime
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

class SlackNotification(BaseModel):
    """Model for Slack notification data"""
    channel: str = "#manufacturing-data"
    message_type: str = Field(..., regex="^(daily_summary|error|alert|startup)$")
    title: str
    data: Dict[str, Any]
    timestamp: datetime
    urgent: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ===============================
# UTILITY FUNCTIONS
# ===============================

def validate_business_rules(invoice: Invoice, customer: Customer) -> List[str]:
    """Validate business rules for invoice creation"""
    errors = []
    
    # Check credit limit
    if invoice.amount > customer.credit_limit:
        errors.append(f"Invoice amount ${invoice.amount} exceeds customer credit limit ${customer.credit_limit}")
    
    # Check payment terms consistency
    expected_due_date = invoice.date_issued + timedelta(days=customer.payment_terms)
    if invoice.due_date != expected_due_date:
        errors.append(f"Due date should be {expected_due_date} based on customer payment terms")
    
    return errors

def calculate_aging_bucket(days_outstanding: int) -> AgingBucket:
    """Calculate AR aging bucket based on days outstanding"""
    if days_outstanding <= 30:
        return AgingBucket.CURRENT
    elif days_outstanding <= 60:
        return AgingBucket.THIRTY_SIXTY
    elif days_outstanding <= 90:
        return AgingBucket.SIXTY_NINETY
    else:
        return AgingBucket.OVER_NINETY

def format_currency(amount: Union[Decimal, float]) -> str:
    """Format currency for display"""
    return f"${float(amount):,.2f}"

def calculate_working_days(start_date: date, end_date: date) -> int:
    """Calculate working days between two dates (excluding weekends)"""
    days = 0
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
            days += 1
        current_date += timedelta(days=1)
    
    return days

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class SimulationError(Exception):
    """Custom exception for simulation operations"""
    pass

class ExportError(Exception):
    """Custom exception for export operations"""
    pass

class IntegrationError(Exception):
    """Custom exception for integration operations"""
    pass