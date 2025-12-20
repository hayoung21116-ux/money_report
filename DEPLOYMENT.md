# Deployment Guide

This guide explains how to deploy the Money Report web application to a production environment.

## Prerequisites

- Docker and Docker Compose installed
- Domain name (optional but recommended)
- SSL certificate (optional but recommended)

## Deployment Options

### 1. Local Deployment with Docker Compose

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd money_report
   ```

2. Start the application:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### 2. Cloud Deployment (Generic)

#### Using a Cloud Provider (AWS, Google Cloud, Azure)

1. Create a virtual machine or container service
2. Install Docker and Docker Compose
3. Deploy the application using docker-compose:
   ```bash
   docker-compose up -d
   ```

### 3. Domain Configuration

To use a custom domain:

1. Point your domain's DNS A record to your server's IP address
2. Configure reverse proxy (nginx example below)

#### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. SSL Configuration

To enable HTTPS, you can use Let's Encrypt with Certbot:

1. Install Certbot:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. Obtain SSL certificate:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. Certbot will automatically configure nginx to use SSL

### 5. Environment Variables

The application can be configured with environment variables:

#### Backend
- `DATA_FILE_PATH` - Path to the JSON data file (default: "data/ledger.json")

#### Frontend
- `REACT_APP_API_URL` - URL of the backend API (default: "http://localhost:8000")

### 6. Data Persistence

Data is stored in the `data/` directory as `ledger.json`. Make sure this directory is backed up regularly.

To backup data:
```bash
# On the server
cp -r data/ backups/data-$(date +%Y%m%d)
```

### 7. Monitoring and Maintenance

#### Health Checks
- Backend health check: `GET /health`
- Frontend health check: Load the main page

#### Logs
View application logs:
```bash
# Backend logs
docker-compose logs backend

# Frontend logs
docker-compose logs frontend
```

#### Updates
To update the application:
```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose down
docker-compose up --build -d
```

### 8. Security Considerations

1. Use HTTPS in production
2. Restrict access to the server
3. Regularly update Docker images
4. Use strong passwords for any admin interfaces
5. Implement proper firewall rules

### 9. Scaling Considerations

For high-traffic applications:

1. Use a proper database instead of JSON files
2. Implement load balancing
3. Use a CDN for static assets
4. Implement caching strategies

### 10. Troubleshooting

#### Common Issues

1. **Application not accessible**
   - Check if containers are running: `docker-compose ps`
   - Check logs: `docker-compose logs`
   - Verify ports are not blocked by firewall

2. **Data not persisting**
   - Ensure the `data/` directory has proper permissions
   - Verify volume mapping in docker-compose.yml

3. **API connection issues**
   - Check if backend is running: `docker-compose logs backend`
   - Verify API_URL configuration in frontend

#### Useful Commands

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs

# Restart specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Rebuild containers
docker-compose up --build -d
```

## Support

For issues with deployment, please check:
1. Docker and Docker Compose documentation
2. Cloud provider documentation
3. Application logs
4. Community forums for the technologies used
