# EZBI Analytics - Development Setup

## Quick Start

### 1. Start Database (one time)
```bash
docker-compose -f docker-compose.simple.yml up -d postgres
```

### 2. Start Backend
```bash
python run.py
```
Backend will be available at: **http://localhost:8000**

### 3. Start Frontend (in new terminal)
```bash
cd frontend
npm run dev
```
Frontend will be available at: **http://localhost:3000**

## What You Get

🏭 **Backend (port 8000)**
- FastAPI server with auto-reload
- Full EZBI Analytics API
- ML predictions (Prophet + LSTM)
- Manufacturing data endpoints
- Authentication system

🌐 **Frontend (port 3000)**
- Next.js React application
- Real-time hot reload
- French manufacturing UI
- TypeScript support
- Tailwind CSS styling

## Demo Login
- **Email:** demo@ezbi.fr  
- **Password:** demo123

## API Documentation
- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Database
- PostgreSQL running on port 5434
- 218K+ manufacturing records pre-loaded
- Connection: postgresql://ezbi_user:ezbi_password@localhost:5434/ezbi_db

## Development Tips

### Backend Development
- Auto-reload enabled - changes take effect immediately
- Logs show in terminal
- Full ML and prediction capabilities

### Frontend Development  
- Hot reload for instant UI changes
- TypeScript checking with `npm run type-check`
- Linting with `npm run lint`

### Troubleshooting
- If backend fails: Check database is running (`docker ps`)
- If frontend fails: Run `npm install` in frontend directory
- Database issues: `docker-compose -f docker-compose.simple.yml restart postgres`

## Architecture
```
Frontend (Next.js) ← → Backend (FastAPI) ← → Database (PostgreSQL)
   :3000                    :8000                  :5434
```