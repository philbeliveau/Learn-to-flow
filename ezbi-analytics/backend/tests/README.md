# EZBI Analytics - Comprehensive Testing Framework

A complete testing framework for the EZBI Analytics AI-powered cash flow prediction platform, designed specifically for French manufacturing SMEs.

## 🏗️ Testing Architecture

### Test Pyramid Structure

```
       E2E Tests (Playwright)
    ├─────────────────────────┤
   Integration Tests (FastAPI)
  ├─────────────────────────────┤
 Unit Tests (Models, Services, Utils)
├─────────────────────────────────┤
```

### Test Categories

- **Unit Tests** (`tests/unit/`) - 90%+ coverage of business logic
- **Integration Tests** (`tests/integration/`) - API endpoints and database operations
- **End-to-End Tests** (`tests/e2e/`) - Complete user workflows with Playwright
- **ML Model Tests** (`tests/ml/`) - Machine learning model validation and performance
- **Performance Tests** (`tests/performance/`) - Load testing and benchmarking
- **Security Tests** (`tests/security/`) - Security vulnerability testing

### Manufacturing Domain Focus

- **Cash Flow Prediction Testing** - ML model accuracy and reliability
- **French Compliance Testing** - RGPD, accounting standards, data retention
- **Manufacturing KPI Testing** - Production metrics, inventory, quality
- **ERP Integration Testing** - Sage, SAP, Cegid integrations
- **Banking API Testing** - Open banking PSD2 compliance

## 📊 Test Coverage Goals

| Test Type | Coverage Target | Focus Areas |
|-----------|----------------|-------------|
| Unit Tests | 95%+ | Business logic, models, utilities |
| Integration Tests | 90%+ | API endpoints, database operations |
| E2E Tests | Key workflows | User journeys, critical paths |
| ML Tests | 100% | Model accuracy, performance, reliability |
| Security Tests | All endpoints | Authentication, authorization, data protection |

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r tests/test_requirements.txt

# Install Playwright browsers
playwright install

# Set up test database
createdb ezbi_analytics_test
```

### Run All Tests

```bash
# Complete test suite
python tests/run_tests.py --suite all

# Quick smoke tests
python tests/run_tests.py --suite smoke

# Parallel execution
python tests/run_tests.py --parallel --workers 4
```

### Run Specific Test Suites

```bash
# Unit tests with coverage
python tests/run_tests.py --suite unit

# Integration tests
python tests/run_tests.py --suite integration

# End-to-end tests
python tests/run_tests.py --suite e2e

# ML model tests
python tests/run_tests.py --suite ml

# Performance tests
python tests/run_tests.py --suite performance

# Security tests
python tests/run_tests.py --suite security

# French compliance tests
python tests/run_tests.py --suite french

# Manufacturing domain tests
python tests/run_tests.py --suite manufacturing
```

## 🧪 Test Structure

### Unit Tests (`tests/unit/`)

```
unit/
├── test_models.py          # Database model tests
├── test_auth.py           # Authentication and security
├── test_services.py       # Business logic services
├── test_utils.py          # Utility functions
└── test_validators.py     # Input validation
```

**Key Features:**
- 95%+ code coverage
- Fast execution (< 30 seconds)
- Isolated from external dependencies
- French business logic validation
- Manufacturing domain rules

### Integration Tests (`tests/integration/`)

```
integration/
├── test_api_endpoints.py   # REST API testing
├── test_database.py       # Database operations
├── test_file_upload.py    # File processing
├── test_ml_integration.py # ML service integration
└── test_erp_integration.py # ERP system integration
```

**Key Features:**
- Real database interactions
- HTTP endpoint testing
- File upload/download workflows
- ML model integration
- ERP/banking API integration

### End-to-End Tests (`tests/e2e/`)

```
e2e/
├── test_playwright.py     # Complete user workflows
├── test_auth_flow.py      # Authentication journeys
├── test_dashboard.py      # Dashboard functionality
├── test_predictions.py   # Prediction workflows
└── test_reporting.py     # Report generation
```

**Key Features:**
- Real browser automation
- Complete user workflows
- Cross-browser testing
- French UI/UX testing
- Manufacturing scenarios

### ML Model Tests (`tests/ml/`)

```
ml/
├── test_models.py         # ML model testing
├── test_training.py       # Training pipeline tests
├── test_features.py       # Feature engineering
├── test_predictions.py   # Prediction accuracy
└── test_monitoring.py    # Model monitoring
```

**Key Features:**
- Model accuracy validation
- Training pipeline testing
- Feature engineering verification
- Prediction reliability
- Performance monitoring

### Performance Tests (`tests/performance/`)

```
performance/
├── test_load_testing.py   # Load and stress testing
├── test_api_performance.py # API response times
├── test_db_performance.py # Database query optimization
└── test_ml_performance.py # ML model performance
```

**Key Features:**
- Load testing (100+ concurrent users)
- Response time benchmarks
- Database query optimization
- ML model inference speed
- Memory and CPU monitoring

### Security Tests (`tests/security/`)

```
security/
├── test_security.py       # Security vulnerability testing
├── test_auth_security.py  # Authentication security
├── test_data_protection.py # Data protection (RGPD)
└── test_compliance.py     # French compliance
```

**Key Features:**
- SQL injection prevention
- XSS protection
- Authentication security
- Data protection (RGPD)
- French compliance validation

## 🔧 Test Configuration

### Environment Variables

```bash
# Test environment
TESTING=1
ENVIRONMENT=testing
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/ezbi_analytics_test
SECRET_KEY=test_secret_key_for_testing_only

# Test database
TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/ezbi_analytics_test

# ML testing
ML_MODEL_PATH=./test_models
PREDICTION_CACHE_TTL=0

# Performance testing
PERFORMANCE_TEST_DURATION=60
MAX_CONCURRENT_USERS=100
```

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    ml: Machine learning tests
    performance: Performance tests
    security: Security tests
    manufacturing: Manufacturing-specific tests
    french: French compliance tests

addopts = 
    --strict-markers
    --verbose
    --cov=app
    --cov-report=html
    --cov-fail-under=90
    --asyncio-mode=auto
```

## 📈 Test Data and Fixtures

### Manufacturing Test Data

```python
# Sample financial data for French manufacturing company
{
    "company": "Manufacture Lyonnaise SA",
    "siret": "12345678901234",
    "naf_code": "2562Z",  # Usinage
    "monthly_data": [
        {
            "period": "2024-01",
            "revenue": 150000,
            "expenses": 112500,
            "production_volume": 1200,
            "inventory": 37500
        }
    ]
}
```

### French Business Scenarios

- **Seasonal Manufacturing Patterns** - Q1/Q4 peaks, summer slowdowns
- **French Holidays Impact** - July/August vacations, public holidays
- **Compliance Requirements** - 7-year data retention, RGPD
- **Manufacturing KPIs** - Production efficiency, cost per unit

## 🚨 CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: ezbi_analytics_test
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/test_requirements.txt
      
      - name: Run tests
        run: python tests/run_tests.py --suite all
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Automation

- **Pre-commit Hooks** - Run tests before commits
- **Pull Request Testing** - Automatic test execution
- **Coverage Reporting** - Codecov integration
- **Performance Monitoring** - Track test execution times

## 📊 Test Reporting

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View coverage
open htmlcov/index.html
```

### Performance Reports

```bash
# Generate performance report
python tests/run_tests.py --suite performance

# View benchmarks
open reports/performance-report.html
```

### Security Reports

```bash
# Run security audit
python tests/run_tests.py --audit

# View security report
open reports/security-audit.html
```

## 🏭 Manufacturing Domain Testing

### Cash Flow Prediction Testing

- **Model Accuracy** - MAPE < 10% for 30-day predictions
- **Confidence Intervals** - Proper uncertainty quantification
- **Seasonal Patterns** - French manufacturing seasonality
- **Production Correlation** - Volume vs. cash flow correlation

### French Compliance Testing

- **RGPD Compliance** - Data subject rights, consent management
- **Accounting Standards** - 7-year data retention
- **Audit Trail** - Complete operation logging
- **Data Protection** - Encryption, access controls

### Manufacturing KPI Testing

- **Production Metrics** - Efficiency, capacity utilization
- **Quality Metrics** - Defect rates, compliance
- **Inventory Management** - Turnover, optimization
- **Cost Analysis** - Per-unit costs, margin analysis

## 🔧 Development Workflow

### Test-Driven Development (TDD)

1. **Write failing test** - Red phase
2. **Implement feature** - Green phase
3. **Refactor code** - Blue phase
4. **Repeat cycle** - Continuous improvement

### Testing Best Practices

- **Arrange-Act-Assert** pattern
- **Descriptive test names** in French context
- **Independent tests** - No test dependencies
- **Fast feedback** - Quick test execution
- **Comprehensive coverage** - Business critical paths

### Code Quality Gates

- **95%+ unit test coverage**
- **90%+ integration test coverage**
- **All security tests passing**
- **Performance benchmarks met**
- **French compliance validated**

## 📚 Resources and Documentation

### Testing Documentation

- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Testing](https://playwright.dev/python/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

### French Business Context

- [RGPD Compliance](https://www.cnil.fr/en/data-protection-act)
- [French Accounting Standards](https://www.anc.gouv.fr/)
- [Manufacturing Regulations](https://www.economie.gouv.fr/)

### Manufacturing Domain

- [Industry 4.0 Standards](https://www.industrie-techno.com/)
- [French Manufacturing](https://www.france-industrie.org/)
- [SME Regulations](https://www.economie.gouv.fr/entreprises)

## 🤝 Contributing

### Adding New Tests

1. **Identify test category** - Unit, integration, e2e, etc.
2. **Follow naming conventions** - `test_feature_scenario.py`
3. **Use appropriate fixtures** - Database, auth, mock services
4. **Add test markers** - `@pytest.mark.manufacturing`
5. **Update documentation** - Test descriptions and coverage

### Test Data Management

- **Use factories** - Factory Boy for test data generation
- **Mock external services** - ERP, banking APIs
- **French localization** - Use French business data
- **Clean test state** - Independent test execution

## 📞 Support

For testing framework support:

- **Issues**: GitHub Issues
- **Documentation**: `/tests/README.md`
- **Examples**: `/tests/examples/`
- **Best Practices**: `/tests/docs/`

---

**Made with ❤️ for French Manufacturing SMEs**

*Comprehensive testing ensures reliable AI-powered cash flow predictions for the manufacturing industry.*