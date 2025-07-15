# JWT Authentication System - Production Implementation

## Overview

This document outlines the comprehensive JWT authentication system implemented for the EZBI Analytics manufacturing API. The system provides enterprise-grade security with role-based access control, MFA support, and comprehensive audit logging.

## Architecture

### Core Components

1. **JWT Token Management** (`app/core/security.py`)
   - Access tokens (30 minutes default)
   - Refresh tokens (7 days default)
   - Reset tokens (30 minutes)
   - Token blacklisting via Redis

2. **Role-Based Access Control** (`app/core/rbac.py`)
   - Hierarchical role system
   - Fine-grained permissions
   - Manufacturing-specific roles

3. **Secure Token Storage** (`app/services/token_service.py`)
   - Encrypted token storage
   - Device fingerprinting
   - Automatic token rotation

4. **Authentication Middleware** (`app/middleware/auth_middleware.py`)
   - Request authentication
   - Permission validation
   - Rate limiting
   - Audit logging

## User Roles and Permissions

### Role Hierarchy

```
Admin (Level 100)
├── Manager (Level 80)
│   ├── Analyst (Level 60)
│   ├── Sales User (Level 40)
│   ├── Accounting User (Level 40)
│   ├── Operations User (Level 40)
│   ├── Finance User (Level 40)
│   └── HR User (Level 40)
└── Viewer (Level 20)
```

### Manufacturing API Permissions

#### Sales Module
- **Read Access**: `sales_read`
  - Roles: Sales User, Manager, Admin
  - Endpoints: `/sales/customers`, `/sales/invoices`, `/sales/kpis`

- **Write Access**: `sales_write`
  - Roles: Manager, Admin
  - Endpoints: POST/PUT/DELETE operations

#### Accounting Module
- **Read Access**: `accounting_read`
  - Roles: Accounting User, Manager, Admin
  - Endpoints: `/accounting/vendors`, `/accounting/purchases`, `/accounting/accounts-receivable`

- **Write Access**: `accounting_write`
  - Roles: Manager, Admin

#### Operations Module
- **Read Access**: `operations_read`
  - Roles: Operations User, Manager, Admin
  - Endpoints: `/operations/products`, `/operations/production-orders`

- **Write Access**: `operations_write`
  - Roles: Manager, Admin

#### Finance Module (Sensitive)
- **Read Access**: `finance_read`
  - Roles: Finance User, Manager, Admin
  - Endpoints: `/finance/cash-ledger`, `/finance/debt-accounts`
  - **Additional Requirements**: MFA enabled for enterprise accounts

- **Write Access**: `finance_write`
  - Roles: Manager, Admin

#### HR Module (Sensitive)
- **Read Access**: `hr_read`
  - Roles: HR User, Manager, Admin
  - Endpoints: `/hr/employees`, `/hr/payroll`
  - **Additional Requirements**: MFA enabled for enterprise accounts

- **Write Access**: `hr_write`
  - Roles: Manager, Admin

#### Dashboard Access
- **Analyst Access**: `analyst_access`
  - Roles: Analyst, Manager, Admin
  - Endpoints: `/dashboard/overview`

#### Admin Access
- **Admin Access**: `admin_access`
  - Roles: Admin only
  - Endpoints: `/admin/audit-logs`, `/system/health`

## Authentication Flow

### 1. User Registration
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Manufacturing Corp"
}
```

### 2. User Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "SecurePassword123!",
  "remember_me": false,
  "mfa_token": "123456"  // Optional, if MFA enabled
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@company.com",
    "roles": ["sales_user"],
    "permissions": ["sales_read", "sales_write"]
  }
}
```

### 3. Token Refresh
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 4. Accessing Protected Endpoints
```http
GET /api/v1/manufacturing/sales/customers
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Multi-Factor Authentication (MFA)

### Setup MFA
```http
POST /api/v1/auth/mfa/setup
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "backup_codes": ["12345678", "87654321", ...]
}
```

### Verify MFA
```http
POST /api/v1/auth/mfa/verify
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "token": "123456"
}
```

## Security Features

### 1. Token Security
- **Encryption**: All tokens encrypted at rest using Fernet
- **Blacklisting**: Revoked tokens stored in Redis blacklist
- **Rotation**: Automatic token rotation when 80% of lifetime passed
- **Device Fingerprinting**: Tracks device characteristics for security

### 2. Rate Limiting
- **Admin**: 1000 requests/minute
- **Manager**: 500 requests/minute
- **Analyst**: 200 requests/minute
- **User**: 100 requests/minute

### 3. Input Validation
- **Sanitization**: All string inputs sanitized against XSS
- **Validation**: Pattern matching for emails, phone numbers, etc.
- **Length Limits**: Maximum field lengths enforced

### 4. Audit Logging
All API access logged with:
- User ID and email
- IP address and user agent
- Endpoint accessed
- Response status
- Duration
- Additional metadata

### 5. Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: default-src 'self'`

## Configuration

### Environment Variables
```bash
# JWT Configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
RESET_TOKEN_EXPIRE_MINUTES=30

# Security
FERNET_KEY=your-fernet-key-here
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Redis (for token storage and rate limiting)
REDIS_URL=redis://localhost:6379/0

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/db
```

## Usage Examples

### Manufacturing API Access

#### Sales Data Access
```python
import requests

# Login
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'sales@company.com',
    'password': 'password123'
})
token = response.json()['access_token']

# Access sales data
headers = {'Authorization': f'Bearer {token}'}
customers = requests.get(
    'http://localhost:8000/api/v1/manufacturing/sales/customers',
    headers=headers
)
```

#### Admin Operations
```python
# Admin login
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'admin@company.com',
    'password': 'adminpass123'
})
token = response.json()['access_token']

# Access audit logs
headers = {'Authorization': f'Bearer {token}'}
audit_logs = requests.get(
    'http://localhost:8000/api/v1/manufacturing/admin/audit-logs',
    headers=headers
)
```

## Error Handling

### Authentication Errors
```json
{
  "detail": "Invalid credentials",
  "error_code": "AUTH_FAILED"
}
```

### Authorization Errors
```json
{
  "detail": "Insufficient permissions for this endpoint",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

### Rate Limiting Errors
```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

## Best Practices

### For Frontend Applications
1. Store tokens securely (not in localStorage)
2. Implement automatic token refresh
3. Handle 401 errors gracefully
4. Use HTTPS in production

### For API Consumers
1. Include proper Authorization headers
2. Respect rate limits
3. Handle token expiration
4. Validate SSL certificates

## Testing

### Unit Tests
```bash
# Test authentication
pytest tests/unit/test_auth.py

# Test RBAC
pytest tests/unit/test_rbac.py

# Test security middleware
pytest tests/unit/test_middleware.py
```

### Integration Tests
```bash
# Test manufacturing API endpoints
pytest tests/integration/test_manufacturing_api.py

# Test security scenarios
pytest tests/security/test_security.py
```

## Monitoring

### Key Metrics
- Authentication success/failure rates
- Token usage patterns
- Rate limit violations
- Security incidents

### Audit Queries
```sql
-- Failed login attempts
SELECT * FROM audit_logs 
WHERE action = 'api_access_failed' 
AND created_at > NOW() - INTERVAL '1 hour';

-- High-privilege operations
SELECT * FROM audit_logs 
WHERE additional_data->>'permissions' LIKE '%admin%'
AND created_at > NOW() - INTERVAL '1 day';
```

## Security Considerations

### Production Deployment
1. Use strong, unique secret keys
2. Enable MFA for all admin accounts
3. Implement IP whitelisting for sensitive endpoints
4. Regular security audits
5. Monitor for suspicious activities

### Compliance
- GDPR compliance for EU users
- Data retention policies
- Right to be forgotten
- Audit trail requirements

## Support

For security issues or questions:
- Email: security@ezbi-analytics.com
- Documentation: https://docs.ezbi-analytics.com/security
- GitHub Issues: https://github.com/ezbi-analytics/api/issues