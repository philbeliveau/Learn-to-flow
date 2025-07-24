from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, JSON, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
import enum

from app.core.database import Base

class TransactionType(enum.Enum):
    """Transaction type classification."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"

class TransactionCategory(enum.Enum):
    """Transaction category for manufacturing businesses."""
    # Income categories
    SALES_REVENUE = "sales_revenue"
    SERVICE_REVENUE = "service_revenue"
    INVESTMENT_INCOME = "investment_income"
    OTHER_INCOME = "other_income"
    
    # Expense categories
    RAW_MATERIALS = "raw_materials"
    LABOR_COSTS = "labor_costs"
    MANUFACTURING_OVERHEAD = "manufacturing_overhead"
    UTILITIES = "utilities"
    RENT = "rent"
    INSURANCE = "insurance"
    MARKETING = "marketing"
    ADMINISTRATIVE = "administrative"
    TAXES = "taxes"
    LOAN_PAYMENTS = "loan_payments"
    EQUIPMENT_PURCHASE = "equipment_purchase"
    MAINTENANCE = "maintenance"
    OTHER_EXPENSES = "other_expenses"

class PaymentMethod(enum.Enum):
    """Payment method types."""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CHECK = "check"
    DIGITAL_PAYMENT = "digital_payment"
    CRYPTO = "crypto"
    OTHER = "other"

class DataSource(enum.Enum):
    """Data source types."""
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    EXCEL_IMPORT = "excel_import"
    BANK_API = "bank_api"
    ERP_SYNC = "erp_sync"
    API_INTEGRATION = "api_integration"
    AUTOMATIC = "automatic"

class FinancialData(Base):
    """Financial transaction and cash flow data."""
    
    __tablename__ = "financial_data"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Transaction identification
    transaction_id = Column(String(100), nullable=True, index=True)  # External transaction ID
    reference_number = Column(String(50), nullable=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50), nullable=True)
    
    # Financial amounts
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    
    # Description and notes
    description = Column(String(500), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Date information
    transaction_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=True)
    
    # Payment information
    payment_method = Column(String(20), nullable=True)
    payment_status = Column(String(20), default="pending")
    
    # Counterparty information
    counterparty_name = Column(String(200), nullable=True)
    counterparty_account = Column(String(50), nullable=True)
    
    # Classification and tagging
    tags = Column(JSON, nullable=True)
    project_id = Column(String(50), nullable=True)
    department = Column(String(50), nullable=True)
    
    # Manufacturing specific fields
    production_batch = Column(String(50), nullable=True)
    product_line = Column(String(100), nullable=True)
    manufacturing_stage = Column(String(50), nullable=True)
    
    # Accounting information
    account_code = Column(String(20), nullable=True)
    tax_rate = Column(Numeric(5, 2), nullable=True)
    tax_amount = Column(Numeric(15, 2), nullable=True)
    
    # Data source and validation
    data_source = Column(String(20), default=DataSource.MANUAL.value)
    is_validated = Column(Boolean, default=False)
    validation_notes = Column(Text, nullable=True)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciliation_date = Column(DateTime, nullable=True)
    reconciliation_notes = Column(Text, nullable=True)
    
    # Prediction and forecasting
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00-1.00
    
    # Audit and tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="financial_data")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Hybrid properties
    @hybrid_property
    def is_income(self) -> bool:
        """Check if transaction is income."""
        return self.transaction_type == TransactionType.INCOME.value
    
    @hybrid_property
    def is_expense(self) -> bool:
        """Check if transaction is expense."""
        return self.transaction_type == TransactionType.EXPENSE.value
    
    @hybrid_property
    def net_amount(self) -> Decimal:
        """Get net amount (positive for income, negative for expense)."""
        if self.is_income:
            return self.amount
        else:
            return -self.amount
    
    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if payment is overdue."""
        if self.due_date and self.payment_status != "paid":
            return date.today() > self.due_date
        return False
    
    @hybrid_property
    def days_until_due(self) -> Optional[int]:
        """Get days until due date."""
        if self.due_date:
            delta = self.due_date - date.today()
            return delta.days
        return None
    
    @hybrid_property
    def is_manufacturing_related(self) -> bool:
        """Check if transaction is manufacturing-related."""
        manufacturing_categories = [
            TransactionCategory.RAW_MATERIALS.value,
            TransactionCategory.LABOR_COSTS.value,
            TransactionCategory.MANUFACTURING_OVERHEAD.value,
            TransactionCategory.EQUIPMENT_PURCHASE.value,
            TransactionCategory.MAINTENANCE.value,
        ]
        return self.category in manufacturing_categories
    
    # Methods
    def validate_transaction(self) -> Dict[str, Any]:
        """Validate transaction data and return validation results."""
        errors = []
        warnings = []
        
        # Required field validation
        if not self.amount or self.amount <= 0:
            errors.append("Amount must be positive")
        
        if not self.description or len(self.description.strip()) < 5:
            errors.append("Description must be at least 5 characters")
        
        if not self.transaction_date:
            errors.append("Transaction date is required")
        
        # Business rule validation
        if self.transaction_date > date.today():
            warnings.append("Transaction date is in the future")
        
        if self.amount > 1000000:  # 1M EUR
            warnings.append("Large transaction amount - please verify")
        
        # Category validation
        valid_categories = [cat.value for cat in TransactionCategory]
        if self.category not in valid_categories:
            errors.append(f"Invalid category: {self.category}")
        
        # Currency validation
        if self.currency not in ["EUR", "USD", "GBP"]:
            warnings.append(f"Unusual currency: {self.currency}")
        
        # Due date validation
        if self.due_date and self.due_date < self.transaction_date:
            errors.append("Due date cannot be before transaction date")
        
        is_valid = len(errors) == 0
        if is_valid:
            self.is_validated = True
            self.validation_notes = f"Validated on {datetime.utcnow().isoformat()}"
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "validation_timestamp": datetime.utcnow().isoformat(),
        }
    
    def categorize_automatically(self) -> str:
        """Automatically categorize transaction based on description and counterparty."""
        description_lower = self.description.lower()
        counterparty_lower = (self.counterparty_name or "").lower()
        
        # Keywords for automatic categorization
        category_keywords = {
            TransactionCategory.RAW_MATERIALS.value: [
                "raw material", "materials", "steel", "aluminum", "plastic", "components",
                "supplier", "inventory", "stock"
            ],
            TransactionCategory.LABOR_COSTS.value: [
                "salary", "wage", "payroll", "overtime", "bonus", "employee",
                "social security", "benefits"
            ],
            TransactionCategory.UTILITIES.value: [
                "electricity", "gas", "water", "utility", "power", "energy",
                "edf", "engie", "total"
            ],
            TransactionCategory.RENT.value: [
                "rent", "lease", "location", "loyer", "bail"
            ],
            TransactionCategory.INSURANCE.value: [
                "insurance", "assurance", "premium", "policy"
            ],
            TransactionCategory.MAINTENANCE.value: [
                "maintenance", "repair", "service", "fix", "replacement"
            ],
            TransactionCategory.SALES_REVENUE.value: [
                "sale", "revenue", "invoice", "payment received", "customer"
            ],
        }
        
        # Check description and counterparty against keywords
        for category, keywords in category_keywords.items():
            if any(keyword in description_lower or keyword in counterparty_lower 
                   for keyword in keywords):
                return category
        
        # Default categorization based on transaction type
        if self.transaction_type == TransactionType.INCOME.value:
            return TransactionCategory.SALES_REVENUE.value
        else:
            return TransactionCategory.OTHER_EXPENSES.value
    
    def set_recurrence_pattern(self, pattern_type: str, interval: int = 1, 
                             end_date: Optional[date] = None) -> None:
        """Set recurrence pattern for regular transactions."""
        self.is_recurring = True
        self.recurrence_pattern = {
            "type": pattern_type,  # daily, weekly, monthly, quarterly, yearly
            "interval": interval,
            "next_date": self.transaction_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else None,
            "created_at": datetime.utcnow().isoformat(),
        }
    
    def get_next_recurrence_date(self) -> Optional[date]:
        """Get next occurrence date for recurring transactions."""
        if not self.is_recurring or not self.recurrence_pattern:
            return None
        
        from dateutil.relativedelta import relativedelta
        
        pattern = self.recurrence_pattern
        last_date = datetime.fromisoformat(pattern["next_date"]).date()
        interval = pattern["interval"]
        
        if pattern["type"] == "daily":
            return last_date + relativedelta(days=interval)
        elif pattern["type"] == "weekly":
            return last_date + relativedelta(weeks=interval)
        elif pattern["type"] == "monthly":
            return last_date + relativedelta(months=interval)
        elif pattern["type"] == "quarterly":
            return last_date + relativedelta(months=3 * interval)
        elif pattern["type"] == "yearly":
            return last_date + relativedelta(years=interval)
        
        return None
    
    def calculate_tax_amount(self) -> Decimal:
        """Calculate tax amount based on tax rate."""
        if self.tax_rate:
            return self.amount * (self.tax_rate / 100)
        return Decimal("0.00")
    
    def get_manufacturing_metrics(self) -> Dict[str, Any]:
        """Get manufacturing-specific metrics."""
        return {
            "is_manufacturing_related": self.is_manufacturing_related,
            "production_batch": self.production_batch,
            "product_line": self.product_line,
            "manufacturing_stage": self.manufacturing_stage,
            "cost_per_unit": None,  # Would need additional data
            "efficiency_score": None,  # Would need additional data
        }
    
    def reconcile(self, notes: str = "") -> None:
        """Mark transaction as reconciled."""
        self.is_reconciled = True
        self.reconciliation_date = datetime.utcnow()
        self.reconciliation_notes = notes
    
    def add_tags(self, tags: List[str]) -> None:
        """Add tags to transaction."""
        current_tags = self.tags or []
        new_tags = list(set(current_tags + tags))
        self.tags = new_tags
    
    def remove_tags(self, tags: List[str]) -> None:
        """Remove tags from transaction."""
        if self.tags:
            self.tags = [tag for tag in self.tags if tag not in tags]
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        result = {
            "id": self.id,
            "company_id": self.company_id,
            "transaction_id": self.transaction_id,
            "reference_number": self.reference_number,
            "transaction_type": self.transaction_type,
            "category": self.category,
            "subcategory": self.subcategory,
            "amount": float(self.amount),
            "currency": self.currency,
            "net_amount": float(self.net_amount),
            "description": self.description,
            "notes": self.notes,
            "transaction_date": self.transaction_date.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "counterparty_name": self.counterparty_name,
            "tags": self.tags,
            "project_id": self.project_id,
            "department": self.department,
            "account_code": self.account_code,
            "tax_rate": float(self.tax_rate) if self.tax_rate else None,
            "tax_amount": float(self.tax_amount) if self.tax_amount else None,
            "data_source": self.data_source,
            "is_validated": self.is_validated,
            "is_reconciled": self.is_reconciled,
            "is_recurring": self.is_recurring,
            "is_overdue": self.is_overdue,
            "days_until_due": self.days_until_due,
            "manufacturing_metrics": self.get_manufacturing_metrics(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_sensitive:
            result.update({
                "counterparty_account": self.counterparty_account,
                "validation_notes": self.validation_notes,
                "reconciliation_notes": self.reconciliation_notes,
                "recurrence_pattern": self.recurrence_pattern,
                "confidence_score": float(self.confidence_score) if self.confidence_score else None,
            })
        
        return result
    
    def __repr__(self):
        return f"<FinancialData {self.transaction_type} {self.amount} {self.currency}>"

class CashFlowProjection(Base):
    """Cash flow projections and forecasts."""
    
    __tablename__ = "cash_flow_projections"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Projection details
    projection_date = Column(Date, nullable=False, index=True)
    projection_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Projected amounts
    projected_income = Column(Numeric(15, 2), nullable=False, default=0)
    projected_expenses = Column(Numeric(15, 2), nullable=False, default=0)
    projected_net_flow = Column(Numeric(15, 2), nullable=False, default=0)
    
    # Confidence and accuracy
    confidence_score = Column(Numeric(3, 2), nullable=False, default=0.5)
    accuracy_score = Column(Numeric(3, 2), nullable=True)  # Calculated after actual data
    
    # Model information
    model_used = Column(String(50), nullable=True)
    model_version = Column(String(20), nullable=True)
    
    # Seasonality and trends
    seasonal_factor = Column(Numeric(5, 2), nullable=True)
    trend_factor = Column(Numeric(5, 2), nullable=True)
    
    # Business context
    business_context = Column(JSON, nullable=True)
    assumptions = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company")
    
    @property
    def is_accurate(self) -> bool:
        """Check if projection was accurate (within 10% of actual)."""
        if self.accuracy_score:
            return self.accuracy_score >= 0.9
        return False
    
    def calculate_accuracy(self, actual_income: Decimal, actual_expenses: Decimal) -> None:
        """Calculate accuracy score based on actual values."""
        actual_net_flow = actual_income - actual_expenses
        
        if actual_net_flow != 0:
            error_rate = abs(self.projected_net_flow - actual_net_flow) / abs(actual_net_flow)
            self.accuracy_score = max(0, 1 - error_rate)
        else:
            self.accuracy_score = 1.0 if self.projected_net_flow == 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert projection to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "projection_date": self.projection_date.isoformat(),
            "projection_type": self.projection_type,
            "projected_income": float(self.projected_income),
            "projected_expenses": float(self.projected_expenses),
            "projected_net_flow": float(self.projected_net_flow),
            "confidence_score": float(self.confidence_score),
            "accuracy_score": float(self.accuracy_score) if self.accuracy_score else None,
            "model_used": self.model_used,
            "model_version": self.model_version,
            "seasonal_factor": float(self.seasonal_factor) if self.seasonal_factor else None,
            "trend_factor": float(self.trend_factor) if self.trend_factor else None,
            "business_context": self.business_context,
            "assumptions": self.assumptions,
            "is_accurate": self.is_accurate,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<CashFlowProjection {self.projection_date} net={self.projected_net_flow}>"

class Budget(Base):
    """Budget planning and tracking."""
    
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Budget identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Budget period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Budget amounts by category
    budget_data = Column(JSON, nullable=False)  # Category-wise budget amounts
    
    # Status and approval
    status = Column(String(20), default="draft")  # draft, approved, active, completed
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Variance tracking
    variance_threshold = Column(Numeric(5, 2), default=10)  # Percentage
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    company = relationship("Company")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def calculate_variance(self, actual_data: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate variance between budget and actual amounts."""
        variances = {}
        
        for category, budgeted_amount in self.budget_data.items():
            actual_amount = actual_data.get(category, Decimal("0.00"))
            variance = actual_amount - Decimal(str(budgeted_amount))
            variance_percent = (variance / Decimal(str(budgeted_amount))) * 100 if budgeted_amount != 0 else 0
            
            variances[category] = {
                "budgeted": float(budgeted_amount),
                "actual": float(actual_amount),
                "variance": float(variance),
                "variance_percent": float(variance_percent),
                "is_over_threshold": abs(variance_percent) > self.variance_threshold,
            }
        
        return variances
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert budget to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "budget_data": self.budget_data,
            "status": self.status,
            "variance_threshold": float(self.variance_threshold),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<Budget {self.name} ({self.start_date} to {self.end_date})>"
