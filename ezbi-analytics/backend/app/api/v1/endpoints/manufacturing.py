"""
Secure Manufacturing Analytics API Endpoints
Production-ready endpoints with JWT authentication, role-based access control, and comprehensive security
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
from pydantic import BaseModel, Field

from app.core.database import get_async_session
from app.core.security import get_current_user, RateLimiter
from app.core.rbac import (
    rbac_manager, 
    check_manufacturing_access,
    check_admin_access,
    check_manager_access,
    check_sensitive_data_access,
    check_export_permission,
    AccessContext,
    PermissionType
)
from app.models.user import User
from app.models.manufacturing import *
from app.models.audit_log import AuditLog

logger = structlog.get_logger()
security = HTTPBearer()

router = APIRouter()

# Response Models
class CustomerResponse(BaseModel):
    customer_id: int
    company_name: str
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    payment_terms: int
    credit_limit: float
    total_invoices: int = 0
    total_revenue: float = 0.0
    avg_invoice_value: float = 0.0

class InvoiceResponse(BaseModel):
    invoice_id: int
    customer_id: int
    invoice_number: str
    date_issued: datetime
    due_date: datetime
    amount: float
    status: str
    payment_date: Optional[datetime]
    customer_name: Optional[str]

class ProductResponse(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    base_cost: float
    labor_hours: float
    material_cost: float
    total_orders: int = 0
    total_units_produced: int = 0

class ProductionOrderResponse(BaseModel):
    order_id: int
    order_number: str
    product_id: int
    product_name: str
    customer_id: int
    customer_name: str
    start_date: datetime
    completion_date: Optional[datetime]
    status: str
    units_ordered: int
    units_produced: int
    cost_of_goods_sold: Optional[float]

class KPIResponse(BaseModel):
    metric_name: str
    value: float
    unit: str
    change_percent: Optional[float] = None
    period: str = "current"

class DashboardResponse(BaseModel):
    total_customers: int
    total_revenue: float
    total_orders: int
    total_products: int
    active_employees: int
    monthly_costs: float
    key_metrics: List[KPIResponse]
    recent_activity: List[Dict[str, Any]]

# Request Models
class CustomerCreateRequest(BaseModel):
    company_name: str = Field(..., max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    payment_terms: int = Field(30, ge=1, le=365)
    credit_limit: float = Field(50000.0, ge=0)

class InvoiceCreateRequest(BaseModel):
    customer_id: int
    invoice_number: str = Field(..., max_length=50)
    date_issued: datetime
    due_date: datetime
    amount: float = Field(..., gt=0)
    status: str = Field("Open", regex="^(Open|Paid|Overdue|Partial)$")

class ProductCreateRequest(BaseModel):
    product_code: str = Field(..., max_length=50)
    product_name: str = Field(..., max_length=255)
    base_cost: float = Field(..., gt=0)
    labor_hours: float = Field(..., gt=0)
    material_cost: float = Field(..., gt=0)

class ProductionOrderCreateRequest(BaseModel):
    order_number: str = Field(..., max_length=50)
    product_id: int
    customer_id: int
    start_date: datetime
    expected_completion: datetime
    units_ordered: int = Field(..., gt=0)
    status: str = Field("Planned", regex="^(Planned|In Progress|Completed|On Hold)$")

# Utility Functions
async def log_api_access(request: Request, user: User, endpoint: str, action: str, db: AsyncSession):
    """Log API access for audit purposes"""
    try:
        audit_log = AuditLog.create_log(
            action=f"manufacturing_{action}",
            resource_type="manufacturing_api",
            resource_id=endpoint,
            description=f"User {user.email} accessed {endpoint}",
            user_id=user.id,
            company_id=user.company_id,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )
        db.add(audit_log)
        await db.commit()
    except Exception as e:
        logger.error("Failed to log API access", error=str(e))

async def check_rate_limit(user: User, request: Request):
    """Check rate limit for user"""
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"manufacturing_api:{user.id}:{client_ip}"
    
    # Different limits based on user role
    user_roles = [role.name for role in user.roles]
    if "admin" in user_roles:
        limit = 1000
    elif "manager" in user_roles:
        limit = 500
    else:
        limit = 200
    
    if not RateLimiter.check_rate_limit(rate_limit_key, limit, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"}
        )

# ===================
# SALES ENDPOINTS
# ===================

@router.get("/sales/customers", response_model=List[CustomerResponse])
async def get_customers(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, max_length=255),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get customers with analytics - requires sales_read permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "sales", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for sales data"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/sales/customers", "read", db)
    
    # Build query
    query = select(Customer)
    
    # Apply search filter
    if search:
        query = query.where(
            or_(
                Customer.company_name.ilike(f"%{search}%"),
                Customer.contact_name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%")
            )
        )
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    customers = result.scalars().all()
    
    # Get invoice summaries for each customer
    customer_responses = []
    for customer in customers:
        # Get invoice statistics
        invoice_stats = await db.execute(
            select(
                func.count(Invoice.invoice_id).label("total_invoices"),
                func.coalesce(func.sum(Invoice.amount), 0).label("total_revenue"),
                func.coalesce(func.avg(Invoice.amount), 0).label("avg_invoice_value")
            ).where(Invoice.customer_id == customer.customer_id)
        )
        stats = invoice_stats.first()
        
        customer_responses.append(CustomerResponse(
            customer_id=customer.customer_id,
            company_name=customer.company_name,
            contact_name=customer.contact_name,
            email=customer.email,
            phone=customer.phone,
            address=customer.address,
            payment_terms=customer.payment_terms,
            credit_limit=float(customer.credit_limit),
            total_invoices=stats.total_invoices,
            total_revenue=float(stats.total_revenue),
            avg_invoice_value=float(stats.avg_invoice_value)
        ))
    
    return customer_responses

@router.post("/sales/customers", response_model=CustomerResponse)
async def create_customer(
    request: Request,
    customer_data: CustomerCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create new customer - requires sales_write permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "sales", "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create customers"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Check if customer already exists
    existing = await db.execute(
        select(Customer).where(
            or_(
                Customer.company_name == customer_data.company_name,
                Customer.email == customer_data.email
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this name or email already exists"
        )
    
    # Create customer
    customer = Customer(
        company_name=customer_data.company_name,
        contact_name=customer_data.contact_name,
        email=customer_data.email,
        phone=customer_data.phone,
        address=customer_data.address,
        payment_terms=customer_data.payment_terms,
        credit_limit=customer_data.credit_limit
    )
    
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    
    # Log action
    await log_api_access(request, current_user, "/sales/customers", "create", db)
    
    return CustomerResponse(
        customer_id=customer.customer_id,
        company_name=customer.company_name,
        contact_name=customer.contact_name,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        payment_terms=customer.payment_terms,
        credit_limit=float(customer.credit_limit),
        total_invoices=0,
        total_revenue=0.0,
        avg_invoice_value=0.0
    )

@router.get("/sales/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, regex="^(Open|Paid|Overdue|Partial)$"),
    customer_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get invoices with customer details - requires sales_read permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "sales", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for sales data"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/sales/invoices", "read", db)
    
    # Build query
    query = select(Invoice, Customer.company_name).join(Customer)
    
    # Apply filters
    if status_filter:
        query = query.where(Invoice.status == status_filter)
    
    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)
    
    # Apply pagination
    query = query.offset(offset).limit(limit).order_by(Invoice.date_issued.desc())
    
    # Execute query
    result = await db.execute(query)
    invoices_data = result.all()
    
    # Format response
    invoices = []
    for invoice, customer_name in invoices_data:
        invoices.append(InvoiceResponse(
            invoice_id=invoice.invoice_id,
            customer_id=invoice.customer_id,
            invoice_number=invoice.invoice_number,
            date_issued=invoice.date_issued,
            due_date=invoice.due_date,
            amount=float(invoice.amount),
            status=invoice.status,
            payment_date=invoice.payment_date,
            customer_name=customer_name
        ))
    
    return invoices

@router.post("/sales/invoices", response_model=InvoiceResponse)
async def create_invoice(
    request: Request,
    invoice_data: InvoiceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create new invoice - requires sales_write permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "sales", "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create invoices"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Validate customer exists
    customer = await db.execute(
        select(Customer).where(Customer.customer_id == invoice_data.customer_id)
    )
    if not customer.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer not found"
        )
    
    # Check if invoice number already exists
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice number already exists"
        )
    
    # Create invoice
    invoice = Invoice(
        customer_id=invoice_data.customer_id,
        invoice_number=invoice_data.invoice_number,
        date_issued=invoice_data.date_issued,
        due_date=invoice_data.due_date,
        amount=invoice_data.amount,
        status=invoice_data.status
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    # Log action
    await log_api_access(request, current_user, "/sales/invoices", "create", db)
    
    return InvoiceResponse(
        invoice_id=invoice.invoice_id,
        customer_id=invoice.customer_id,
        invoice_number=invoice.invoice_number,
        date_issued=invoice.date_issued,
        due_date=invoice.due_date,
        amount=float(invoice.amount),
        status=invoice.status,
        payment_date=invoice.payment_date,
        customer_name=None
    )

@router.get("/sales/kpis", response_model=Dict[str, Any])
async def get_sales_kpis(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get sales KPIs and analytics - requires sales_read permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "sales", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for sales data"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/sales/kpis", "read", db)
    
    # Total sales metrics
    totals = await db.execute(
        select(
            func.count(Invoice.invoice_id).label("total_invoices"),
            func.coalesce(func.sum(Invoice.amount), 0).label("total_revenue"),
            func.coalesce(func.avg(Invoice.amount), 0).label("avg_invoice_value"),
            func.count(func.distinct(Invoice.customer_id)).label("active_customers")
        )
    )
    totals_data = totals.first()
    
    # Status breakdown
    status_breakdown = await db.execute(
        select(
            Invoice.status,
            func.count(Invoice.invoice_id).label("count"),
            func.coalesce(func.sum(Invoice.amount), 0).label("total_amount")
        ).group_by(Invoice.status)
    )
    status_data = [
        {
            "status": row.status,
            "count": row.count,
            "total_amount": float(row.total_amount)
        }
        for row in status_breakdown.all()
    ]
    
    # Monthly revenue trend
    monthly_trend = await db.execute(
        text("""
            SELECT 
                DATE_TRUNC('month', date_issued) as month,
                SUM(amount) as revenue,
                COUNT(*) as invoice_count
            FROM sales.invoices
            WHERE date_issued >= NOW() - INTERVAL '12 months'
            GROUP BY month
            ORDER BY month
        """)
    )
    monthly_data = [
        {
            "month": row.month.strftime("%Y-%m"),
            "revenue": float(row.revenue),
            "invoice_count": row.invoice_count
        }
        for row in monthly_trend.all()
    ]
    
    # Top customers
    top_customers = await db.execute(
        select(
            Customer.company_name,
            func.coalesce(func.sum(Invoice.amount), 0).label("total_revenue"),
            func.count(Invoice.invoice_id).label("invoice_count")
        )
        .join(Invoice, Customer.customer_id == Invoice.customer_id)
        .group_by(Customer.customer_id, Customer.company_name)
        .order_by(func.sum(Invoice.amount).desc())
        .limit(10)
    )
    top_customers_data = [
        {
            "company_name": row.company_name,
            "total_revenue": float(row.total_revenue),
            "invoice_count": row.invoice_count
        }
        for row in top_customers.all()
    ]
    
    return {
        "totals": {
            "total_invoices": totals_data.total_invoices,
            "total_revenue": float(totals_data.total_revenue),
            "avg_invoice_value": float(totals_data.avg_invoice_value),
            "active_customers": totals_data.active_customers
        },
        "status_breakdown": status_data,
        "monthly_trend": monthly_data,
        "top_customers": top_customers_data
    }

# ===================
# OPERATIONS ENDPOINTS
# ===================

@router.get("/operations/products", response_model=List[ProductResponse])
async def get_products(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, max_length=255),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get products with production statistics - requires operations_read permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "operations", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for operations data"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/operations/products", "read", db)
    
    # Build query
    query = select(Product)
    
    # Apply search filter
    if search:
        query = query.where(
            or_(
                Product.product_name.ilike(f"%{search}%"),
                Product.product_code.ilike(f"%{search}%")
            )
        )
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()
    
    # Get production statistics for each product
    product_responses = []
    for product in products:
        # Get production statistics
        production_stats = await db.execute(
            select(
                func.count(ProductionOrder.order_id).label("total_orders"),
                func.coalesce(func.sum(ProductionOrder.units_produced), 0).label("total_units_produced")
            ).where(ProductionOrder.product_id == product.product_id)
        )
        stats = production_stats.first()
        
        product_responses.append(ProductResponse(
            product_id=product.product_id,
            product_code=product.product_code,
            product_name=product.product_name,
            base_cost=float(product.base_cost),
            labor_hours=float(product.labor_hours),
            material_cost=float(product.material_cost),
            total_orders=stats.total_orders,
            total_units_produced=stats.total_units_produced
        ))
    
    return product_responses

@router.post("/operations/products", response_model=ProductResponse)
async def create_product(
    request: Request,
    product_data: ProductCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create new product - requires operations_write permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "operations", "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create products"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Check if product code already exists
    existing = await db.execute(
        select(Product).where(Product.product_code == product_data.product_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product code already exists"
        )
    
    # Create product
    product = Product(
        product_code=product_data.product_code,
        product_name=product_data.product_name,
        base_cost=product_data.base_cost,
        labor_hours=product_data.labor_hours,
        material_cost=product_data.material_cost
    )
    
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    # Log action
    await log_api_access(request, current_user, "/operations/products", "create", db)
    
    return ProductResponse(
        product_id=product.product_id,
        product_code=product.product_code,
        product_name=product.product_name,
        base_cost=float(product.base_cost),
        labor_hours=float(product.labor_hours),
        material_cost=float(product.material_cost),
        total_orders=0,
        total_units_produced=0
    )

@router.get("/operations/kpis", response_model=Dict[str, Any])
async def get_operations_kpis(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get operations KPIs and analytics - requires operations_read permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "operations", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for operations data"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/operations/kpis", "read", db)
    
    # Production efficiency metrics
    efficiency = await db.execute(
        text("""
            SELECT 
                COUNT(order_id) as total_orders,
                COALESCE(SUM(units_ordered), 0) as total_units_ordered,
                COALESCE(SUM(units_produced), 0) as total_units_produced,
                CASE 
                    WHEN SUM(units_ordered) > 0 
                    THEN (SUM(units_produced) * 100.0 / SUM(units_ordered))
                    ELSE 0
                END as avg_efficiency
            FROM operations.production_orders
        """)
    )
    efficiency_data = efficiency.first()
    
    # Status breakdown
    status_breakdown = await db.execute(
        text("""
            SELECT 
                status,
                COUNT(order_id) as order_count,
                COALESCE(SUM(units_ordered), 0) as units_ordered,
                COALESCE(SUM(units_produced), 0) as units_produced
            FROM operations.production_orders
            GROUP BY status
            ORDER BY order_count DESC
        """)
    )
    status_data = [
        {
            "status": row.status,
            "order_count": row.order_count,
            "units_ordered": row.units_ordered,
            "units_produced": row.units_produced
        }
        for row in status_breakdown.all()
    ]
    
    # Top products by production volume
    top_products = await db.execute(
        text("""
            SELECT 
                p.product_name,
                COALESCE(SUM(po.units_produced), 0) as total_produced,
                COUNT(po.order_id) as order_count
            FROM operations.products p
            LEFT JOIN operations.production_orders po ON p.product_id = po.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY total_produced DESC
            LIMIT 10
        """)
    )
    top_products_data = [
        {
            "product_name": row.product_name,
            "total_produced": row.total_produced,
            "order_count": row.order_count
        }
        for row in top_products.all()
    ]
    
    return {
        "efficiency": {
            "total_orders": efficiency_data.total_orders,
            "total_units_ordered": efficiency_data.total_units_ordered,
            "total_units_produced": efficiency_data.total_units_produced,
            "avg_efficiency": float(efficiency_data.avg_efficiency) if efficiency_data.avg_efficiency else 0.0
        },
        "status_breakdown": status_data,
        "top_products": top_products_data
    }

# ===================
# FINANCE ENDPOINTS
# ===================

@router.get("/finance/kpis", response_model=Dict[str, Any])
async def get_finance_kpis(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get finance KPIs from manufacturing tables - requires finance_read permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "finance", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for finance data"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/finance/kpis", "read", db)
    
    # Get finance KPIs from manufacturing tables
    finance_kpis = await db.execute(
        text("""
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'Inflow' THEN amount ELSE -amount END), 0) as total_cash_flow,
                COALESCE(SUM(principal_amount), 0) as total_debt,
                COALESCE(AVG(interest_rate), 0.05) as interest_rate,
                COALESCE(SUM(monthly_payment_amount), 0) as monthly_payments,
                COUNT(DISTINCT account_number) as debt_accounts_count
            FROM finance.debt_accounts
        """)
    )
    kpis = finance_kpis.first()
    
    return {
        "total_cash_flow": float(kpis.total_cash_flow) if kpis.total_cash_flow else 0.0,
        "total_debt": float(kpis.total_debt) if kpis.total_debt else 0.0,
        "interest_rate": float(kpis.interest_rate) if kpis.interest_rate else 0.05,
        "monthly_payments": float(kpis.monthly_payments) if kpis.monthly_payments else 0.0,
        "debt_accounts_count": kpis.debt_accounts_count if kpis.debt_accounts_count else 0
    }

@router.get("/finance/cash-ledger", response_model=Dict[str, Any])
async def get_cash_ledger(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get cash ledger transactions - requires finance_read permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "finance", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for finance data"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/finance/cash-ledger", "read", db)
    
    # Get recent cash ledger transactions
    transactions = await db.execute(
        text("""
            SELECT transaction_number, transaction_type, amount, 
                   counterparty, date_recorded
            FROM finance.cash_ledger
            ORDER BY date_recorded DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )
    
    data = [
        {
            "transaction_number": row.transaction_number,
            "transaction_type": row.transaction_type,
            "amount": float(row.amount),
            "counterparty": row.counterparty,
            "date_recorded": row.date_recorded.isoformat()
        }
        for row in transactions.all()
    ]
    
    return {"data": data, "count": len(data)}

@router.get("/finance/debt-accounts", response_model=Dict[str, Any])
async def get_debt_accounts(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get debt accounts summary - requires finance_read permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "finance", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for finance data"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/finance/debt-accounts", "read", db)
    
    # Get debt accounts
    accounts = await db.execute(
        text("""
            SELECT account_number, institution_name, principal_amount,
                   outstanding_balance, interest_rate, monthly_payment_amount,
                   loan_start_date, loan_end_date
            FROM finance.debt_accounts
            ORDER BY outstanding_balance DESC
        """)
    )
    
    data = [
        {
            "account_number": row.account_number,
            "institution_name": row.institution_name,
            "principal_amount": float(row.principal_amount),
            "outstanding_balance": float(row.outstanding_balance),
            "interest_rate": float(row.interest_rate),
            "monthly_payment_amount": float(row.monthly_payment_amount),
            "loan_start_date": row.loan_start_date.isoformat(),
            "loan_end_date": row.loan_end_date.isoformat() if row.loan_end_date else None
        }
        for row in accounts.all()
    ]
    
    return {"data": data, "count": len(data)}

# ===================
# ACCOUNTING ENDPOINTS
# ===================

@router.get("/accounting/kpis", response_model=Dict[str, Any])
async def get_accounting_kpis(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get accounting KPIs from manufacturing tables - requires accounting_read permission"""
    
    # Check permission
    if not await check_manufacturing_access(current_user, "accounting", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for accounting data"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/accounting/kpis", "read", db)
    
    # Get AR aging data
    ar_aging = await db.execute(
        text("""
            SELECT 
                CASE 
                    WHEN days_outstanding <= 30 THEN '0-30 days'
                    WHEN days_outstanding <= 60 THEN '31-60 days'
                    WHEN days_outstanding <= 90 THEN '61-90 days'
                    ELSE '90+ days'
                END as aging_bucket,
                COUNT(*) as invoice_count,
                SUM(outstanding_amount) as total_amount
            FROM accounting.accounts_receivable
            GROUP BY aging_bucket
            ORDER BY aging_bucket
        """)
    )
    
    ar_data = [
        {
            "aging_bucket": row.aging_bucket,
            "invoice_count": row.invoice_count,
            "total_amount": float(row.total_amount)
        }
        for row in ar_aging.all()
    ]
    
    # Get AP summary
    ap_summary = await db.execute(
        text("""
            SELECT 
                COUNT(*) as total_payables,
                SUM(amount_due) as total_amount,
                AVG(days_until_due) as avg_days_until_due
            FROM accounting.accounts_payable
        """)
    )
    ap_data = ap_summary.first()
    
    return {
        "ar_aging": ar_data,
        "ap_summary": {
            "total_payables": ap_data.total_payables if ap_data else 0,
            "total_amount": float(ap_data.total_amount) if ap_data and ap_data.total_amount else 0.0,
            "avg_days_until_due": float(ap_data.avg_days_until_due) if ap_data and ap_data.avg_days_until_due else 0.0
        }
    }

# ===================
# DASHBOARD ENDPOINTS
# ===================

@router.get("/dashboard/overview", response_model=DashboardResponse)
async def get_dashboard_overview(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get comprehensive dashboard overview - requires analyst_access permission"""
    
    # Check permission (analysts and above can access dashboard)
    context = AccessContext(user=current_user, resource_type="dashboard")
    if not await rbac_manager.check_permission(context, PermissionType.ANALYST_ACCESS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for dashboard access"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Log access
    await log_api_access(request, current_user, "/dashboard/overview", "read", db)
    
    # Get overview metrics
    overview = await db.execute(
        text("""
            SELECT 
                (SELECT COUNT(*) FROM sales.customers) as total_customers,
                (SELECT COALESCE(SUM(amount), 0) FROM sales.invoices) as total_revenue,
                (SELECT COUNT(*) FROM operations.production_orders) as total_orders,
                (SELECT COUNT(*) FROM operations.products) as total_products,
                (SELECT COUNT(*) FROM hr.employees WHERE status = 'Active') as active_employees,
                (SELECT COALESCE(SUM(amount), 0) FROM expenses.fixed_costs) as monthly_costs
        """)
    )
    overview_data = overview.first()
    
    # Key metrics
    key_metrics = [
        KPIResponse(
            metric_name="Total Revenue",
            value=float(overview_data.total_revenue),
            unit="EUR",
            period="all_time"
        ),
        KPIResponse(
            metric_name="Active Customers",
            value=overview_data.total_customers,
            unit="count",
            period="current"
        ),
        KPIResponse(
            metric_name="Production Orders",
            value=overview_data.total_orders,
            unit="count",
            period="current"
        ),
        KPIResponse(
            metric_name="Monthly Fixed Costs",
            value=float(overview_data.monthly_costs),
            unit="EUR",
            period="monthly"
        ),
    ]
    
    # Recent activity (last 10 items)
    recent_invoices = await db.execute(
        text("""
            SELECT 'Invoice' as type, invoice_number as reference, 
                   amount, date_issued as date
            FROM sales.invoices
            ORDER BY date_issued DESC
            LIMIT 5
        """)
    )
    
    recent_orders = await db.execute(
        text("""
            SELECT 'Production Order' as type, order_number as reference, 
                   COALESCE(cost_of_goods_sold, 0) as amount, start_date as date
            FROM operations.production_orders
            ORDER BY start_date DESC
            LIMIT 5
        """)
    )
    
    recent_activity = []
    for row in recent_invoices.all():
        recent_activity.append({
            "type": row.type,
            "reference": row.reference,
            "amount": float(row.amount),
            "date": row.date.isoformat()
        })
    
    for row in recent_orders.all():
        recent_activity.append({
            "type": row.type,
            "reference": row.reference,
            "amount": float(row.amount),
            "date": row.date.isoformat()
        })
    
    # Sort by date
    recent_activity.sort(key=lambda x: x["date"], reverse=True)
    
    return DashboardResponse(
        total_customers=overview_data.total_customers,
        total_revenue=float(overview_data.total_revenue),
        total_orders=overview_data.total_orders,
        total_products=overview_data.total_products,
        active_employees=overview_data.active_employees,
        monthly_costs=float(overview_data.monthly_costs),
        key_metrics=key_metrics,
        recent_activity=recent_activity[:10]
    )

# ===================
# ADMIN ENDPOINTS
# ===================

@router.get("/admin/audit-logs")
async def get_audit_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action_filter: Optional[str] = Query(None, max_length=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get audit logs - requires admin_access permission"""
    
    # Check admin permission
    if not await check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Rate limiting
    await check_rate_limit(current_user, request)
    
    # Build query
    query = select(AuditLog)
    
    # Apply filters
    if action_filter:
        query = query.where(AuditLog.action.ilike(f"%{action_filter}%"))
    
    # Apply pagination
    query = query.offset(offset).limit(limit).order_by(AuditLog.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    audit_logs = result.scalars().all()
    
    # Format response
    logs = []
    for log in audit_logs:
        logs.append({
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "description": log.description,
            "user_id": log.user_id,
            "company_id": log.company_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "additional_data": log.additional_data,
            "created_at": log.created_at.isoformat()
        })
    
    return {"audit_logs": logs, "total": len(logs)}

@router.get("/system/health")
async def get_system_health(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get system health status - requires admin_access permission"""
    
    # Check admin permission
    if not await check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if database_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": database_status,
            "authentication": "healthy",
            "api": "healthy"
        },
        "user_info": {
            "user_id": current_user.id,
            "email": current_user.email,
            "roles": [role.name for role in current_user.roles]
        }
    }