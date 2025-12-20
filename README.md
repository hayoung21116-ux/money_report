# Money Report - Web Application Conversion

This project is a conversion of the PySide6 desktop ledger application to a web-based application using modern web technologies.

## Project Structure

```
money_report/
├── backend/              # FastAPI backend
│   ├── api/              # API endpoints
│   ├── core/             # Business logic (extracted from current app)
│   ├── models/           # Data models
│   ├── database/         # Database layer
│   └── main.py           # Application entry point
├── frontend/             # React frontend
│   ├── public/           # Static assets
│   ├── src/              # React components
│   │   ├── components/   # UI components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API service layer
│   │   ├── App.js        # Main application component
│   │   └── index.js      # Entry point
│   └── package.json      # Frontend dependencies
├── shared/               # Shared code between frontend and backend
│   └── models/           # Shared data models
├── data/                 # Data files
│   └── ledger.json       # Current data file
└── README.md             # This file
```

## Technology Stack

### Backend
- **FastAPI**: Modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
- **Pydantic**: Data validation and settings management using Python type annotations.
- **Uvicorn**: Lightning-fast ASGI server implementation, using uvloop and httptools.

### Frontend
- **React**: JavaScript library for building user interfaces.
- **React Router**: Declarative routing for React applications.
- **Axios**: Promise based HTTP client for the browser and node.js.
- **Styled Components**: Visual primitives for the component age.

## Implementation Plan

### Phase 1: Backend Development
1. Extract business logic from current application
2. Create FastAPI application structure
3. Implement API endpoints for all service methods
4. Set up data persistence layer
5. Add validation and error handling

### Phase 2: Frontend Development
1. Set up React application
2. Create responsive UI components matching current design
3. Implement state management
4. Connect to backend API
5. Add mobile-specific features

### Phase 3: Deployment
1. Containerize application with Docker
2. Set up CI/CD pipeline
3. Deploy to cloud platform
4. Configure domain and SSL

## Getting Started

### Prerequisites
- Python 3.7+
- Node.js 14+
- npm or yarn

### Installation
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Running the Application
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm start
```
