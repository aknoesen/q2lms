#!/bin/bash
# backup_q2lms.sh - Automated backup script for Q2LMS

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/q2lms}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="q2lms_backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_DIR/backup.log"
}

error_exit() {
    log "ERROR: $1"
    if [[ -n "$NOTIFICATION_EMAIL" ]]; then
        echo "Q2LMS backup failed: $1" | mail -s "Q2LMS Backup Failed" "$NOTIFICATION_EMAIL"
    fi
    exit 1
}

log "Starting Q2LMS backup: $BACKUP_NAME"

# Create backup structure
mkdir -p "$BACKUP_PATH"/{data,config,logs,database}

# Backup application data
log "Backing up application data..."
if [[ -d "/app/data" ]]; then
    cp -r /app/data/* "$BACKUP_PATH/data/" || error_exit "Failed to backup application data"
fi

# Backup configuration files
log "Backing up configuration..."
if [[ -f "/app/.streamlit/config.toml" ]]; then
    cp /app/.streamlit/config.toml "$BACKUP_PATH/config/"
fi
if [[ -f "/app/.env" ]]; then
    cp /app/.env "$BACKUP_PATH/config/"
fi

# Backup logs
log "Backing up logs..."
if [[ -d "/app/logs" ]]; then
    cp -r /app/logs/* "$BACKUP_PATH/logs/" 2>/dev/null || true
fi

# Backup database (if using external database)
if [[ -n "${DATABASE_URL:-}" ]]; then
    log "Backing up database..."
    pg_dump "$DATABASE_URL" > "$BACKUP_PATH/database/dump.sql" || error_exit "Database backup failed"
fi

# Create backup metadata
cat > "$BACKUP_PATH/metadata.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "created_at": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "version": "$(cat /app/VERSION 2>/dev/null || echo 'unknown')",
    "backup_type": "full",
    "retention_days": $RETENTION_DAYS
}
EOF

# Compress backup
log "Compressing backup..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME" || error_exit "Compression failed"

# Encrypt backup if key provided
if [[ -n "$ENCRYPTION_KEY" ]]; then
    log "Encrypting backup..."
    openssl enc -aes-256-cbc -salt -in "${BACKUP_NAME}.tar.gz" -out "${BACKUP_NAME}.tar.gz.enc" -k "$ENCRYPTION_KEY" || error_exit "Encryption failed"
    rm "${BACKUP_NAME}.tar.gz"
    BACKUP_FILE="${BACKUP_NAME}.tar.gz.enc"
else
    BACKUP_FILE="${BACKUP_NAME}.tar.gz"
fi

# Upload to S3 if configured
if [[ -n "$S3_BUCKET" ]]; then
    log "Uploading to S3..."
    aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/q2lms-backups/" || error_exit "S3 upload failed"
fi

# Clean up old backups
log "Cleaning up old backups..."
find "$BACKUP_DIR" -name "q2lms_backup_*" -type f -mtime +$RETENTION_DAYS -delete || true
rm -rf "$BACKUP_PATH"

# Calculate backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

log "Backup completed successfully: $BACKUP_FILE ($BACKUP_SIZE)"

# Send success notification
if [[ -n "$NOTIFICATION_EMAIL" ]]; then
    echo "Q2LMS backup completed successfully. File: $BACKUP_FILE, Size: $BACKUP_SIZE" | \
        mail -s "Q2LMS Backup Successful" "$NOTIFICATION_EMAIL"
fi
```

### Recovery Procedures

```bash
#!/bin/bash
# restore_q2lms.sh - Recovery script for Q2LMS

set -euo pipefail

BACKUP_FILE="$1"
RESTORE_DIR="${RESTORE_DIR:-/tmp/q2lms_restore}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"

usage() {
    echo "Usage: $0 <backup_file> [options]"
    echo "Options:"
    echo "  --decrypt-key KEY    Decryption key for encrypted backups"
    echo "  --restore-dir DIR    Temporary restore directory"
    echo "  --dry-run           Show what would be restored without doing it"
    echo "  --selective TYPE     Restore only specific components (data|config|logs|database)"
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Parse arguments
DRY_RUN=false
SELECTIVE=""

while [[ $# -gt 1 ]]; do
    case $1 in
        --decrypt-key)
            ENCRYPTION_KEY="$2"
            shift 2
            ;;
        --restore-dir)
            RESTORE_DIR="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --selective)
            SELECTIVE="$2"
            shift 2
            ;;
        *)
            usage
            ;;
    esac
done

if [[ -z "$BACKUP_FILE" ]]; then
    usage
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    log "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

log "Starting Q2LMS restore from: $BACKUP_FILE"

# Create restore directory
mkdir -p "$RESTORE_DIR"
cd "$RESTORE_DIR"

# Decrypt if needed
if [[ "$BACKUP_FILE" == *.enc ]]; then
    if [[ -z "$ENCRYPTION_KEY" ]]; then
        log "ERROR: Backup is encrypted but no decryption key provided"
        exit 1
    fi
    
    log "Decrypting backup..."
    openssl enc -aes-256-cbc -d -in "$BACKUP_FILE" -out "backup.tar.gz" -k "$ENCRYPTION_KEY"
    EXTRACT_FILE="backup.tar.gz"
else
    EXTRACT_FILE="$BACKUP_FILE"
fi

# Extract backup
log "Extracting backup..."
tar -xzf "$EXTRACT_FILE"

# Find extracted directory
BACKUP_DIR=$(find . -name "q2lms_backup_*" -type d | head -1)
if [[ -z "$BACKUP_DIR" ]]; then
    log "ERROR: Could not find backup directory in archive"
    exit 1
fi

# Read metadata
if [[ -f "$BACKUP_DIR/metadata.json" ]]; then
    log "Backup metadata:"
    cat "$BACKUP_DIR/metadata.json"
else
    log "WARNING: No metadata file found"
fi

# Restore functions
restore_data() {
    if [[ -d "$BACKUP_DIR/data" ]] && [[ -n "$(ls -A "$BACKUP_DIR/data" 2>/dev/null)" ]]; then
        log "Restoring application data..."
        if [[ "$DRY_RUN" == "false" ]]; then
            mkdir -p /app/data
            cp -r "$BACKUP_DIR/data/"* /app/data/
        else
            log "DRY RUN: Would restore $(du -sh "$BACKUP_DIR/data" | cut -f1) of application data"
        fi
    fi
}

restore_config() {
    if [[ -d "$BACKUP_DIR/config" ]] && [[ -n "$(ls -A "$BACKUP_DIR/config" 2>/dev/null)" ]]; then
        log "Restoring configuration..."
        if [[ "$DRY_RUN" == "false" ]]; then
            mkdir -p /app/.streamlit
            [[ -f "$BACKUP_DIR/config/config.toml" ]] && cp "$BACKUP_DIR/config/config.toml" /app/.streamlit/
            [[ -f "$BACKUP_DIR/config/.env" ]] && cp "$BACKUP_DIR/config/.env" /app/
        else
            log "DRY RUN: Would restore configuration files"
        fi
    fi
}

restore_logs() {
    if [[ -d "$BACKUP_DIR/logs" ]] && [[ -n "$(ls -A "$BACKUP_DIR/logs" 2>/dev/null)" ]]; then
        log "Restoring logs..."
        if [[ "$DRY_RUN" == "false" ]]; then
            mkdir -p /app/logs
            cp -r "$BACKUP_DIR/logs/"* /app/logs/
        else
            log "DRY RUN: Would restore $(du -sh "$BACKUP_DIR/logs" | cut -f1) of logs"
        fi
    fi
}

restore_database() {
    if [[ -f "$BACKUP_DIR/database/dump.sql" ]]; then
        log "Restoring database..."
        if [[ "$DRY_RUN" == "false" ]]; then
            if [[ -n "${DATABASE_URL:-}" ]]; then
                psql "$DATABASE_URL" < "$BACKUP_DIR/database/dump.sql"
            else
                log "WARNING: DATABASE_URL not set, skipping database restore"
            fi
        else
            log "DRY RUN: Would restore database from SQL dump"
        fi
    fi
}

# Perform selective or full restore
case "$SELECTIVE" in
    "data")
        restore_data
        ;;
    "config")
        restore_config
        ;;
    "logs")
        restore_logs
        ;;
    "database")
        restore_database
        ;;
    "")
        # Full restore
        restore_data
        restore_config
        restore_logs
        restore_database
        ;;
    *)
        log "ERROR: Invalid selective restore type: $SELECTIVE"
        exit 1
        ;;
esac

# Cleanup
if [[ "$DRY_RUN" == "false" ]]; then
    log "Cleaning up temporary files..."
    rm -rf "$RESTORE_DIR"
    
    log "Restore completed successfully!"
    log "NOTE: You may need to restart the Q2LMS application for changes to take effect"
else
    log "DRY RUN completed - no changes made"
fi
```

### Disaster Recovery Plan

```yaml
# disaster_recovery.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: disaster-recovery-plan
  namespace: q2lms
data:
  recovery_plan.md: |
    # Q2LMS Disaster Recovery Plan
    
    ## Recovery Time Objectives (RTO)
    - **Critical System Failure**: 4 hours
    - **Data Corruption**: 2 hours  
    - **Regional Outage**: 8 hours
    - **Complete Infrastructure Loss**: 24 hours
    
    ## Recovery Point Objectives (RPO)
    - **Database**: 15 minutes (continuous backup)
    - **Application Data**: 1 hour (automated backups)
    - **Configuration**: 24 hours (daily backups)
    
    ## Recovery Procedures
    
    ### 1. Application Failure
    ```bash
    # Check pod status
    kubectl get pods -n q2lms
    
    # Restart failed pods
    kubectl rollout restart deployment/q2lms -n q2lms
    
    # Scale up if needed
    kubectl scale deployment/q2lms --replicas=5 -n q2lms
    ```
    
    ### 2. Data Corruption
    ```bash
    # Stop application
    kubectl scale deployment/q2lms --replicas=0 -n q2lms
    
    # Restore from backup
    ./restore_q2lms.sh /backups/latest_backup.tar.gz
    
    # Restart application
    kubectl scale deployment/q2lms --replicas=3 -n q2lms
    ```
    
    ### 3. Regional Outage
    ```bash
    # Switch to backup region
    kubectl config use-context backup-region
    
    # Deploy Q2LMS in backup region
    helm install q2lms-dr ./helm/q2lms -n q2lms-dr
    
    # Update DNS to point to backup region
    # (Manual process - update DNS records)
    ```
    
    ## Emergency Contacts
    - Primary Admin: admin@institution.edu
    - Secondary Admin: backup-admin@institution.edu
    - Infrastructure Team: infra@institution.edu
    - Emergency Hotline: +1-555-EMERGENCY

---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-job
  namespace: q2lms
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: q2lms-backup:latest
            command:
            - /bin/bash
            - -c
            - |
              # Perform backup
              /scripts/backup_q2lms.sh
              
              # Upload to multiple locations
              aws s3 sync /var/backups/q2lms s3://primary-backup-bucket/q2lms/
              aws s3 sync /var/backups/q2lms s3://secondary-backup-bucket/q2lms/ --region us-west-2
            env:
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: backup-secrets
                  key: aws_access_key_id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: backup-secrets
                  key: aws_secret_access_key
            volumeMounts:
            - name: data-volume
              mountPath: /app/data
              readOnly: true
            - name: backup-volume
              mountPath: /var/backups
          volumes:
          - name: data-volume
            persistentVolumeClaim:
              claimName: q2lms-data
          - name: backup-volume
            persistentVolumeClaim:
              claimName: backup-storage
          restartPolicy: OnFailure
```

---

## Troubleshooting

### Common Issues and Solutions

#### Performance Issues

**Issue**: Slow application response times
```bash
# Check resource usage
kubectl top pods -n q2lms
kubectl describe pod <pod-name> -n q2lms

# Check logs for bottlenecks
kubectl logs -f deployment/q2lms -n q2lms | grep -E "(ERROR|WARN|slow)"

# Scale up if needed
kubectl scale deployment/q2lms --replicas=5 -n q2lms
```

**Issue**: Memory leaks
```python
# Add memory monitoring to application
import psutil
import gc

def monitor_memory():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    if memory_mb > 1500:  # Alert if over 1.5GB
        gc.collect()  # Force garbage collection
        logging.warning(f"High memory usage: {memory_mb:.1f} MB")
```

#### Database Issues

**Issue**: Database connection failures
```bash
# Check database status
kubectl get pods -l app=postgres -n q2lms

# Check connection from application pod
kubectl exec -it deployment/q2lms -n q2lms -- bash
psql $DATABASE_URL -c "SELECT 1;"

# Restart database if needed
kubectl rollout restart deployment/postgres -n q2lms
```

**Issue**: Database corruption
```bash
# Stop applications using database
kubectl scale deployment/q2lms --replicas=0 -n q2lms

# Restore from backup
kubectl exec -it postgres-pod -- bash
pg_restore -d q2lms /backups/latest_dump.sql

# Restart applications
kubectl scale deployment/q2lms --replicas=3 -n q2lms
```

#### Network Issues

**Issue**: External service connectivity
```bash
# Test network connectivity
kubectl exec -it deployment/q2lms -n q2lms -- bash
curl -I https://external-service.com
nslookup external-service.com

# Check network policies
kubectl get networkpolicies -n q2lms
kubectl describe networkpolicy <policy-name> -n q2lms
```

**Issue**: Load balancer issues
```bash
# Check ingress status
kubectl get ingress -n q2lms
kubectl describe ingress q2lms-ingress -n q2lms

# Check ingress controller logs
kubectl logs -f deployment/nginx-ingress-controller -n ingress-nginx
```

### Debugging Tools

```python
# debug_tools.py
import streamlit as st
import sys
import traceback
import logging
from datetime import datetime
import psutil
import json

class DebugManager:
    """Debug tools for Q2LMS"""
    
    def __init__(self):
        self.debug_enabled = st.sidebar.checkbox("🐛 Enable Debug Mode", value=False)
    
    def debug_panel(self):
        """Show debug information panel"""
        if not self.debug_enabled:
            return
        
        with st.sidebar.expander("🔧 Debug Info", expanded=False):
            st.markdown("### System Info")
            st.code(f"""
Python Version: {sys.version}
Streamlit Version: {st.__version__}
Memory Usage: {psutil.virtual_memory().percent:.1f}%
CPU Usage: {psutil.cpu_percent():.1f}%
            """)
            
            st.markdown("### Session State")
            session_keys = list(st.session_state.keys())
            selected_keys = st.multiselect("Session Keys", session_keys, default=[])
            
            for key in selected_keys:
                with st.expander(f"🔑 {key}"):
                    try:
                        value = st.session_state[key]
                        if isinstance(value, (dict, list)):
                            st.json(value)
                        else:
                            st.code(str(value))
                    except Exception as e:
                        st.error(f"Error displaying {key}: {str(e)}")
            
            if st.button("💾 Export Debug Info"):
                debug_data = self.collect_debug_info()
                st.download_button(
                    label="📥 Download Debug Report",
                    data=json.dumps(debug_data, indent=2, default=str),
                    file_name=f"q2lms_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    def collect_debug_info(self) -> dict:
        """Collect comprehensive debug information"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'python_version': sys.version,
                'platform': sys.platform,
                'memory_percent': psutil.virtual_memory().percent,
                'cpu_percent': psutil.cpu_percent(),
                'disk_usage': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free
                }
            },
            'application': {
                'streamlit_version': st.__version__,
                'session_state_keys': list(st.session_state.keys()),
                'has_database': 'df' in st.session_state,
                'database_size': len(st.session_state.get('df', [])),
            },
            'environment': dict(os.environ),
            'recent_errors': self.get_recent_errors()
        }
    
    def get_recent_errors(self) -> list:
        """Get recent error logs"""
        try:
            with open('/app/logs/q2lms-errors.log', 'r') as f:
                lines = f.readlines()
                return lines[-50:]  # Last 50 error lines
        except Exception:
            return ["No error log available"]
    
    def exception_handler(self, func):
        """Decorator for exception handling with debug info"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self.debug_enabled:
                    st.error(f"Exception in {func.__name__}: {str(e)}")
                    st.code(traceback.format_exc())
                else:
                    st.error(f"An error occurred. Enable debug mode for details.")
                
                # Log the error
                logging.error(f"Exception in {func.__name__}: {str(e)}", exc_info=True)
                return None
        return wrapper

# Initialize debug manager
debug_manager = DebugManager()

# Usage in application
@debug_manager.exception_handler
def problematic_function():
    """Function that might have issues"""
    # Your code here
    pass
```

### Log Analysis Tools

```bash
#!/bin/bash
# log_analyzer.sh - Analyze Q2LMS logs for issues

LOG_DIR="${1:-/app/logs}"
OUTPUT_DIR="${2:-/tmp/log_analysis}"

mkdir -p "$OUTPUT_DIR"

echo "Analyzing Q2LMS logs in $LOG_DIR..."

# Error analysis
echo "=== ERROR ANALYSIS ===" > "$OUTPUT_DIR/error_summary.txt"
grep -h "ERROR" "$LOG_DIR"/*.log | \
    awk '{print $5}' | sort | uniq -c | sort -nr >> "$OUTPUT_DIR/error_summary.txt"

# Performance analysis
echo "=== SLOW REQUESTS ===" > "$OUTPUT_DIR/performance_issues.txt"
grep -h "slow\|timeout\|Response time" "$LOG_DIR"/*.log >> "$OUTPUT_DIR/performance_issues.txt"

# User activity analysis
echo "=== USER ACTIVITY ===" > "$OUTPUT_DIR/user_activity.txt"
grep -h "user_id" "$LOG_DIR"/*.log | \
    jq -r '.user_id' 2>/dev/null | sort | uniq -c | sort -nr >> "$OUTPUT_DIR/user_activity.txt"

# Memory usage trends
echo "=== MEMORY USAGE ===" > "$OUTPUT_DIR/memory_trends.txt"
grep -h "memory" "$LOG_DIR"/*.log | \
    grep -o "memory.*[0-9]*\.*[0-9]*%" | sort >> "$OUTPUT_DIR/memory_trends.txt"

# Generate summary report
cat > "$OUTPUT_DIR/analysis_report.md" << EOF
# Q2LMS Log Analysis Report

Generated: $(date)
Log Directory: $LOG_DIR

## Summary
- Total log files analyzed: $(ls -1 "$LOG_DIR"/*.log 2>/dev/null | wc -l)
- Analysis period: $(head -1 "$LOG_DIR"/*.log 2>/dev/null | grep -o '[0-9-]* [0-9:]*' | head -1) to $(tail -1 "$LOG_DIR"/*.log 2>/dev/null | grep -o '[0-9-]* [0-9:]*' | tail -1)

## Top Errors
$(head -10 "$OUTPUT_DIR/error_summary.txt")

## Performance Issues
$(wc -l < "$OUTPUT_DIR/performance_issues.txt") slow requests detected

## Active Users
$(wc -l < "$OUTPUT_DIR/user_activity.txt") unique users detected

## Recommendations
- Review top errors and implement fixes
- Monitor memory usage trends
- Consider scaling if performance issues persist
EOF

echo "Analysis complete. Results in $OUTPUT_DIR/"
```

---

## Conclusion

This comprehensive deployment guide provides everything needed to deploy Q2LMS from development through enterprise-scale production environments. Key deployment patterns include:

### Deployment Tiers
- **Development**: Local Python environment for rapid iteration
- **Department**: Streamlit Cloud or Docker for team sharing
- **Institution**: Cloud platforms with high availability and security
- **Enterprise**: Kubernetes with full monitoring, backup, and disaster recovery

### Critical Success Factors
1. **Security First**: Implement proper authentication, encryption, and access controls
2. **Performance Optimization**: Use caching, load balancing, and resource monitoring
3. **Reliability**: Automated backups, health checks, and disaster recovery procedures
4. **Monitoring**: Comprehensive logging, alerting, and performance tracking
5. **Scalability**: Container orchestration and auto-scaling capabilities

### Production Readiness Checklist
- [ ] SSL/TLS encryption configured
- [ ] Authentication and authorization implemented
- [ ] Automated backups scheduled
- [ ] Monitoring and alerting active
- [ ] Disaster recovery plan tested
- [ ] Performance optimization applied
- [ ] Security hardening completed
- [ ] Documentation updated
- [ ] Team training conducted

This guide ensures Q2LMS can be deployed confidently in any educational environment, from individual instructors to large multi-institutional deployments, with enterprise-grade reliability and security.

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Compatibility**: Q2LMS Phase 3D and later  
**Deployment Guide Version**: 1.0    def set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Set cached value"""
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, pickle.dumps(value))
                return
            except Exception:
                pass
        
        # Fallback to session state
        st.session_state[f"cache_{key}"] = value
    
    def cached_function(self, ttl: int = 3600):
        """Decorator for caching function results"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = self.cache_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get_cache(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set_cache(cache_key, result, ttl)
                return result
            
            return wrapper
        return decorator

# Initialize cache manager
cache_manager = CacheManager(
    use_redis=os.getenv('REDIS_URL') is not None,
    redis_url=os.getenv('REDIS_URL')
)

# Usage examples
@cache_manager.cached_function(ttl=1800)  # 30 minutes
def load_large_database(file_hash: str):
    """Cached database loading"""
    # Expensive database processing
    pass

@cache_manager.cached_function(ttl=300)   # 5 minutes
def generate_analytics_charts(data_hash: str):
    """Cached chart generation"""
    # Expensive chart generation
    pass
```

### Database Optimization

```python
# database_optimization.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import sqlite3
import asyncio
import concurrent.futures

class DatabaseOptimizer:
    """Database performance optimization"""
    
    def __init__(self):
        self.chunk_size = 1000
        self.max_workers = 4
    
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage"""
        optimized_df = df.copy()
        
        # Optimize string columns
        string_columns = optimized_df.select_dtypes(include=['object']).columns
        for col in string_columns:
            if optimized_df[col].nunique() / len(optimized_df) < 0.5:
                optimized_df[col] = optimized_df[col].astype('category')
        
        # Optimize numeric columns
        numeric_columns = optimized_df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            col_min = optimized_df[col].min()
            col_max = optimized_df[col].max()
            
            if optimized_df[col].dtype == 'int64':
                if col_min >= 0:
                    if col_max < 255:
                        optimized_df[col] = optimized_df[col].astype('uint8')
                    elif col_max < 65535:
                        optimized_df[col] = optimized_df[col].astype('uint16')
                    elif col_max < 4294967295:
                        optimized_df[col] = optimized_df[col].astype('uint32')
                else:
                    if col_min > -128 and col_max < 127:
                        optimized_df[col] = optimized_df[col].astype('int8')
                    elif col_min > -32768 and col_max < 32767:
                        optimized_df[col] = optimized_df[col].astype('int16')
                    elif col_min > -2147483648 and col_max < 2147483647:
                        optimized_df[col] = optimized_df[col].astype('int32')
        
        return optimized_df
    
    def parallel_processing(self, data: List[Any], process_func: callable) -> List[Any]:
        """Process data in parallel"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Split data into chunks
            chunks = [data[i:i + self.chunk_size] for i in range(0, len(data), self.chunk_size)]
            
            # Process chunks in parallel
            futures = [executor.submit(process_func, chunk) for chunk in chunks]
            results = []
            
            for future in concurrent.futures.as_completed(futures):
                results.extend(future.result())
        
        return results
    
    async def async_data_processing(self, data_sources: List[str]) -> List[pd.DataFrame]:
        """Asynchronous data processing"""
        async def load_data_source(source: str) -> pd.DataFrame:
            # Simulate async data loading
            await asyncio.sleep(0.1)
            return pd.read_json(source)
        
        tasks = [load_data_source(source) for source in data_sources]
        return await asyncio.gather(*tasks)

class MemoryManager:
    """Memory usage optimization"""
    
    def __init__(self, max_memory_mb: int = 2048):
        self.max_memory_mb = max_memory_mb
        self.current_usage = 0
    
    def check_memory_usage(self) -> float:
        """Check current memory usage"""
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        return memory_mb
    
    def cleanup_large_objects(self):
        """Clean up large objects from session state"""
        import gc
        
        # Clear large cached objects
        keys_to_remove = []
        for key, value in st.session_state.items():
            if isinstance(value, pd.DataFrame) and len(value) > 10000:
                keys_to_remove.append(key)
            elif isinstance(value, list) and len(value) > 5000:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            if key not in ['df', 'original_questions']:  # Keep essential data
                del st.session_state[key]
        
        # Force garbage collection
        gc.collect()
    
    def memory_efficient_processing(self, data: pd.DataFrame, process_func: callable) -> pd.DataFrame:
        """Process large DataFrames in memory-efficient chunks"""
        chunk_size = min(1000, len(data) // 10)
        processed_chunks = []
        
        for i in range(0, len(data), chunk_size):
            chunk = data.iloc[i:i + chunk_size]
            processed_chunk = process_func(chunk)
            processed_chunks.append(processed_chunk)
            
            # Monitor memory usage
            if self.check_memory_usage() > self.max_memory_mb * 0.8:
                self.cleanup_large_objects()
        
        return pd.concat(processed_chunks, ignore_index=True)
```

### Load Balancing Configuration

```yaml
# docker-compose.loadbalancer.yml
version: '3.8'

services:
  nginx-lb:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - q2lms-1
      - q2lms-2
      - q2lms-3
    restart: always

  q2lms-1:
    build: .
    environment:
      - Q2LMS_ENV=production
      - Q2LMS_INSTANCE_ID=1
    volumes:
      - shared-data:/app/data
    restart: always

  q2lms-2:
    build: .
    environment:
      - Q2LMS_ENV=production
      - Q2LMS_INSTANCE_ID=2
    volumes:
      - shared-data:/app/data
    restart: always

  q2lms-3:
    build: .
    environment:
      - Q2LMS_ENV=production
      - Q2LMS_INSTANCE_ID=3
    volumes:
      - shared-data:/app/data
    restart: always

  redis:
    image: redis:alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data

volumes:
  shared-data:
  redis-data:
```

```nginx
# nginx-lb.conf
events {
    worker_connections 1024;
}

http {
    upstream q2lms_backend {
        least_conn;
        server q2lms-1:8501 max_fails=3 fail_timeout=30s;
        server q2lms-2:8501 max_fails=3 fail_timeout=30s;
        server q2lms-3:8501 max_fails=3 fail_timeout=30s;
    }

    # Health check
    upstream q2lms_health {
        server q2lms-1:8501;
        server q2lms-2:8501;
        server q2lms-3:8501;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=2r/s;

    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name q2lms.yourdomain.com;

        ssl_certificate /etc/ssl/certificate.crt;
        ssl_certificate_key /etc/ssl/private.key;

        # Health check endpoint
        location /_health {
            proxy_pass http://q2lms_health/_stcore/health;
            access_log off;
        }

        # Upload endpoints with special rate limiting
        location /upload {
            limit_req zone=upload_limit burst=5 nodelay;
            proxy_pass http://q2lms_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            client_max_body_size 500M;
            proxy_read_timeout 300s;
            proxy_send_timeout 300s;
        }

        # Regular application traffic
        location / {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://q2lms_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;

            # Sticky sessions (if needed)
            proxy_set_header X-Instance-ID $upstream_addr;
        }

        # Static file caching
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            proxy_pass http://q2lms_backend;
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }
}
```

---

## Monitoring and Maintenance

### Application Monitoring

```python
# monitoring.py
import time
import logging
import psutil
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio

class ApplicationMonitor:
    """Application performance monitoring"""
    
    def __init__(self):
        self.metrics = {
            'requests': 0,
            'errors': 0,
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'active_users': set(),
            'upload_count': 0,
            'export_count': 0
        }
        self.start_time = datetime.now()
    
    def record_request(self, user_id: str = None):
        """Record incoming request"""
        self.metrics['requests'] += 1
        if user_id:
            self.metrics['active_users'].add(user_id)
    
    def record_error(self, error_type: str, error_message: str):
        """Record application error"""
        self.metrics['errors'] += 1
        logging.error(f"{error_type}: {error_message}")
    
    def record_response_time(self, response_time: float):
        """Record response time"""
        self.metrics['response_times'].append(response_time)
        # Keep only last 1000 response times
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
    
    def record_system_metrics(self):
        """Record system resource usage"""
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=1)
        
        self.metrics['memory_usage'].append({
            'timestamp': datetime.now(),
            'usage': memory_percent
        })
        
        self.metrics['cpu_usage'].append({
            'timestamp': datetime.now(),
            'usage': cpu_percent
        })
        
        # Keep only last hour of metrics
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.metrics['memory_usage'] = [
            m for m in self.metrics['memory_usage'] 
            if m['timestamp'] > cutoff_time
        ]
        self.metrics['cpu_usage'] = [
            m for m in self.metrics['cpu_usage'] 
            if m['timestamp'] > cutoff_time
        ]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        uptime = datetime.now() - self.start_time
        avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times']) if self.metrics['response_times'] else 0
        
        return {
            'uptime': str(uptime),
            'total_requests': self.metrics['requests'],
            'total_errors': self.metrics['errors'],
            'error_rate': (self.metrics['errors'] / self.metrics['requests']) * 100 if self.metrics['requests'] > 0 else 0,
            'avg_response_time': round(avg_response_time, 2),
            'active_users': len(self.metrics['active_users']),
            'uploads_processed': self.metrics['upload_count'],
            'exports_generated': self.metrics['export_count'],
            'current_memory': psutil.virtual_memory().percent,
            'current_cpu': psutil.cpu_percent()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Application health check"""
        health_status = "healthy"
        issues = []
        
        # Check error rate
        if self.metrics['requests'] > 0:
            error_rate = (self.metrics['errors'] / self.metrics['requests']) * 100
            if error_rate > 5:  # More than 5% error rate
                health_status = "unhealthy"
                issues.append(f"High error rate: {error_rate:.1f}%")
        
        # Check memory usage
        memory_usage = psutil.virtual_memory().percent
        if memory_usage > 90:
            health_status = "unhealthy"
            issues.append(f"High memory usage: {memory_usage:.1f}%")
        elif memory_usage > 80:
            health_status = "warning"
            issues.append(f"Elevated memory usage: {memory_usage:.1f}%")
        
        # Check CPU usage
        cpu_usage = psutil.cpu_percent()
        if cpu_usage > 90:
            health_status = "unhealthy"
            issues.append(f"High CPU usage: {cpu_usage:.1f}%")
        
        return {
            'status': health_status,
            'timestamp': datetime.now().isoformat(),
            'issues': issues,
            'metrics': self.get_metrics_summary()
        }

# Performance monitoring decorator
def monitor_performance(monitor: ApplicationMonitor):
    """Decorator to monitor function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                monitor.record_error(type(e).__name__, str(e))
                raise
            finally:
                response_time = time.time() - start_time
                monitor.record_response_time(response_time)
        return wrapper
    return decorator

# Initialize global monitor
app_monitor = ApplicationMonitor()

# Usage in Streamlit app
@monitor_performance(app_monitor)
def monitored_function():
    """Example of monitored function"""
    # Function logic here
    pass
```

### Logging Configuration

```python
# logging_config.py
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any
import os

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def setup_production_logging():
    """Set up production logging configuration"""
    
    # Create logs directory
    log_dir = os.getenv('Q2LMS_LOG_DIR', './logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'q2lms.log'),
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10
    )
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'q2lms-errors.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)
    
    # Performance log handler
    perf_logger = logging.getLogger('q2lms.performance')
    perf_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'q2lms-performance.log'),
        maxBytes=25 * 1024 * 1024,  # 25MB
        backupCount=5
    )
    perf_handler.setFormatter(JSONFormatter())
    perf_logger.addHandler(perf_handler)
    
    # Security log handler
    security_logger = logging.getLogger('q2lms.security')
    security_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'q2lms-security.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    security_handler.setFormatter(JSONFormatter())
    security_logger.addHandler(security_handler)

class AuditLogger:
    """Audit logging for security and compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger('q2lms.audit')
    
    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any] = None):
        """Log user actions for audit trail"""
        self.logger.info(
            f"User action: {action}",
            extra={
                'user_id': user_id,
                'action': action,
                'details': details or {},
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_data_access(self, user_id: str, resource: str, operation: str):
        """Log data access events"""
        self.logger.info(
            f"Data access: {operation} on {resource}",
            extra={
                'user_id': user_id,
                'resource': resource,
                'operation': operation,
                'access_type': 'data_access'
            }
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        self.logger.warning(
            f"Security event: {event_type}",
            extra={
                'event_type': event_type,
                'security_event': True,
                'details': details
            }
        )

# Initialize audit logger
audit_logger = AuditLogger()
```

### Health Checks and Alerts

```python
# health_checks.py
import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from typing import List, Dict, Any
from datetime import datetime

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_manager = AlertManager(config.get('alerts', {}))
    
    async def check_application_health(self) -> Dict[str, Any]:
        """Check application health endpoints"""
        checks = {}
        
        # Check main application endpoint
        checks['app_endpoint'] = await self._check_endpoint(
            f"{self.config['app_url']}/_stcore/health"
        )
        
        # Check database connectivity
        checks['database'] = await self._check_database()
        
        # Check external dependencies
        checks['redis'] = await self._check_redis()
        
        # Check file system
        checks['filesystem'] = self._check_filesystem()
        
        # Overall status
        all_healthy = all(check.get('healthy', False) for check in checks.values())
        
        return {
            'overall_status': 'healthy' if all_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }
    
    async def _check_endpoint(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """Check HTTP endpoint health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    return {
                        'healthy': response.status == 200,
                        'status_code': response.status,
                        'response_time': response.headers.get('X-Response-Time'),
                        'url': url
                    }
        except asyncio.TimeoutError:
            return {
                'healthy': False,
                'error': 'timeout',
                'url': url
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'url': url
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            # This would check your actual database
            # For demo purposes, assume it's healthy
            return {
                'healthy': True,
                'connection_pool': 'available',
                'response_time': '< 100ms'
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        if not self.config.get('redis_url'):
            return {'healthy': True, 'note': 'Redis not configured'}
        
        try:
            import redis
            r = redis.from_url(self.config['redis_url'])
            r.ping()
            return {
                'healthy': True,
                'connection': 'successful'
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem health"""
        import shutil
        
        try:
            # Check disk space
            total, used, free = shutil.disk_usage('/')
            free_percent = (free / total) * 100
            
            return {
                'healthy': free_percent > 10,  # Alert if less than 10% free
                'free_space_percent': round(free_percent, 2),
                'free_space_gb': round(free / (1024**3), 2)
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }

class AlertManager:
    """Alert management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.email_config = config.get('email', {})
        self.webhook_config = config.get('webhook', {})
    
    async def send_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Send alert through configured channels"""
        alert_data = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'Q2LMS'
        }
        
        # Send email alert
        if self.email_config.get('enabled'):
            await self._send_email_alert(alert_data)
        
        # Send webhook alert
        if self.webhook_config.get('enabled'):
            await self._send_webhook_alert(alert_data)
    
    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = ', '.join(self.email_config['to_emails'])
            msg['Subject'] = f"Q2LMS Alert: {alert_data['type']} ({alert_data['severity']})"
            
            body = f"""
            Alert Type: {alert_data['type']}
            Severity: {alert_data['severity']}
            Time: {alert_data['timestamp']}
            
            Message:
            {alert_data['message']}
            
            Source: {alert_data['source']}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            if self.email_config.get('use_tls'):
                server.starttls()
            if self.email_config.get('username'):
                server.login(self.email_config['username'], self.email_config['password'])
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logging.error(f"Failed to send email alert: {str(e)}")
    
    async def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """Send webhook alert"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_config['url'],
                    json=alert_data,
                    headers=self.webhook_config.get('headers', {})
                ) as response:
                    if response.status >= 400:
                        logging.error(f"Webhook alert failed: {response.status}")
        except Exception as e:
            logging.error(f"Failed to send webhook alert: {str(e)}")

# Continuous monitoring task
async def continuous_monitoring():
    """Continuous monitoring task"""
    config = {
        'app_url': os.getenv('Q2LMS_URL', 'http://localhost:8501'),
        'redis_url': os.getenv('REDIS_URL'),
        'alerts': {
            'email': {
                'enabled': os.getenv('ALERTS_EMAIL_ENABLED', 'false').lower() == 'true',
                'from_email': os.getenv('ALERTS_FROM_EMAIL'),
                'to_emails': os.getenv('ALERTS_TO_EMAILS', '').split(','),
                'smtp_server': os.getenv('ALERTS_SMTP_SERVER'),
                'smtp_port': int(os.getenv('ALERTS_SMTP_PORT', '587')),
                'use_tls': os.getenv('ALERTS_USE_TLS', 'true').lower() == 'true',
                'username': os.getenv('ALERTS_SMTP_USERNAME'),
                'password': os.getenv('ALERTS_SMTP_PASSWORD')
            },
            'webhook': {
                'enabled': os.getenv('ALERTS_WEBHOOK_ENABLED', 'false').lower() == 'true',
                'url': os.getenv('ALERTS_WEBHOOK_URL'),
                'headers': json.loads(os.getenv('ALERTS_WEBHOOK_HEADERS', '{}'))
            }
        }
    }
    
    health_checker = HealthChecker(config)
    
    while True:
        try:
            health_status = await health_checker.check_application_health()
            
            if health_status['overall_status'] != 'healthy':
                await health_checker.alert_manager.send_alert(
                    'health_check_failed',
                    f"Health check failed: {json.dumps(health_status, indent=2)}",
                    'critical'
                )
            
            # Wait 5 minutes before next check
            await asyncio.sleep(300)
            
        except Exception as e:
            logging.error(f"Monitoring task error: {str(e)}")
            await asyncio.sleep(60)  # Wait 1 minute on error
```

---

## Backup and Recovery

### Automated Backup System

```bash
#!/bin/bash
# backup_q2        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: q2lms-secrets
              key: database-url
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: q2lms-data
      securityContext:
        fsGroup: 1000

---
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: q2lms-hpa
  namespace: q2lms
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: q2lms
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: q2lms-service
  namespace: q2lms
  labels:
    app: q2lms
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8501
    protocol: TCP
    name: http
  selector:
    app: q2lms

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
    nginx.ingress.kubernetes.io/proxy-body-size: "200m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - q2lms.yourdomain.com
    secretName: q2lms-tls
  rules:
  - host: q2lms.yourdomain.com
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

### Deployment Commands

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Or use Helm
helm install q2lms ./helm/q2lms -n q2lms --create-namespace

# Check deployment status
kubectl get pods -n q2lms
kubectl get services -n q2lms
kubectl get ingress -n q2lms

# View logs
kubectl logs -f deployment/q2lms -n q2lms

# Scale deployment
kubectl scale deployment q2lms --replicas=5 -n q2lms
```

---

## Enterprise Integration

### Single Sign-On (SSO) Integration

#### SAML Configuration

```python
# sso_integration.py
import streamlit as st
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

class SSOManager:
    """Enterprise SSO integration for Q2LMS"""
    
    def __init__(self, saml_settings):
        self.saml_settings = saml_settings
    
    def init_saml_auth(self, request):
        """Initialize SAML authentication"""
        auth = OneLogin_Saml2_Auth(request, self.saml_settings)
        return auth
    
    def login(self):
        """Initiate SSO login"""
        request = self._prepare_request()
        auth = self.init_saml_auth(request)
        return auth.login()
    
    def process_response(self):
        """Process SAML response"""
        request = self._prepare_request()
        auth = self.init_saml_auth(request)
        auth.process_response()
        
        if auth.is_authenticated():
            return {
                'authenticated': True,
                'user_id': auth.get_nameid(),
                'attributes': auth.get_attributes(),
                'session_index': auth.get_session_index()
            }
        else:
            return {
                'authenticated': False,
                'errors': auth.get_errors()
            }

# SAML settings configuration
SAML_SETTINGS = {
    "sp": {
        "entityId": "https://q2lms.yourdomain.com/saml/metadata",
        "assertionConsumerService": {
            "url": "https://q2lms.yourdomain.com/saml/acs",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        },
        "singleLogoutService": {
            "url": "https://q2lms.yourdomain.com/saml/sls",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
        "x509cert": "",
        "privateKey": ""
    },
    "idp": {
        "entityId": "https://idp.yourdomain.com/saml/metadata",
        "singleSignOnService": {
            "url": "https://idp.yourdomain.com/saml/sso",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "singleLogoutService": {
            "url": "https://idp.yourdomain.com/saml/slo",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "x509cert": "your_idp_certificate"
    }
}
```

#### LDAP Integration

```python
# ldap_integration.py
import ldap
from ldap.ldapobject import LDAPObject

class LDAPManager:
    """LDAP integration for user authentication and authorization"""
    
    def __init__(self, server_uri, base_dn, bind_dn=None, bind_password=None):
        self.server_uri = server_uri
        self.base_dn = base_dn
        self.bind_dn = bind_dn
        self.bind_password = bind_password
    
    def authenticate_user(self, username, password):
        """Authenticate user against LDAP"""
        try:
            conn = ldap.initialize(self.server_uri)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            
            # Bind with service account if provided
            if self.bind_dn:
                conn.simple_bind_s(self.bind_dn, self.bind_password)
            
            # Search for user
            search_filter = f"(sAMAccountName={username})"
            result = conn.search_s(
                self.base_dn, 
                ldap.SCOPE_SUBTREE, 
                search_filter,
                ['distinguishedName', 'mail', 'displayName', 'memberOf']
            )
            
            if not result:
                return None
            
            user_dn = result[0][0]
            user_attrs = result[0][1]
            
            # Authenticate user
            try:
                user_conn = ldap.initialize(self.server_uri)
                user_conn.simple_bind_s(user_dn, password)
                user_conn.unbind()
                
                return {
                    'dn': user_dn,
                    'username': username,
                    'email': user_attrs.get('mail', [b''])[0].decode('utf-8'),
                    'display_name': user_attrs.get('displayName', [b''])[0].decode('utf-8'),
                    'groups': [g.decode('utf-8') for g in user_attrs.get('memberOf', [])]
                }
            except ldap.INVALID_CREDENTIALS:
                return None
                
        except Exception as e:
            st.error(f"LDAP authentication error: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.unbind()
    
    def get_user_groups(self, username):
        """Get user group memberships"""
        try:
            conn = ldap.initialize(self.server_uri)
            if self.bind_dn:
                conn.simple_bind_s(self.bind_dn, self.bind_password)
            
            search_filter = f"(sAMAccountName={username})"
            result = conn.search_s(
                self.base_dn,
                ldap.SCOPE_SUBTREE,
                search_filter,
                ['memberOf']
            )
            
            if result:
                groups = result[0][1].get('memberOf', [])
                return [g.decode('utf-8') for g in groups]
            
            return []
        
        except Exception as e:
            st.error(f"Error fetching user groups: {str(e)}")
            return []
        finally:
            if 'conn' in locals():
                conn.unbind()
```

### Role-Based Access Control (RBAC)

```python
# rbac.py
from enum import Enum
from typing import List, Dict, Any
import streamlit as st

class Permission(Enum):
    """Available permissions in Q2LMS"""
    VIEW_QUESTIONS = "view_questions"
    EDIT_QUESTIONS = "edit_questions"
    DELETE_QUESTIONS = "delete_questions"
    EXPORT_QUESTIONS = "export_questions"
    MANAGE_USERS = "manage_users"
    SYSTEM_ADMIN = "system_admin"

class Role(Enum):
    """Predefined roles"""
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

ROLE_PERMISSIONS = {
    Role.STUDENT: [
        Permission.VIEW_QUESTIONS
    ],
    Role.INSTRUCTOR: [
        Permission.VIEW_QUESTIONS,
        Permission.EDIT_QUESTIONS,
        Permission.EXPORT_QUESTIONS
    ],
    Role.ADMIN: [
        Permission.VIEW_QUESTIONS,
        Permission.EDIT_QUESTIONS,
        Permission.DELETE_QUESTIONS,
        Permission.EXPORT_QUESTIONS,
        Permission.MANAGE_USERS
    ],
    Role.SUPER_ADMIN: list(Permission)
}

class RBACManager:
    """Role-Based Access Control Manager"""
    
    def __init__(self):
        self.user_roles = {}
        self.group_roles = {}
    
    def assign_role(self, user_id: str, role: Role):
        """Assign role to user"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        self.user_roles[user_id].append(role)
    
    def assign_group_role(self, group_name: str, role: Role):
        """Assign role to group"""
        self.group_roles[group_name] = role
    
    def get_user_permissions(self, user_id: str, user_groups: List[str] = None) -> List[Permission]:
        """Get all permissions for user"""
        permissions = set()
        
        # User direct roles
        user_roles = self.user_roles.get(user_id, [])
        for role in user_roles:
            permissions.update(ROLE_PERMISSIONS.get(role, []))
        
        # Group roles
        if user_groups:
            for group in user_groups:
                group_role = self.group_roles.get(group)
                if group_role:
                    permissions.update(ROLE_PERMISSIONS.get(group_role, []))
        
        return list(permissions)
    
    def has_permission(self, user_id: str, permission: Permission, user_groups: List[str] = None) -> bool:
        """Check if user has specific permission"""
        user_permissions = self.get_user_permissions(user_id, user_groups)
        return permission in user_permissions
    
    def require_permission(self, permission: Permission):
        """Decorator to require permission for function access"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                user_id = st.session_state.get('user_id')
                user_groups = st.session_state.get('user_groups', [])
                
                if not user_id:
                    st.error("Authentication required")
                    st.stop()
                
                if not self.has_permission(user_id, permission, user_groups):
                    st.error("Insufficient permissions")
                    st.stop()
                
                return func(*args, **kwargs)
            return wrapper
        return decorator

# Usage example
rbac = RBACManager()

@rbac.require_permission(Permission.EDIT_QUESTIONS)
def edit_question_interface():
    """Question editing interface - requires edit permission"""
    st.markdown("### Edit Question")
    # ... editing logic ...

@rbac.require_permission(Permission.SYSTEM_ADMIN)
def admin_panel():
    """Admin panel - requires admin permission"""
    st.markdown("### System Administration")
    # ... admin logic ...
```

### API Integration

```python
# api_integration.py
import requests
from typing import Dict, Any, Optional
import streamlit as st

class InstitutionAPIManager:
    """Integration with institutional APIs"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def get_courses(self, instructor_id: str) -> List[Dict]:
        """Get courses for instructor from SIS"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/instructors/{instructor_id}/courses"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error fetching courses: {str(e)}")
            return []
    
    def get_students(self, course_id: str) -> List[Dict]:
        """Get enrolled students for course"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/courses/{course_id}/students"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error fetching students: {str(e)}")
            return []
    
    def sync_gradebook(self, course_id: str, grades: Dict[str, float]) -> bool:
        """Sync grades back to SIS"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/courses/{course_id}/grades",
                json=grades
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            st.error(f"Error syncing grades: {str(e)}")
            return False

class CanvasAPIManager:
    """Canvas LMS API integration"""
    
    def __init__(self, canvas_url: str, access_token: str):
        self.canvas_url = canvas_url
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}'
        })
    
    def get_courses(self) -> List[Dict]:
        """Get instructor's courses from Canvas"""
        try:
            response = self.session.get(
                f"{self.canvas_url}/api/v1/courses",
                params={'enrollment_type': 'teacher'}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Canvas API error: {str(e)}")
            return []
    
    def create_quiz(self, course_id: str, quiz_data: Dict) -> Optional[Dict]:
        """Create quiz in Canvas"""
        try:
            response = self.session.post(
                f"{self.canvas_url}/api/v1/courses/{course_id}/quizzes",
                json={'quiz': quiz_data}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error creating Canvas quiz: {str(e)}")
            return None
    
    def upload_qti_package(self, course_id: str, qti_data: bytes) -> bool:
        """Upload QTI package to Canvas"""
        try:
            # Step 1: Get upload URL
            response = self.session.post(
                f"{self.canvas_url}/api/v1/courses/{course_id}/content_migrations",
                json={
                    'migration_type': 'qti_converter',
                    'settings': {
                        'file_url': 'upload'
                    }
                }
            )
            response.raise_for_status()
            
            migration = response.json()
            
            # Step 2: Upload file
            upload_response = self.session.post(
                migration['attachment']['upload_url'],
                files={'file': ('quiz.zip', qti_data, 'application/zip')}
            )
            upload_response.raise_for_status()
            
            return True
        except requests.RequestException as e:
            st.error(f"Error uploading QTI package: {str(e)}")
            return False
```

---

## Security Configuration

### SSL/TLS Configuration

#### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d q2lms.yourdomain.com

# Auto-renewal setup
sudo crontab -e
# Add line: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Custom SSL Certificate

```nginx
# nginx-ssl.conf
server {
    listen 443 ssl http2;
    server_name q2lms.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/q2lms.crt;
    ssl_certificate_key /etc/ssl/private/q2lms.key;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' wss:";
    
    location / {
        proxy_pass http://q2lms_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Application Security

```python
# security.py
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
import streamlit as st

class SecurityManager:
    """Application security management"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        return hmac.compare_digest(token, session_token)
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_bytes(32)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return salt.hex() + hashed.hex()
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        salt_hex = stored_hash[:64]
        hash_hex = stored_hash[64:]
        salt = bytes.fromhex(salt_hex)
        stored_password_hash = bytes.fromhex(hash_hex)
        
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return hmac.compare_digest(stored_password_hash, new_hash)
    
    def create_secure_session(self, user_id: str) -> Dict[str, Any]:
        """Create secure session"""
        session_id = secrets.token_urlsafe(32)
        csrf_token = self.generate_csrf_token()
        expiry = datetime.now() + timedelta(hours=8)
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'csrf_token': csrf_token,
            'expiry': expiry.isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        return session_data
    
    def validate_session(self, session_data: Dict[str, Any]) -> bool:
        """Validate session data"""
        try:
            expiry = datetime.fromisoformat(session_data['expiry'])
            return datetime.now() < expiry
        except (KeyError, ValueError):
            return False

# Input validation
class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize uploaded filename"""
        import re
        # Remove path components and dangerous characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        filename = re.sub(r'\.{2,}', '.', filename)
        return filename[:255]  # Limit length
    
    @staticmethod
    def validate_json_structure(data: Dict) -> bool:
        """Validate JSON structure"""
        required_keys = ['questions']
        if not all(key in data for key in required_keys):
            return False
        
        if not isinstance(data['questions'], list):
            return False
        
        return True
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Basic HTML sanitization"""
        import html
        return html.escape(text)

# Rate limiting
class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self):
        self.requests = {}
    
    def is_rate_limited(self, identifier: str, max_requests: int = 100, window_minutes: int = 60) -> bool:
        """Check if identifier is rate limited"""
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= max_requests:
            return True
        
        # Add current request
        self.requests[identifier].append(now)
        return False
```

### Data Protection

```python
# data_protection.py
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataProtection:
    """Data encryption and protection"""
    
    def __init__(self, password: str):
        self.key = self._derive_key(password)
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        password_bytes = password.encode()
        salt = b'stable_salt_for_q2lms'  # In production, use random salt per dataset
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    def encrypt_file(self, file_path: str, output_path: str):
        """Encrypt file"""
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        encrypted_data = self.cipher.encrypt(file_data)
        
        with open(output_path, 'wb') as file:
            file.write(encrypted_data)
    
    def decrypt_file(self, encrypted_path: str, output_path: str):
        """Decrypt file"""
        with open(encrypted_path, 'rb') as file:
            encrypted_data = file.read()
        
        decrypted_data = self.cipher.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as file:
            file.write(decrypted_data)

# GDPR Compliance
class GDPRManager:
    """GDPR compliance management"""
    
    def __init__(self):
        self.data_retention_days = 365 * 2  # 2 years
        self.personal_data_fields = ['email', 'name', 'user_id']
    
    def anonymize_user_data(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Anonymize personal data"""
        anonymized = data.copy()
        
        for field in self.personal_data_fields:
            if field in anonymized:
                anonymized[field] = f"anonymized_{hash(user_id + field) % 10000}"
        
        return anonymized
    
    def check_data_retention(self, created_date: datetime) -> bool:
        """Check if data should be retained"""
        retention_limit = datetime.now() - timedelta(days=self.data_retention_days)
        return created_date > retention_limit
    
    def generate_data_export(self, user_id: str) -> Dict[str, Any]:
        """Generate user data export for GDPR request"""
        # This would collect all user data across the system
        user_data = {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'questions_created': [],
            'questions_edited': [],
            'exports_generated': [],
            'login_history': []
        }
        
        return user_data
```

---

## Performance Optimization

### Caching Strategies

```python
# caching.py
import streamlit as st
import hashlib
import pickle
from functools import wraps
import redis
from typing import Any, Callable

class CacheManager:
    """Advanced caching for Q2LMS"""
    
    def __init__(self, use_redis: bool = False, redis_url: str = None):
        self.use_redis = use_redis
        if use_redis and redis_url:
            self.redis_client = redis.from_url(redis_url)
        else:
            self.redis_client = None
    
    def cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key"""
        key_data = f"{func_name}_{str(args)}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cache(self, key: str) -> Any:
        """Get cached value"""
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return pickle.loads(data)
            except Exception:
                pass
        
        # Fallback to session state
        return st.session_state.get(f"cache_{key}")
    
    def set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Set cached value"""
        if self.redis│  • Thousands of users                               │
└─────────────────────────────────────────────────────┘
```

### Prerequisites

**System Requirements**:
- Python 3.8 or higher
- 2GB RAM minimum (4GB recommended for production)
- 1GB disk space for application and data
- Network connectivity for LMS integration

**Software Dependencies**:
- Streamlit >= 1.20.0
- Pandas >= 1.5.0
- Plotly >= 5.0.0
- Additional packages per requirements.txt

---

## Local Development Setup

### Quick Start Installation

```bash
# Clone the repository
git clone https://github.com/your-org/q2lms.git
cd q2lms

# Create virtual environment
python -m venv q2lms_env

# Activate virtual environment
# On Windows:
q2lms_env\Scripts\activate
# On macOS/Linux:
source q2lms_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch application
streamlit run streamlit_app.py
```

### Development Environment Configuration

#### Virtual Environment Setup

```bash
# Create isolated environment
python -m venv q2lms_dev
source q2lms_dev/bin/activate  # or q2lms_dev\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
pre-commit install
```

#### Environment Variables

Create `.env` file for development configuration:

```bash
# .env file
Q2LMS_ENV=development
Q2LMS_DEBUG=true
Q2LMS_LOG_LEVEL=DEBUG

# Optional: Custom paths
Q2LMS_DATA_DIR=./data
Q2LMS_TEMP_DIR=./temp
Q2LMS_LOG_DIR=./logs

# Optional: Feature flags
Q2LMS_ENABLE_ANALYTICS=false
Q2LMS_ENABLE_TELEMETRY=false
```

#### IDE Configuration

**VS Code settings.json**:
```json
{
    "python.defaultInterpreterPath": "./q2lms_env/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

### Testing Local Installation

```bash
# Run unit tests
python -m pytest tests/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run performance tests
python -m pytest tests/performance/ -v

# Test application startup
streamlit run streamlit_app.py --server.headless true --server.port 8501
```

---

## Streamlit Cloud Deployment

### Setup Process

1. **Repository Preparation**
   ```bash
   # Ensure clean repository structure
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Streamlit Cloud Configuration**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Connect GitHub account
   - Select Q2LMS repository
   - Configure deployment settings

3. **Streamlit Configuration File**

   Create `.streamlit/config.toml`:
   ```toml
   [global]
   developmentMode = false
   
   [server]
   headless = true
   enableCORS = false
   enableXsrfProtection = true
   maxUploadSize = 200
   
   [browser]
   gatherUsageStats = false
   
   [theme]
   primaryColor = "#1f77b4"
   backgroundColor = "#ffffff"
   secondaryBackgroundColor = "#f0f2f6"
   textColor = "#262730"
   font = "sans serif"
   ```

### Streamlit Secrets Management

Create `.streamlit/secrets.toml` for sensitive configuration:

```toml
# Database connections (if applicable)
[connections]
database_url = "your_database_connection_string"

# API keys
[api]
analytics_key = "your_analytics_key"
monitoring_key = "your_monitoring_key"

# Feature flags
[features]
enable_advanced_analytics = true
enable_custom_branding = true

# Institutional settings
[institution]
name = "Your Institution"
logo_url = "https://your-institution.edu/logo.png"
support_email = "support@your-institution.edu"
```

### Production Streamlit Cloud Settings

#### Memory Optimization
```python
# Add to streamlit_app.py for production
import streamlit as st

# Configure for production
if not st._is_running_with_streamlit:
    st.set_page_config(
        page_title="Q2LMS",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://your-institution.edu/q2lms-help',
            'Report a bug': 'https://your-institution.edu/q2lms-support',
            'About': "Q2LMS - Question Database Manager v1.0"
        }
    )

# Memory management for large datasets
@st.cache_data(max_entries=10, ttl=3600)
def cached_data_processing(data_hash):
    # Cached processing for better performance
    pass
```

---

## Docker Containerization

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 q2lms && chown -R q2lms:q2lms /app
USER q2lms

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Start application
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  q2lms:
    build: .
    ports:
      - "8501:8501"
    environment:
      - Q2LMS_ENV=development
      - Q2LMS_DEBUG=true
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  # Optional: Redis for caching
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  # Optional: Database
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: q2lms
      POSTGRES_USER: q2lms
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  q2lms:
    build: .
    ports:
      - "8501:8501"
    environment:
      - Q2LMS_ENV=production
      - Q2LMS_DEBUG=false
      - Q2LMS_LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data:ro
      - ./logs:/app/logs
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - q2lms
    restart: always

  # Monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    restart: always

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure_admin_password
    volumes:
      - grafana_data:/var/lib/grafana
    restart: always

volumes:
  grafana_data:
```

### NGINX Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream q2lms {
        server q2lms:8501;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=q2lms_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name your-domain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/certificate.crt;
        ssl_certificate_key /etc/nginx/ssl/private.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # File upload size
        client_max_body_size 200M;

        # Rate limiting
        limit_req zone=q2lms_limit burst=20 nodelay;

        location / {
            proxy_pass http://q2lms;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support for Streamlit
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }

        # Static file caching
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
            proxy_pass http://q2lms;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### Container Build and Deployment

```bash
# Build production image
docker build -t q2lms:latest .

# Tag for registry
docker tag q2lms:latest your-registry.com/q2lms:v1.0

# Push to registry
docker push your-registry.com/q2lms:v1.0

# Deploy with compose
docker-compose -f docker-compose.prod.yml up -d

# Monitor deployment
docker-compose -f docker-compose.prod.yml logs -f q2lms
```

---

## AWS Deployment

### AWS ECS Deployment

#### Task Definition

```json
{
  "family": "q2lms-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/q2lmsTaskRole",
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
        },
        {
          "name": "Q2LMS_LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:q2lms/database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/q2lms",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8501/_stcore/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### CloudFormation Template

```yaml
# q2lms-infrastructure.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Q2LMS Infrastructure on AWS'

Parameters:
  DomainName:
    Type: String
    Description: Domain name for Q2LMS
    Default: q2lms.example.com
  
  CertificateArn:
    Type: String
    Description: SSL certificate ARN
  
  ImageUri:
    Type: String
    Description: ECR image URI

Resources:
  # VPC and Networking
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: Q2LMS-VPC

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true

  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.3.0/24
      AvailabilityZone: !Select [0, !GetAZs '']

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.4.0/24
      AvailabilityZone: !Select [1, !GetAZs '']

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: q2lms-cluster
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT

  # Application Load Balancer
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: q2lms-alb
      Scheme: internet-facing
      Type: application
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref LoadBalancerSecurityGroup

  LoadBalancerSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Q2LMS load balancer
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    Properties:
      ServiceName: q2lms-service
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          SecurityGroups:
            - !Ref ECSSecurityGroup
          Subnets:
            - !Ref PrivateSubnet1
            - !Ref PrivateSubnet2
          AssignPublicIp: DISABLED
      LoadBalancers:
        - ContainerName: q2lms
          ContainerPort: 8501
          TargetGroupArn: !Ref TargetGroup

  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: q2lms-task
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: 1024
      Memory: 2048
      ExecutionRoleArn: !Ref ECSExecutionRole
      TaskRoleArn: !Ref ECSTaskRole
      ContainerDefinitions:
        - Name: q2lms
          Image: !Ref ImageUri
          PortMappings:
            - ContainerPort: 8501
          Environment:
            - Name: Q2LMS_ENV
              Value: production
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Ref LogGroup
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs

  # Auto Scaling
  AutoScalingTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      MaxCapacity: 10
      MinCapacity: 2
      ResourceId: !Sub service/${ECSCluster}/${ECSService.Name}
      RoleARN: !Sub arn:aws:iam::${AWS::AccountId}:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService
      ScalableDimension: ecs:service:DesiredCount
      ServiceNamespace: ecs

  AutoScalingPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: q2lms-scaling-policy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref AutoScalingTarget
      TargetTrackingScalingPolicyConfiguration:
        PredefinedMetricSpecification:
          PredefinedMetricType: ECSServiceAverageCPUUtilization
        TargetValue: 70.0

Outputs:
  LoadBalancerDNS:
    Description: Load Balancer DNS Name
    Value: !GetAtt LoadBalancer.DNSName
  
  ClusterName:
    Description: ECS Cluster Name
    Value: !Ref ECSCluster
```

### AWS Lambda Deployment (Serverless)

For lightweight deployments, Q2LMS can run on AWS Lambda:

```python
# lambda_handler.py
import json
import base64
from streamlit.web import cli as stcli
import sys
import os

def lambda_handler(event, context):
    """AWS Lambda handler for Q2LMS"""
    
    # Set up Streamlit for Lambda
    sys.argv = ["streamlit", "run", "streamlit_app.py", 
                "--server.headless", "true",
                "--server.enableCORS", "false",
                "--server.port", "8501"]
    
    # Override Streamlit's main function
    stcli.main()
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
            'Access-Control-Allow-Origin': '*'
        },
        'body': 'Q2LMS Lambda deployment successful'
    }
```

---

## Azure Deployment

### Azure Container Instances

```bash
# Create resource group
az group create --name q2lms-rg --location eastus

# Create container registry
az acr create --resource-group q2lms-rg --name q2lmsregistry --sku Basic

# Build and push image
az acr build --registry q2lmsregistry --image q2lms:v1 .

# Create container instance
az container create \
  --resource-group q2lms-rg \
  --name q2lms-container \
  --image q2lmsregistry.azurecr.io/q2lms:v1 \
  --cpu 2 \
  --memory 4 \
  --registry-login-server q2lmsregistry.azurecr.io \
  --registry-username q2lmsregistry \
  --registry-password $(az acr credential show --name q2lmsregistry --query "passwords[0].value" -o tsv) \
  --ip-address Public \
  --ports 8501 \
  --environment-variables Q2LMS_ENV=production
```

### Azure App Service

```yaml
# azure-pipelines.yml
trigger:
- main

variables:
  azureSubscription: 'your-azure-subscription'
  appName: 'q2lms-app'
  resourceGroupName: 'q2lms-rg'

stages:
- stage: Build
  jobs:
  - job: BuildAndPush
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: Docker@2
      displayName: Build and push image
      inputs:
        containerRegistry: 'q2lmsregistry'
        repository: 'q2lms'
        command: 'buildAndPush'
        Dockerfile: '**/Dockerfile'
        tags: |
          $(Build.BuildId)
          latest

- stage: Deploy
  jobs:
  - deployment: DeployToAzure
    environment: 'production'
    pool:
      vmImage: 'ubuntu-latest'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureWebAppContainer@1
            displayName: 'Deploy to Azure App Service'
            inputs:
              azureSubscription: $(azureSubscription)
              appName: $(appName)
              imageName: 'q2lmsregistry.azurecr.io/q2lms:$(Build.BuildId)'
```

### Azure Kubernetes Service (AKS)

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: q2lms-deployment
  labels:
    app: q2lms
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
        image: q2lmsregistry.azurecr.io/q2lms:latest
        ports:
        - containerPort: 8501
        env:
        - name: Q2LMS_ENV
          value: "production"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: q2lms-service
spec:
  selector:
    app: q2lms
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8501
  type: LoadBalancer

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: q2lms-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - q2lms.yourdomain.com
    secretName: q2lms-tls
  rules:
  - host: q2lms.yourdomain.com
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

---

## Google Cloud Platform

### Cloud Run Deployment

```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/q2lms

gcloud run deploy q2lms \
  --image gcr.io/PROJECT_ID/q2lms \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 100 \
  --max-instances 10 \
  --set-env-vars Q2LMS_ENV=production
```

### Google Kubernetes Engine (GKE)

```yaml
# gke-cluster.yaml
apiVersion: container.v1
kind: Cluster
metadata:
  name: q2lms-cluster
spec:
  zone: us-central1-a
  initialNodeCount: 3
  nodeConfig:
    machineType: n1-standard-2
    diskSizeGb: 100
    preemptible: false
  masterAuth:
    username: admin
  network: default
  addonsConfig:
    httpLoadBalancing:
      disabled: false
    horizontalPodAutoscaling:
      disabled: false
```

### Cloud Functions (Serverless)

```python
# main.py for Cloud Functions
import functions_framework
from streamlit.web import cli as stcli
import sys

@functions_framework.http
def q2lms_function(request):
    """Google Cloud Function for Q2LMS"""
    
    # Configure Streamlit for Cloud Functions
    sys.argv = ["streamlit", "run", "streamlit_app.py", 
                "--server.headless", "true",
                "--server.port", "8080"]
    
    try:
        stcli.main()
        return 'Q2LMS Cloud Function deployed successfully'
    except Exception as e:
        return f'Error: {str(e)}', 500
```

---

## Kubernetes Deployment

### Helm Chart

```yaml
# helm/q2lms/Chart.yaml
apiVersion: v2
name: q2lms
description: Q2LMS Helm Chart
version: 1.0.0
appVersion: "1.0.0"

# helm/q2lms/values.yaml
replicaCount: 3

image:
  repository: q2lms
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  port: 80
  targetPort: 8501

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "200m"
  hosts:
    - host: q2lms.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: q2lms-tls
      hosts:
        - q2lms.example.com

resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

nodeSelector: {}
tolerations: []
affinity: {}

# Persistent storage for data
persistence:
  enabled: true
  storageClass: "fast-ssd"
  accessMode: ReadWriteOnce
  size: 10Gi

# Environment variables
env:
  Q2LMS_ENV: production
  Q2LMS_LOG_LEVEL: INFO

# Secrets
secrets:
  database_url: ""
  api_keys: ""
```

### Production Kubernetes Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: q2lms
  labels:
    name: q2lms

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: q2lms-config
  namespace: q2lms
data:
  Q2LMS_ENV: "production"
  Q2LMS_LOG_LEVEL: "INFO"
  Q2LMS_MAX_UPLOAD_SIZE: "200"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: q2lms-secrets
  namespace: q2lms
type: Opaque
data:
  database-url: <base64-encoded-database-url>
  api-key: <base64-encoded-api-key>

---
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: q2lms-data
  namespace: q2lms
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: q2lms
  namespace: q2lms
  labels:
    app: q2lms
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: q2lms
  template:
    metadata:
      labels:
        app: q2lms
        version: v1
    spec:
      containers:
      - name: q2lms
        image: q2lms:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8501
          name: http
        envFrom:
        - configMapRef:
            name: q2lms-config
        # Q2LMS Deployment Guide
## Production Deployment and Operations Manual

### Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Local Development Setup](#local-development-setup)
3. [Streamlit Cloud Deployment](#streamlit-cloud-deployment)
4. [Docker Containerization](#docker-containerization)
5. [AWS Deployment](#aws-deployment)
6. [Azure Deployment](#azure-deployment)
7. [Google Cloud Platform](#google-cloud-platform)
8. [Kubernetes Deployment](#kubernetes-deployment)
9. [Enterprise Integration](#enterprise-integration)
10. [Security Configuration](#security-configuration)
11. [Performance Optimization](#performance-optimization)
12. [Monitoring and Maintenance](#monitoring-and-maintenance)
13. [Troubleshooting](#troubleshooting)
14. [Backup and Recovery](#backup-and-recovery)

---

## Deployment Overview

Q2LMS is designed for flexible deployment across various environments, from individual instructor laptops to enterprise-scale educational infrastructure. This guide covers all deployment scenarios with production-ready configurations.

### Architecture Options

```
┌─ Individual Use ─────────────────────────────────────┐
│  • Local Python environment                         │
│  • Single user access                               │
│  • Development and testing                          │
└─────────────────────────────────────────────────────┘

┌─ Department Deployment ──────────────────────────────┐
│  • Streamlit Cloud or Docker                        │
│  • Multiple concurrent users (5-50)                 │
│  • Shared department resources                      │
└─────────────────────────────────────────────────────┘

┌─ Institutional Deployment ───────────────────────────┐
│  • Cloud platforms (AWS, Azure, GCP)                │
│  • High availability and scalability                │
│  • Enterprise security and integration              │
│  • Hundreds of concurrent users                     │
└─────────────────────────────────────────────────────┘

┌─ Multi-Tenant SaaS ──────────────────────────────────┐
│  • Kubernetes orchestration                         │
│  • Multi-institution hosting                        │
│  • Advanced monitoring and analytics                │
│  • Thousands of users