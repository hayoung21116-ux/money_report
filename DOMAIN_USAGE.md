# Domain Usage Guide

This guide explains how to use a custom domain with your deployed Money Report web application.

## How Domain Connectivity Works

With the web application architecture we've created, you can use a single domain to access your application from any device:
- Desktop computers
- Mobile phones
- Tablets

The same URL works for all devices, and the application automatically adapts to different screen sizes.

## Setting Up Your Domain

### 1. Purchase a Domain

You can purchase a domain from providers like:
- GoDaddy
- Namecheap
- Google Domains
- AWS Route 53
- Cloudflare

### 2. Point Your Domain to Your Server

1. Get your server's IP address:
   ```bash
   # On your server, run:
   curl ifconfig.me
   ```

2. In your domain registrar's DNS settings, create an A record:
   - Type: A
   - Name: @ (or your subdomain like "ledger")
   - Value: Your server's IP address
   - TTL: 300 (or default)

### 3. Configure Reverse Proxy (Nginx)

Create an nginx configuration file (e.g., `/etc/nginx/sites-available/money-report`):

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect www to non-www
    if ($host = www.your-domain.com) {
        return 301 https://your-domain.com$request_uri;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/money-report /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Enable HTTPS with Let's Encrypt

Install Certbot:
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

Obtain SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot will automatically:
- Obtain an SSL certificate
- Configure nginx to use HTTPS
- Set up automatic certificate renewal

### 5. Update Application Configuration

Update your docker-compose.yml to use the domain:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATA_FILE_PATH=/app/data/ledger.json

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=https://your-domain.com/api
```

Rebuild and restart:
```bash
docker-compose down
docker-compose up --build -d
```

## Benefits of Using a Domain

### Single URL for All Devices
- Same address works on desktop, mobile, and tablet
- No need to remember different URLs for different devices
- Easy to share with family members

### Professional Appearance
- Looks more professional than an IP address
- Easier to remember
- Can use subdomains for organization (e.g., ledger.yourname.com)

### Better Security
- HTTPS encryption
- Professional SSL certificates
- Better integration with security tools

### SEO and Analytics
- Search engines can index your domain
- Analytics tools work better with domains
- Better for sharing and marketing

## Accessing Your Application

Once everything is configured, you can access your application from any device using:

```
https://your-domain.com
```

The application will automatically:
- Detect the device type
- Adjust the layout for optimal viewing
- Provide the same functionality on all devices

## Mobile-Specific Features

The application includes mobile-specific features:
- Touch-friendly interface
- Responsive design that adapts to screen size
- Mobile-optimized navigation
- Fast loading times

## Data Synchronization

All devices access the same data in real-time:
- Changes on desktop appear immediately on mobile
- No manual synchronization required
- Data is stored on your server, not on individual devices

## Maintenance and Updates

With a domain setup:
- Updates are deployed once and available to all users
- No need to update separate mobile apps
- Easy to make configuration changes
- Centralized logging and monitoring

## Troubleshooting Domain Issues

### Common Issues and Solutions

1. **Domain not resolving**
   - Check DNS records at your registrar
   - DNS changes can take up to 48 hours to propagate
   - Use `nslookup your-domain.com` to check DNS

2. **SSL certificate issues**
   - Check certificate expiration: `sudo certbot certificates`
   - Renew manually if needed: `sudo certbot renew`
   - Check nginx configuration

3. **Application not loading**
   - Check if Docker containers are running: `docker-compose ps`
   - Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
   - Check application logs: `docker-compose logs`

### Useful Commands

```bash
# Check DNS resolution
nslookup your-domain.com

# Check nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# View application logs
docker-compose logs
```

## Best Practices

1. **Regular Backups**
   - Backup your data directory regularly
   - Backup your nginx configuration
   - Keep a copy of your SSL certificates

2. **Security Updates**
   - Keep your server OS updated
   - Update Docker and Docker Compose regularly
   - Monitor security advisories for your technologies

3. **Monitoring**
   - Set up uptime monitoring
   - Monitor disk space and memory usage
   - Set up alerts for critical issues

4. **Performance**
   - Use a CDN for static assets
   - Implement caching strategies
   - Monitor page load times

## Support

For issues with domain configuration:
1. Check your domain registrar's documentation
2. Review nginx documentation
3. Check Let's Encrypt community forums
4. Review Docker and Docker Compose documentation
