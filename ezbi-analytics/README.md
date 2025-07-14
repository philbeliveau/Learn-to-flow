# 🚀 EZBI Analytics

**AI-Powered Cash Flow Prediction Platform for French Manufacturing SMEs**

EZBI Analytics is a comprehensive platform that leverages artificial intelligence to provide accurate cash flow predictions specifically designed for French small and medium manufacturing enterprises. Using advanced machine learning models, real-time data integration, and manufacturing-specific insights, EZBI helps businesses optimize their financial planning and decision-making.

## 🎯 Key Features

### 💰 Advanced Cash Flow Prediction
- **AI-Powered Models**: Prophet, LSTM, and Ensemble methods
- **Manufacturing-Specific**: Tailored for French SME needs
- **Real-Time Updates**: Live data integration and predictions
- **Scenario Modeling**: Multiple prediction scenarios with confidence intervals

### 🏭 Manufacturing Intelligence
- **Production Planning**: Align cash flow with production cycles
- **Seasonality Detection**: Account for manufacturing seasonality patterns
- **Supply Chain Impact**: Factor in supplier payment terms and delivery schedules
- **Equipment Financing**: Predict capital expenditure cash flow impact

### 🔐 Enterprise Security
- **RGPD Compliance**: Full French data protection compliance
- **Multi-Factor Authentication**: Enhanced security for financial data
- **End-to-End Encryption**: Secure data transmission and storage
- **Audit Trails**: Complete activity logging and compliance reporting

### 🔗 Enterprise Integrations
- **ERP Systems**: Sage, SAP Business One, Cegid
- **Banking APIs**: Open Banking PSD2 compliance
- **Excel/CSV**: Easy data import and export
- **Custom APIs**: Flexible integration capabilities

## 🏗️ Architecture

### Frontend (Next.js 14)
```
frontend/
├── src/
│   ├── app/          # App Router (Next.js 14)
│   ├── components/   # Reusable UI components
│   ├── lib/          # Utilities and configurations
│   ├── hooks/        # Custom React hooks
│   └── types/        # TypeScript type definitions
├── public/           # Static assets
└── tests/           # Frontend tests
```

### Backend (FastAPI)
```
backend/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── core/         # Core configurations and security
│   ├── models/       # SQLAlchemy models
│   ├── services/     # Business logic services
│   ├── ml/           # Machine learning modules
│   └── integrations/ # External service integrations
├── migrations/       # Database migrations
└── tests/           # Backend tests
```

### ML Pipeline
```
ml-pipeline/
├── models/           # Trained ML models
├── data/            # Training and test data
├── notebooks/       # Jupyter notebooks for experimentation
└── scripts/         # Training and prediction scripts
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm 9+
- Python 3.11+
- PostgreSQL 15+
- Redis (for background tasks)

### 1. Clone and Setup
```bash
git clone https://github.com/philbeliveau/learn-to-flow.git
cd learn-to-flow/ezbi-analytics
cp .env.example .env
# Configure your environment variables
```

### 2. Install Dependencies
```bash
# Install all dependencies (frontend + backend)
npm install

# Or install separately
cd frontend && npm install
cd ../backend && pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Create database and run migrations
npm run db:migrate

# Seed with sample data (optional)
cd backend && python scripts/seed_data.py
```

### 4. Start Development
```bash
# Start both frontend and backend
npm run dev

# Or start separately
npm run dev:frontend  # Frontend: http://localhost:3000
npm run dev:backend   # Backend: http://localhost:8000
```

## 🧪 Testing

### Run All Tests
```bash
npm run test
```

### Frontend Tests
```bash
cd frontend
npm run test          # Run once
npm run test:watch    # Watch mode
npm run test:coverage # With coverage
```

### Backend Tests
```bash
cd backend
pytest                # Run all tests
pytest -v            # Verbose output
pytest --cov         # With coverage
```

## 🚀 Deployment

### Frontend (Vercel)
```bash
npm run deploy:frontend
```

### Backend (Railway)
```bash
npm run deploy:backend
```

### Environment Variables
```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_ENVIRONMENT=production

# Backend (.env)
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://user:pass@host:port
JWT_SECRET=your-jwt-secret
ENCRYPTION_MASTER_KEY=your-encryption-key
```

## 📊 Machine Learning

### Supported Models
- **Prophet**: Time series forecasting with seasonality
- **LSTM**: Deep learning for complex patterns
- **Ensemble**: Combined model predictions with confidence scoring

### Training Models
```bash
npm run ml:train      # Train all models
cd ml-pipeline && python train_prophet.py
cd ml-pipeline && python train_lstm.py
```

### Making Predictions
```bash
npm run ml:predict    # Generate predictions
```

## 🔗 API Documentation

### Interactive API Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
```
POST /api/v1/auth/login           # User authentication
GET  /api/v1/predictions          # Get cash flow predictions
POST /api/v1/predictions/generate # Generate new predictions
GET  /api/v1/companies/{id}       # Company data
POST /api/v1/upload/financial     # Upload financial data
```

## 🔐 Security Features

### Authentication
- JWT tokens with refresh mechanism
- Multi-factor authentication (TOTP)
- Role-based access control (RBAC)
- Session management

### Data Protection
- RGPD/GDPR compliance
- Data encryption at rest and in transit
- Audit logging
- Data retention policies

### Security Headers
- CORS protection
- Rate limiting
- Input validation and sanitization
- SQL injection protection

## 🏭 Manufacturing-Specific Features

### Production Integration
- Production cycle alignment
- Raw material cost fluctuations
- Finished goods inventory impact
- Manufacturing capacity planning

### French SME Compliance
- French accounting standards (PCG)
- VAT and tax calculation integration
- Social charges and payroll integration
- French banking system compatibility

## 🛠️ Development

### Code Quality
```bash
npm run lint          # Lint all code
npm run format        # Format all code
npm run type-check    # TypeScript checking
```

### Database Operations
```bash
npm run db:create-migration  # Create new migration
npm run db:migrate          # Apply migrations
```

### Performance Monitoring
- Frontend: Vercel Analytics
- Backend: FastAPI metrics + Prometheus
- Database: PostgreSQL monitoring
- ML: Model performance tracking

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Guidelines
- Follow TypeScript strict mode
- Write tests for new features
- Update documentation
- Ensure RGPD compliance
- Follow French localization standards

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/philbeliveau/learn-to-flow/issues)
- **Security**: security@ezbi-analytics.com

## 🚀 Roadmap

- [ ] Advanced ML models (Transformer-based)
- [ ] Mobile application
- [ ] Advanced integrations (Odoo, Dolibarr)
- [ ] Real-time collaboration features
- [ ] Advanced reporting and analytics
- [ ] Multi-tenant SaaS platform

---

**EZBI Analytics** - Empowering French Manufacturing SMEs with AI-driven financial intelligence.