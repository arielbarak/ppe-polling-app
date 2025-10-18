# Deployment Guide 🚀

Get your PPE polling system running in production.

## Option 1: Docker (Recommended)

### Single Command Deployment

```bash
docker-compose up -d
```

That's it. System is live.

### Configuration

Edit `docker-compose.yml`:

```yaml
environment:
  - API_BASE_URL=https://your-domain.com/api
  - FRONTEND_URL=https://your-domain.com
```

## Option 2: Manual Deployment

### Backend

**Install dependencies:**
```bash
cd backend
pip install -r requirements.txt --break-system-packages
```

**Run with Gunicorn:**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Or with systemd:**

Create `/etc/systemd/system/ppe-backend.service`:

```ini
[Unit]
Description=PPE Polling Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/ppe-polling/backend
ExecStart=/usr/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ppe-backend
sudo systemctl start ppe-backend
```

### Frontend

**Build:**
```bash
cd frontend
npm install
npm run build
```

**Serve with nginx:**

Create `/etc/nginx/sites-available/ppe-polling`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend
    location / {
        root /var/www/ppe-polling/frontend/build;
        try_files $uri /index.html;
    }
    
    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable and reload:
```bash
sudo ln -s /etc/nginx/sites-available/ppe-polling /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Option 3: Cloud Platforms

### Heroku

```bash
# Backend
cd backend
heroku create your-app-backend
git push heroku main

# Frontend
cd frontend
heroku create your-app-frontend
heroku buildpacks:set mars/create-react-app
git push heroku main
```

### AWS

Use provided CloudFormation template:

```bash
aws cloudformation create-stack \
  --stack-name ppe-polling \
  --template-body file://aws-template.yaml
```

### DigitalOcean

Use App Platform with `app.yaml`:

```yaml
name: ppe-polling
services:
  - name: backend
    dockerfile_path: backend/Dockerfile
    http_port: 8000
    routes:
      - path: /api
  - name: frontend
    dockerfile_path: frontend/Dockerfile
    routes:
      - path: /
```

## SSL/TLS Setup

### With Certbot (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Auto-renew:
```bash
sudo systemctl enable certbot.timer
```

## Environment Variables

Create `.env` file:

```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost/ppe_polling
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://your-domain.com

# Frontend
REACT_APP_API_URL=https://your-domain.com/api
REACT_APP_WS_URL=wss://your-domain.com/ws
```

## Database Setup (Optional)

If using PostgreSQL:

```bash
# Install PostgreSQL
sudo apt install postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE ppe_polling;
CREATE USER ppe_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ppe_polling TO ppe_user;
```

Update backend config to use PostgreSQL instead of in-memory storage.

## Health Checks

Backend health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

## Monitoring

Add basic monitoring:

```bash
# Install monitoring tools
pip install prometheus-client

# Add to backend
from prometheus_client import Counter, Histogram
```

## Troubleshooting

**Backend won't start:**
```bash
# Check logs
sudo journalctl -u ppe-backend -f

# Verify port not in use
sudo lsof -i :8000
```

**Frontend build fails:**
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install
```

**WebSocket issues:**
```bash
# Ensure nginx websocket config is correct
# Check proxy_set_header Upgrade and Connection
```

## Performance Tuning

**Backend:**
- Increase Gunicorn workers: `-w 8`
- Use async worker: `-k uvicorn.workers.UvicornWorker`
- Enable gzip in nginx

**Frontend:**
- Enable caching headers
- Use CDN for static assets
- Compress build output

## Security Checklist

- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Secrets in environment variables
- [ ] Regular security updates
- [ ] Firewall configured

## Backup

Backup important data:

```bash
# Backup database (if using PostgreSQL)
pg_dump ppe_polling > backup.sql

# Backup configuration
tar -czf config-backup.tar.gz backend/.env frontend/.env
```

## Scaling

**Horizontal scaling:**
- Run multiple backend instances behind load balancer
- Use Redis for WebSocket pub/sub
- Database connection pooling

**Vertical scaling:**
- Increase server resources
- Optimize database queries
- Enable caching

That's it! Your PPE polling system is production-ready.