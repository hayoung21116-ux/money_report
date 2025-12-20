# Money Report Backend

This is the FastAPI backend for the Money Report ledger application.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- pip

### Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the development server:
   ```bash
   uvicorn main:app --reload
   ```

2. Open your browser and navigate to `http://localhost:8000` to see the API documentation

### Running with Production Server

For production deployment:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Project Structure

```
backend/
├── api/                    # API routers
│   ├── accounts.py         # Account-related endpoints
│   └── stats.py            # Statistics-related endpoints
├── core/                   # Business logic
│   ├── repository.py       # Data repository layer
│   └── service.py          # Service layer with business logic
├── database/               # Database layer
│   └── json_database.py    # JSON file-based database implementation
├── models/                 # Data models
│   └── domain.py           # Pydantic models
├── main.py                 # Application entry point
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Available Endpoints

### Accounts
- `GET /accounts/` - Get all accounts
- `POST /accounts/` - Create a new account
- `GET /accounts/{account_id}` - Get account by ID
- `PUT /accounts/{account_id}` - Update an account
- `DELETE /accounts/{account_id}` - Delete an account
- `POST /accounts/{account_id}/toggle-status` - Toggle account status
- `GET /accounts/{account_id}/transactions` - Get account transactions
- `POST /accounts/{account_id}/transactions` - Add transaction to account
- `GET /accounts/{account_id}/valuations` - Get account valuations
- `POST /accounts/{account_id}/valuations` - Add valuation to account
- `DELETE /accounts/{account_id}/valuations/{valuation_id}` - Delete valuation from account

### Statistics
- `GET /stats/total-assets` - Get total assets
- `GET /stats/total-cash` - Get total cash
- `GET /stats/monthly-income-breakdown` - Get monthly income breakdown
- `GET /stats/salaries` - Get salary data
- `POST /stats/salaries` - Add salary data
- `GET /stats/asset-allocation` - Get asset allocation

## Data Persistence

The application uses a JSON file-based database by default:
- Data is stored in `data/ledger.json`
- The file is automatically created if it doesn't exist
- All data is persisted between application restarts

## Technologies Used

- FastAPI - Modern, fast web framework for building APIs
- Pydantic - Data validation and settings management
- Uvicorn - ASGI server for running the application
- Python 3.7+

## Development

### Adding New Endpoints

1. Create a new router in the `api/` directory
2. Import and include the router in `main.py`
3. Add appropriate service methods in `core/service.py`
4. Update the repository if needed in `core/repository.py`

### Testing

Run the development server with auto-reload:
```bash
uvicorn main:app --reload
```

The server will automatically restart when code changes are detected.

## Deployment

For production deployment, you can use:
- Docker (see Dockerfile example below)
- Cloud platforms like Heroku, AWS, Google Cloud, etc.
- Traditional server deployment

### Docker Deployment

Example Dockerfile:
```dockerfile
FROM python:3.9

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

The application can be configured with environment variables:
- `DATA_FILE_PATH` - Path to the JSON data file (default: "data/ledger.json")

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests if applicable
5. Commit your changes
6. Push to the branch
