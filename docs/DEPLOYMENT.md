# Q2LMS Deployment Guide
Educational Question Database Management Platform

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [System Requirements](#system-requirements)
3. [Quick Deployment](#quick-deployment)
4. [Production Deployments](#production-deployments)
5. [Configuration Management](#configuration-management)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Backup and Recovery](#backup-and-recovery)

---

## Deployment Overview

Q2LMS offers flexible deployment options designed for educational institutions, from individual instructor use to enterprise-wide implementations. Choose the deployment tier that matches your needs and scale.

### Deployment Tiers

| Tier | Use Case | Platform | Users | Features |
|------|----------|----------|-------|----------|
| **Development** | Individual instructors | Local Python | 1 | Full feature set |
| **Department** | Small teams, courses | Streamlit Cloud/Docker | 5-50 | Shared databases |
| **Enterprise** | Large institutions | Kubernetes | 50-500 | Load balancing, monitoring |
| **Institution** | Multi-campus | Cloud platforms | 500+ | High availability, scaling |

### Key Features by Tier
- **All Tiers**: Question editing, LaTeX support, Canvas QTI export, multi-format support
- **Department+**: User management, shared question databases, basic analytics
- **Enterprise+**: SSO integration, advanced monitoring, API access, backup automation
- **Institution**: Multi-tenant architecture, custom integrations, dedicated support

---

## System Requirements

### Minimum Requirements
```bash
# Hardware
CPU: 2 cores, 2.0 GHz
RAM: 4 GB (8 GB recommended)
Storage: 10 GB available space
Network: Stable internet connection

# Software
Python: 3.8 or later
Browser: Modern browser (Chrome, Firefox, Safari, Edge)
Operating System: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
```

### Production Requirements
```bash
# Hardware (per instance)
CPU: 4+ cores, 2.4+ GHz
RAM: 8-16 GB (depending on concurrent users)
Storage: 50+ GB SSD recommended
Network: High-speed connection, backup connectivity

# Software Stack
Python: 3.9+ (recommended)
Streamlit: 1.20.0+
Database: File-based (JSON) or PostgreSQL for enterprise
Load Balancer: nginx, Traefik, or cloud load balancer
Monitoring: Prometheus/Grafana recommended
```

### Dependencies
```python
# Core Dependencies (automatically installed)
streamlit >= 1.20.0
pandas >= 1.5.0
plotly >= 5.0.0

# Optional Dependencies
numpy >= 1.21.0          # Enhanced mathematical operations
python-dateutil >= 2.8.0 # Advanced date handling
psutil                   # System monitoring
```

---

## Quick Deployment

### Local Development Setup

**Step 1: Clone and Install**
```bash
# Clone the repository
git clone https://github.com/aknoesen/q2lms.git
cd q2lms

# Create virtual environment (recommended)
python -m venv q2lms-env
source q2lms-env/bin/activate  # On Windows: q2lms-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Step 2: Launch Application**
```bash
# Start Q2LMS
python -m streamlit run streamlit_app.py

# Access application
# Browser will automatically open to: http://localhost:8501
```

**Step 3: Initial Setup**
1. **Upload Sample Data**: Use files from `examples/` directory
2. **Test Features**: Try question editing, filtering, and export
3. **Verify LaTeX**: Check mathematical notation rendering
4. **Test Export**: Generate QTI package for Canvas

### Streamlit Cloud Deployment

**Step 1: Prepare Repository**
```bash
# Ensure your repository has:
├── streamlit_app.py       # Main application
├── requirements.txt       # Dependencies
├── modules/              # Core modules
├── utilities/            # Helper functions
└── examples/             # Sample data
```

**Step 2: Deploy to Streamlit Cloud**
1. **Connect Repository**: Link your GitHub repository
2. **Configure Settings**: 
   - Main file: `streamlit_app.py`
   - Python version: 3.9+
3. **Deploy**: Streamlit Cloud handles the rest
4. **Access**: Your app at `https://[your-app-name].streamlit.app`

---

## Production Deployments

### Department-Level Docker Deployment

**Step 1: Create Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 q2lms && chown -R q2lms:q2lms /app
USER q2lms

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Step 2: Docker Compose for Department**
```yaml
# docker-compose.yml
version: '3.8'

services:
  q2lms:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - Q2LMS_ENV=production
      - Q2LMS_DATA_DIR=/app/data
      - Q2LMS_LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - q2lms
    restart: unless-stopped
```

**Step 3: Deploy Department Setup**
```bash
# Deploy with Docker Compose
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs q2lms

# Access application
# http://your-server-ip or https://your-domain.edu
```

### Enterprise Kubernetes Deployment

**Step 1: Kubernetes Manifests**
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: q2lms

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: q2lms
  namespace: q2lms
spec:
  replicas: 3
  selector:
    matchLabels:
      app: q2lms
  template:
    metadata:
      labels:
        app: q2lms
    spec:
      containers:
      - name: q2lms
        image: your-registry/q2lms:latest
        ports:
        - containerPort: 8501
        env:
        - name: Q2LMS_ENV
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: q2lms-service
  namespace: q2lms
spec:
  selector:
    app: q2lms
  ports:
  - port: 80
    targetPort: 8501
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: q2lms-ingress
  namespace: q2lms
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - q2lms.your-institution.edu
    secretName: q2lms-tls
  rules:
  - host: q2lms.your-institution.edu
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: q2lms-service
            port:
              number: 80
```

**Step 2: Deploy to Kubernetes**
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n q2lms
kubectl get services -n q2lms
kubectl get ingress -n q2lms

# Check application logs
kubectl logs -f deployment/q2lms -n q2lms
```

### Institution-Level Cloud Deployment

**AWS ECS with Fargate**
```yaml
# aws/task-definition.json
{
  "family": "q2lms",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "q2lms",
      "image": "your-account.dkr.ecr.region.amazonaws.com/q2lms:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "Q2LMS_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/q2lms",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Azure Container Instances**
```yaml
# azure/container-group.yaml
apiVersion: 2019-12-01
location: eastus
name: q2lms-container-group
properties:
  containers:
  - name: q2lms
    properties:
      image: your-registry.azurecr.io/q2lms:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 1.5
      ports:
      - port: 8501
        protocol: TCP
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: '8501'
    dnsNameLabel: q2lms-institution
```

---

## Configuration Management

### Environment Variables
```bash
# Core Configuration
export Q2LMS_ENV=production                    # Environment: development, staging, production
export Q2LMS_DATA_DIR=/app/data               # Data storage directory
export Q2LMS_LOG_LEVEL=info                  # Logging: debug, info, warning, error
export Q2LMS_PORT=8501                       # Application port

# Feature Flags
export Q2LMS_ADVANCED_UPLOAD=true            # Enable advanced upload features
export Q2LMS_QUESTION_EDITOR=true            # Enable question editing
export Q2LMS_EXPORT_SYSTEM=true              # Enable export functionality
export Q2LMS_LATEX_PROCESSOR=true            # Enable LaTeX processing

# Phase 8 Features
export Q2LMS_MULTI_TOPIC_ENABLED=true        # Multi-topic filtering
export Q2LMS_GRACEFUL_EXIT_ENABLED=true      # Enhanced exit system
export Q2LMS_SESSION_TRACKING=true           # Session management

# Performance Tuning
export Q2LMS_MAX_UPLOAD_SIZE=200             # Max file size MB
export Q2LMS_SESSION_TIMEOUT=3600            # Session timeout seconds
export Q2LMS_MEMORY_LIMIT=1024               # Memory limit MB

# Security
export Q2LMS_ENABLE_CORS=false               # CORS settings
export Q2LMS_TRUSTED_HOSTS=localhost         # Trusted host list
export Q2LMS_SECURE_COOKIES=true             # Secure cookie settings
```

### Configuration Files
```toml
# config/q2lms.toml
[application]
name = "Q2LMS"
version = "1.0.0"
debug = false

[server]
host = "0.0.0.0"
port = 8501
max_upload_size = 200

[features]
advanced_upload = true
question_editor = true
export_system = true
latex_processor = true
multi_topic_filtering = true
graceful_exit = true

[database]
type = "file"  # file, postgresql
data_directory = "/app/data"
backup_enabled = true
backup_interval = 3600

[logging]
level = "info"
file = "/app/logs/q2lms.log"
max_size = "100MB"
retention_days = 30

[monitoring]
enabled = true
metrics_port = 9090
health_check_enabled = true
```

---

## Monitoring and Maintenance

### Health Checks
```python
# health_check.py
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import psutil

def check_application_health():
    """Comprehensive health check for Q2LMS"""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'checks': {}
    }
    
    # Check core dependencies
    try:
        import streamlit
        import pandas
        health_status['checks']['dependencies'] = 'ok'
    except ImportError as e:
        health_status['checks']['dependencies'] = f'error: {e}'
        health_status['status'] = 'unhealthy'
    
    # Check system resources
    memory_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent()
    disk_usage = psutil.disk_usage('/').percent
    
    health_status['checks']['memory'] = f'{memory_usage:.1f}%'
    health_status['checks']['cpu'] = f'{cpu_usage:.1f}%'
    health_status['checks']['disk'] = f'{disk_usage:.1f}%'
    
    # Resource warnings
    if memory_usage > 80 or cpu_usage > 80 or disk_usage > 90:
        health_status['status'] = 'warning'
    
    # Check application features
    try:
        # Test data processing
        test_df = pd.DataFrame({'test': [1, 2, 3]})
        health_status['checks']['data_processing'] = 'ok'
        
        # Test file operations
        import os
        test_file = '/tmp/q2lms_health_test.txt'
        with open(test_file, 'w') as f:
            f.write('health check')
        os.remove(test_file)
        health_status['checks']['file_operations'] = 'ok'
        
    except Exception as e:
        health_status['checks']['application_features'] = f'error: {e}'
        health_status['status'] = 'unhealthy'
    
    return health_status

# Health endpoint for load balancers
@st.cache_data(ttl=30)  # Cache for 30 seconds
def health_endpoint():
    return check_application_health()
```

### Performance Monitoring
```python
# monitoring.py
import time
import logging
from functools import wraps

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'response_times': [],
            'error_count': 0,
            'active_sessions': 0
        }
    
    def track_performance(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                self.metrics['request_count'] += 1
                return result
            except Exception as e:
                self.metrics['error_count'] += 1
                logging.error(f"Error in {func.__name__}: {e}")
                raise
            finally:
                response_time = time.time() - start_time
                self.metrics['response_times'].append(response_time)
                # Keep only last 1000 response times
                if len(self.metrics['response_times']) > 1000:
                    self.metrics['response_times'] = self.metrics['response_times'][-1000:]
        
        return wrapper
    
    def get_metrics_summary(self):
        if self.metrics['response_times']:
            avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
            max_response_time = max(self.metrics['response_times'])
        else:
            avg_response_time = 0
            max_response_time = 0
        
        return {
            'total_requests': self.metrics['request_count'],
            'total_errors': self.metrics['error_count'],
            'error_rate': self.metrics['error_count'] / max(self.metrics['request_count'], 1) * 100,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'active_sessions': self.metrics['active_sessions']
        }

# Global monitor instance
app_monitor = PerformanceMonitor()
```

### Automated Maintenance
```bash
#!/bin/bash
# maintenance.sh - Automated maintenance script

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Q2LMS maintenance routine"

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    log "WARNING: Disk usage is ${DISK_USAGE}%"
    # Clean old logs
    find /app/logs -name "*.log" -mtime +30 -delete
    log "Cleaned old log files"
fi

# Backup configuration
BACKUP_DIR="/app/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
cp -r /app/config $BACKUP_DIR/
cp -r /app/data $BACKUP_DIR/
log "Configuration and data backed up to $BACKUP_DIR"

# Check application health
python3 -c "
import sys
sys.path.append('/app')
from health_check import check_application_health

health = check_application_health()
if health['status'] != 'healthy':
    print(f'Application health check failed: {health}')
    exit(1)
else:
    print('Application health check passed')
"

# Restart if needed
if [ $? -ne 0 ]; then
    log "Health check failed, restarting application"
    docker-compose restart q2lms
fi

log "Maintenance routine completed"
```

---

## Troubleshooting

### Common Issues and Solutions

**Issue: Application won't start**
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip list | grep streamlit
pip list | grep pandas

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check for missing files
ls -la streamlit_app.py modules/ utilities/

# Check logs
tail -f logs/q2lms.log
```

**Issue: Memory usage high**
```bash
# Monitor memory usage
ps aux | grep streamlit
free -h

# Check for memory leaks
python3 -c "
import psutil
process = psutil.Process()
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Restart application
docker-compose restart q2lms
```

**Issue: Upload failures**
```bash
# Check file permissions
ls -la data/
chmod 755 data/

# Check disk space
df -h

# Test file upload manually
python3 -c "
import json
test_data = {'questions': [{'title': 'test'}]}
with open('/tmp/test.json', 'w') as f:
    json.dump(test_data, f)
print('Test file created successfully')
"
```

**Issue: Export not working**
```bash
# Check LaTeX dependencies
python3 -c "
try:
    import modules.export.qti_generator
    print('QTI generator available')
except ImportError as e:
    print(f'QTI generator error: {e}')
"

# Verify export directory
mkdir -p /app/exports
chmod 755 /app/exports

# Test export functionality
python3 -c "
import pandas as pd
test_df = pd.DataFrame([
    {'Title': 'Test', 'Type': 'multiple_choice', 'Question_Text': 'Test question'}
])
print(f'Test export data ready: {len(test_df)} questions')
"
```

### Log Analysis
```bash
# View recent errors
grep ERROR /app/logs/q2lms.log | tail -20

# Monitor real-time logs
tail -f /app/logs/q2lms.log | grep -E "(ERROR|WARNING)"

# Analyze performance
grep "response_time" /app/logs/q2lms.log | awk '{print $3}' | sort -n | tail -10

# Check user activity
grep "session_start" /app/logs/q2lms.log | wc -l
```

### Debug Mode
```python
# Enable debug mode
export Q2LMS_DEBUG=true
export Q2LMS_LOG_LEVEL=debug

# Debug configuration
[logging]
level = "debug"
show_sql = true
show_performance = true
```

---

## Backup and Recovery

### Automated Backup Strategy
```bash
#!/bin/bash
# backup.sh - Comprehensive backup script

BACKUP_ROOT="/backups/q2lms"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$DATE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_ROOT/backup.log"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Starting Q2LMS backup: $DATE"

# Backup application data
log "Backing up application data"
cp -r /app/data "$BACKUP_DIR/"

# Backup configuration
log "Backing up configuration"
cp -r /app/config "$BACKUP_DIR/"

# Backup logs (last 7 days)
log "Backing up recent logs"
find /app/logs -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/logs/" \;

# Backup database state
if [ -f /app/data/current_database.json ]; then
    log "Backing up current database state"
    cp /app/data/current_database.json "$BACKUP_DIR/"
fi

# Create backup metadata
cat > "$BACKUP_DIR/backup_info.txt" << EOF
Q2LMS Backup Information
========================
Backup Date: $(date)
Backup Directory: $BACKUP_DIR
Application Version: $(grep version /app/config/q2lms.toml | cut -d'"' -f2)
Data Size: $(du -sh /app/data | cut -f1)
Configuration Files: $(ls /app/config | wc -l)
Log Files Included: $(find /app/logs -name "*.log" -mtime -7 | wc -l)

Backup Contents:
- Application data directory
- Configuration files
- Recent log files (7 days)
- Current database state
- System metadata

Restore Instructions:
1. Stop Q2LMS application
2. Restore data: cp -r $BACKUP_DIR/data/* /app/data/
3. Restore config: cp -r $BACKUP_DIR/config/* /app/config/
4. Restart application
5. Verify functionality
EOF

# Compress backup
log "Compressing backup"
cd "$BACKUP_ROOT"
tar -czf "q2lms_backup_$DATE.tar.gz" "$DATE/"

# Cleanup old backups (keep 30 days)
log "Cleaning up old backups"
find "$BACKUP_ROOT" -name "q2lms_backup_*.tar.gz" -mtime +30 -delete
find "$BACKUP_ROOT" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \;

# Backup verification
if [ -f "$BACKUP_ROOT/q2lms_backup_$DATE.tar.gz" ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_ROOT/q2lms_backup_$DATE.tar.gz" | cut -f1)
    log "Backup completed successfully: q2lms_backup_$DATE.tar.gz ($BACKUP_SIZE)"
else
    log "ERROR: Backup failed - archive not created"
    exit 1
fi

log "Backup process completed"
```

### Disaster Recovery Procedures
```bash
#!/bin/bash
# disaster_recovery.sh - Q2LMS disaster recovery

BACKUP_ROOT="/backups/q2lms"
RESTORE_POINT="$1"

if [ -z "$RESTORE_POINT" ]; then
    echo "Usage: $0 <backup_date_time>"
    echo "Available backups:"
    ls -la "$BACKUP_ROOT"/q2lms_backup_*.tar.gz
    exit 1
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Q2LMS disaster recovery"
log "Restore point: $RESTORE_POINT"

# Stop application
log "Stopping Q2LMS application"
docker-compose down || systemctl stop q2lms

# Backup current state before restore
CURRENT_BACKUP="/tmp/q2lms_pre_restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CURRENT_BACKUP"
cp -r /app/data "$CURRENT_BACKUP/" 2>/dev/null
cp -r /app/config "$CURRENT_BACKUP/" 2>/dev/null
log "Current state backed up to $CURRENT_BACKUP"

# Extract backup
BACKUP_FILE="$BACKUP_ROOT/q2lms_backup_$RESTORE_POINT.tar.gz"
if [ ! -f "$BACKUP_FILE" ]; then
    log "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

log "Extracting backup: $BACKUP_FILE"
cd "$BACKUP_ROOT"
tar -xzf "q2lms_backup_$RESTORE_POINT.tar.gz"

# Restore data
log "Restoring application data"
rm -rf /app/data/*
cp -r "$BACKUP_ROOT/$RESTORE_POINT/data/"* /app/data/

# Restore configuration
log "Restoring configuration"
cp -r "$BACKUP_ROOT/$RESTORE_POINT/config/"* /app/config/

# Set proper permissions
log "Setting file permissions"
chown -R q2lms:q2lms /app/data /app/config
chmod -R 755 /app/data /app/config

# Start application
log "Starting Q2LMS application"
docker-compose up -d || systemctl start q2lms

# Wait for application to start
sleep 30

# Verify restoration
log "Verifying restoration"
python3 -c "
import sys
sys.path.append('/app')
try:
    from health_check import check_application_health
    health = check_application_health()
    if health['status'] == 'healthy':
        print('✅ Application restored successfully')
    else:
        print('⚠️ Application started but health check shows issues')
        print(health)
except Exception as e:
    print(f'❌ Restoration verification failed: {e}')
"

log "Disaster recovery completed"
log "Verify application functionality at your Q2LMS URL"
```

### Backup Monitoring
```python
# backup_monitor.py
import os
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

class BackupMonitor:
    def __init__(self, backup_dir="/backups/q2lms"):
        self.backup_dir = backup_dir
        self.max_backup_age_hours = 24
        self.min_backup_size_mb = 1
    
    def check_backup_health(self):
        """Check backup health and alert if issues found"""
        issues = []
        
        # Check if backup directory exists
        if not os.path.exists(self.backup_dir):
            issues.append("Backup directory not found")
            return {'status': 'critical', 'issues': issues}
        
        # Find latest backup
        backup_files = [f for f in os.listdir(self.backup_dir) 
                       if f.startswith('q2lms_backup_') and f.endswith('.tar.gz')]
        
        if not backup_files:
            issues.append("No backup files found")
            return {'status': 'critical', 'issues': issues}
        
        # Check latest backup age
        latest_backup = max(backup_files)
        backup_path = os.path.join(self.backup_dir, latest_backup)
        backup_time = datetime.fromtimestamp(os.path.getmtime(backup_path))
        age_hours = (datetime.now() - backup_time).total_seconds() / 3600
        
        if age_hours > self.max_backup_age_hours:
            issues.append(f"Latest backup is {age_hours:.1f} hours old")
        
        # Check backup size
        backup_size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        if backup_size_mb < self.min_backup_size_mb:
            issues.append(f"Backup size ({backup_size_mb:.1f}MB) seems too small")
        
        # Determine status
        if issues:
            status = 'warning' if age_hours < 48 else 'critical'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'latest_backup': latest_backup,
            'backup_age_hours': age_hours,
            'backup_size_mb': backup_size_mb,
            'total_backups': len(backup_files),
            'issues': issues
        }
    
    def send_alert(self, backup_status):
        """Send email alert for backup issues"""
        if backup_status['status'] == 'healthy':
            return
        
        # Email configuration (customize for your environment)
        smtp_server = os.getenv('SMTP_SERVER', 'localhost')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        email_user = os.getenv('EMAIL_USER', 'alerts@your-institution.edu')
        email_password = os.getenv('EMAIL_PASSWORD', '')
        alert_recipients = os.getenv('ALERT_RECIPIENTS', 'admin@your-institution.edu').split(',')
        
        subject = f"Q2LMS Backup Alert - {backup_status['status'].upper()}"
        
        body = f"""
Q2LMS Backup Monitoring Alert

Status: {backup_status['status'].upper()}
Timestamp: {datetime.now().isoformat()}

Backup Details:
- Latest Backup: {backup_status.get('latest_backup', 'N/A')}
- Age: {backup_status.get('backup_age_hours', 0):.1f} hours
- Size: {backup_status.get('backup_size_mb', 0):.1f} MB
- Total Backups: {backup_status.get('total_backups', 0)}

Issues Found:
{chr(10).join(f"- {issue}" for issue in backup_status['issues'])}

Action Required:
1. Check backup system functionality
2. Verify disk space in backup directory
3. Review backup logs for errors
4. Consider manual backup if needed

Backup Directory: {self.backup_dir}
        """
        
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = email_user
            msg['To'] = ', '.join(alert_recipients)
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.send_message(msg)
            
            print(f"Alert sent to {alert_recipients}")
            
        except Exception as e:
            print(f"Failed to send alert: {e}")

# Usage in cron job
if __name__ == "__main__":
    monitor = BackupMonitor()
    status = monitor.check_backup_health()
    print(json.dumps(status, indent=2))
    monitor.send_alert(status)
```

---

## Security Considerations

### Production Security Checklist
```bash
# Security Configuration Checklist

# 1. Network Security
- [ ] Application runs behind reverse proxy (nginx/Apache)
- [ ] HTTPS enabled with valid SSL certificates
- [ ] Firewall configured to block unnecessary ports
- [ ] VPN access for administrative functions

# 2. Application Security
- [ ] Debug mode disabled in production
- [ ] Secure headers configured in reverse proxy
- [ ] File upload restrictions enforced
- [ ] Input validation on all user inputs

# 3. System Security
- [ ] Application runs as non-root user
- [ ] File permissions properly configured
- [ ] Regular security updates applied
- [ ] System monitoring and logging enabled

# 4. Data Security
- [ ] Sensitive data encrypted at rest
- [ ] Backup encryption enabled
- [ ] Access logs maintained
- [ ] Data retention policies implemented
```

### SSL/TLS Configuration
```nginx
# nginx-ssl.conf - Production SSL configuration
server {
    listen 80;
    server_name q2lms.your-institution.edu;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name q2lms.your-institution.edu;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/q2lms.crt;
    ssl_certificate_key /etc/nginx/ssl/q2lms.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy no-referrer-when-downgrade always;

    # File upload limits
    client_max_body_size 200M;

    location / {
        proxy_pass http://q2lms:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Security scanning endpoint
    location /_health {
        proxy_pass http://q2lms:8501/_stcore/health;
        access_log off;
    }
}
```

---

## Performance Optimization

### Production Performance Tuning
```toml
# config/performance.toml
[streamlit]
# Streamlit-specific optimizations
maxUploadSize = 200  # MB
maxMessageSize = 200  # MB
enableCORS = false
enableXsrfProtection = true

[caching]
# Enable aggressive caching for production
enable_data_caching = true
cache_ttl_seconds = 300
max_cache_entries = 1000

[concurrency]
# Handle multiple users
max_concurrent_sessions = 50
session_timeout_minutes = 60
memory_cleanup_interval = 300

[database]
# Optimize database operations
enable_query_caching = true
batch_size = 100
connection_pool_size = 10
```

### Load Testing
```python
# load_test.py - Q2LMS load testing
import asyncio
import aiohttp
import time
from datetime import datetime

async def load_test_q2lms():
    """Simulate concurrent user load on Q2LMS"""
    
    base_url = "http://localhost:8501"
    concurrent_users = 20
    test_duration = 300  # 5 minutes
    
    async def simulate_user_session(session, user_id):
        """Simulate a typical user session"""
        start_time = time.time()
        requests_made = 0
        
        while time.time() - start_time < test_duration:
            try:
                # Simulate main page load
                async with session.get(f"{base_url}/") as response:
                    await response.text()
                    requests_made += 1
                
                # Simulate health check
                async with session.get(f"{base_url}/_stcore/health") as response:
                    await response.text()
                    requests_made += 1
                
                # Wait between requests
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"User {user_id} error: {e}")
            
        return {
            'user_id': user_id,
            'requests_made': requests_made,
            'duration': time.time() - start_time
        }
    
    # Run concurrent user sessions
    async with aiohttp.ClientSession() as session:
        print(f"Starting load test with {concurrent_users} concurrent users")
        print(f"Test duration: {test_duration} seconds")
        
        tasks = [
            simulate_user_session(session, i) 
            for i in range(concurrent_users)
        ]
        
        results = await asyncio.gather(*tasks)
    
    # Analyze results
    total_requests = sum(r['requests_made'] for r in results)
    avg_requests_per_user = total_requests / len(results)
    requests_per_second = total_requests / test_duration
    
    print(f"""
Load Test Results:
==================
Total Requests: {total_requests}
Requests per User: {avg_requests_per_user:.1f}
Requests per Second: {requests_per_second:.1f}
Test Duration: {test_duration} seconds
Concurrent Users: {concurrent_users}

Performance Assessment: {'✅ GOOD' if requests_per_second > 10 else '⚠️ NEEDS OPTIMIZATION'}
    """)

if __name__ == "__main__":
    asyncio.run(load_test_q2lms())
```

---

## Appendix

### Quick Reference Commands
```bash
# Development
python -m streamlit run streamlit_app.py
pip install -r requirements.txt

# Docker
docker-compose up -d
docker-compose logs -f q2lms
docker-compose restart q2lms

# Kubernetes
kubectl apply -f k8s/
kubectl get pods -n q2lms
kubectl logs -f deployment/q2lms -n q2lms

# Maintenance
bash backup.sh
bash maintenance.sh
python3 backup_monitor.py

# Monitoring
curl http://localhost:8501/_stcore/health
python3 health_check.py
tail -f /app/logs/q2lms.log
```

### Support Resources
- **Documentation**: Complete guides available in repository `/docs` folder
- **Issues**: Report issues at [GitHub Issues](https://github.com/aknoesen/q2lms/issues)
- **Discussions**: Community support at [GitHub Discussions](https://github.com/aknoesen/q2lms/discussions)
- **Updates**: Follow repository for latest releases and security updates

### Version Compatibility
| Q2LMS Version | Python | Streamlit | Pandas | Status |
|---------------|--------|-----------|--------|---------|
| 1.0.x | 3.8+ | 1.20.0+ | 1.5.0+ | Current |
| 0.9.x | 3.8+ | 1.18.0+ | 1.4.0+ | Legacy Support |

---

**Built for educators by educators** - Q2LMS provides robust, scalable question database management for educational institutions of all sizes.