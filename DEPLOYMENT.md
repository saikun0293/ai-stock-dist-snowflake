# Deployment Guide

This guide covers deployment options for the Inventory Monitoring System.

## Quick Start (Local Development)

### Using the Setup Script

```bash
# Clone the repository
git clone https://github.com/saikun0293/ai-stock-dist-snowflake.git
cd ai-stock-dist-snowflake

# Run setup script
chmod +x setup.sh
./setup.sh

# Launch dashboard
cd streamlit_app
streamlit run app.py
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Generate sample data
cd data
python generate_sample_data.py
cd ..

# Run dashboard
cd streamlit_app
streamlit run app.py
```

## Production Deployment

### Option 1: Streamlit Cloud (Recommended)

**Prerequisites:**
- GitHub account
- Snowflake account (optional)

**Steps:**

1. **Push to GitHub** (already done)

2. **Connect to Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Sign in with GitHub
   - Click "New app"
   - Select your repository: `saikun0293/ai-stock-dist-snowflake`
   - Set main file path: `streamlit_app/app.py`
   - Click "Deploy"

3. **Configure Secrets** (if using Snowflake)
   - In Streamlit Cloud dashboard, go to "Advanced settings"
   - Add secrets:
   ```toml
   snowflake_user = "your_username"
   snowflake_password = "your_password"
   snowflake_account = "your_account"
   snowflake_warehouse = "COMPUTE_WH"
   snowflake_database = "INVENTORY_DB"
   snowflake_schema = "INVENTORY_SCHEMA"
   ```

4. **Access Your App**
   - URL: `https://share.streamlit.io/[username]/ai-stock-dist-snowflake`

### Option 2: Docker Deployment

**Create Dockerfile:**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY streamlit_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY streamlit_app/ ./streamlit_app/
COPY data/ ./data/

WORKDIR /app/streamlit_app

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Build and Run:**

```bash
# Build image
docker build -t inventory-dashboard .

# Run container
docker run -p 8501:8501 inventory-dashboard

# With Snowflake secrets
docker run -p 8501:8501 \
  -e SNOWFLAKE_USER="your_user" \
  -e SNOWFLAKE_PASSWORD="your_pass" \
  -e SNOWFLAKE_ACCOUNT="your_account" \
  inventory-dashboard
```

**Docker Compose:**

```yaml
version: '3.8'
services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SNOWFLAKE_USER=${SNOWFLAKE_USER}
      - SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
    restart: unless-stopped
```

### Option 3: AWS EC2

**Prerequisites:**
- AWS account
- EC2 instance (t2.medium or larger recommended)

**Steps:**

1. **Launch EC2 Instance**
   - AMI: Amazon Linux 2 or Ubuntu 20.04
   - Instance type: t2.medium
   - Security group: Allow inbound on port 8501

2. **Connect and Setup**
   ```bash
   # SSH into instance
   ssh -i your-key.pem ec2-user@your-instance-ip
   
   # Install Python and Git
   sudo yum update -y
   sudo yum install python3 git -y
   
   # Clone repository
   git clone https://github.com/saikun0293/ai-stock-dist-snowflake.git
   cd ai-stock-dist-snowflake
   
   # Install dependencies
   pip3 install -r requirements.txt
   
   # Generate data
   cd data && python3 generate_sample_data.py && cd ..
   ```

3. **Run with systemd**
   
   Create `/etc/systemd/system/inventory-dashboard.service`:
   ```ini
   [Unit]
   Description=Inventory Dashboard
   After=network.target
   
   [Service]
   User=ec2-user
   WorkingDirectory=/home/ec2-user/ai-stock-dist-snowflake/streamlit_app
   ExecStart=/usr/local/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start:
   ```bash
   sudo systemctl enable inventory-dashboard
   sudo systemctl start inventory-dashboard
   ```

4. **Access Dashboard**
   - URL: `http://your-instance-ip:8501`

### Option 4: Google Cloud Run

**Prerequisites:**
- Google Cloud account
- gcloud CLI installed

**Steps:**

1. **Create Dockerfile** (see Docker option above)

2. **Build and Deploy**
   ```bash
   # Set project
   gcloud config set project your-project-id
   
   # Build image
   gcloud builds submit --tag gcr.io/your-project-id/inventory-dashboard
   
   # Deploy to Cloud Run
   gcloud run deploy inventory-dashboard \
     --image gcr.io/your-project-id/inventory-dashboard \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8501
   ```

3. **Add Secrets** (if using Snowflake)
   ```bash
   # Create secrets in Secret Manager
   echo -n "your_password" | gcloud secrets create snowflake-password --data-file=-
   
   # Grant access to Cloud Run
   gcloud secrets add-iam-policy-binding snowflake-password \
     --member=serviceAccount:your-service-account \
     --role=roles/secretmanager.secretAccessor
   ```

### Option 5: Azure App Service

**Prerequisites:**
- Azure account
- Azure CLI installed

**Steps:**

1. **Create App Service**
   ```bash
   # Login
   az login
   
   # Create resource group
   az group create --name inventory-rg --location eastus
   
   # Create App Service plan
   az appservice plan create --name inventory-plan \
     --resource-group inventory-rg --sku B1 --is-linux
   
   # Create web app
   az webapp create --name inventory-dashboard \
     --resource-group inventory-rg \
     --plan inventory-plan \
     --runtime "PYTHON:3.9"
   ```

2. **Deploy Code**
   ```bash
   # Deploy from GitHub
   az webapp deployment source config --name inventory-dashboard \
     --resource-group inventory-rg \
     --repo-url https://github.com/saikun0293/ai-stock-dist-snowflake \
     --branch main --manual-integration
   ```

3. **Configure Settings**
   ```bash
   # Set startup command
   az webapp config set --name inventory-dashboard \
     --resource-group inventory-rg \
     --startup-file "streamlit run streamlit_app/app.py --server.port=8000"
   ```

## Snowflake Setup

### Prerequisites
- Snowflake account
- ACCOUNTADMIN or equivalent role

### Setup Steps

1. **Connect to Snowflake**
   ```bash
   snowsql -a your_account -u your_username
   ```

2. **Execute SQL Scripts**
   ```sql
   -- Run in order
   !source snowflake/01_database_setup.sql
   !source snowflake/02_streams_setup.sql
   !source snowflake/03_tasks_setup.sql
   !source snowflake/04_cortex_forecasting.sql
   ```

3. **Load Sample Data**
   ```sql
   -- Upload CSV to stage
   PUT file:///path/to/inventory_data.csv @INVENTORY_STAGE;
   
   -- Load data
   CALL LOAD_INVENTORY_DATA('@INVENTORY_STAGE');
   
   -- Verify
   SELECT COUNT(*) FROM INVENTORY_SNAPSHOTS;
   ```

4. **Activate Tasks**
   ```sql
   ALTER TASK TASK_PROCESS_INVENTORY_CHANGES RESUME;
   ALTER TASK TASK_DAILY_FORECAST RESUME;
   ALTER TASK TASK_CLEANUP_OLD_ALERTS RESUME;
   ALTER TASK TASK_REFRESH_STATISTICS RESUME;
   ```

## Environment Variables

### Required (for Snowflake connection)
- `SNOWFLAKE_USER`: Snowflake username
- `SNOWFLAKE_PASSWORD`: Snowflake password
- `SNOWFLAKE_ACCOUNT`: Snowflake account identifier
- `SNOWFLAKE_WAREHOUSE`: Warehouse name (default: COMPUTE_WH)
- `SNOWFLAKE_DATABASE`: Database name (default: INVENTORY_DB)
- `SNOWFLAKE_SCHEMA`: Schema name (default: INVENTORY_SCHEMA)

### Optional
- `STREAMLIT_SERVER_PORT`: Port number (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Bind address (default: localhost)

## Security Considerations

### Production Checklist
- [ ] Use HTTPS (SSL/TLS certificates)
- [ ] Enable authentication (Streamlit Cloud or custom)
- [ ] Secure Snowflake credentials (secrets manager)
- [ ] Enable CORS protection
- [ ] Set up firewall rules
- [ ] Enable logging and monitoring
- [ ] Regular security updates
- [ ] Backup strategy for data

### Snowflake Security
- [ ] Create dedicated service account
- [ ] Use role-based access control
- [ ] Enable network policies
- [ ] Rotate credentials regularly
- [ ] Enable query auditing
- [ ] Use private connectivity (PrivateLink)

## Monitoring

### Application Monitoring
- Use Streamlit Cloud metrics
- Monitor response times
- Track user sessions
- Log errors and exceptions

### Snowflake Monitoring
```sql
-- Check task execution
SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE database_name = 'INVENTORY_DB'
ORDER BY scheduled_time DESC LIMIT 10;

-- Check warehouse usage
SELECT * FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY())
WHERE warehouse_name = 'COMPUTE_WH'
ORDER BY start_time DESC LIMIT 10;

-- Check query performance
SELECT * FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE database_name = 'INVENTORY_DB'
ORDER BY start_time DESC LIMIT 10;
```

## Troubleshooting

### Common Issues

**Dashboard won't start**
- Check Python version (3.8+)
- Verify all dependencies installed
- Check port 8501 is available

**Can't connect to Snowflake**
- Verify credentials in secrets.toml
- Check network connectivity
- Ensure warehouse is running
- Verify account identifier format

**Performance issues**
- Increase Snowflake warehouse size
- Enable caching in Streamlit
- Optimize SQL queries
- Reduce data volume with filters

**Memory errors**
- Increase instance size
- Limit query result sizes
- Enable pagination

## Scaling

### Horizontal Scaling
- Deploy multiple instances behind load balancer
- Use Streamlit Cloud auto-scaling
- Implement caching layer (Redis)

### Vertical Scaling
- Increase instance size
- Upgrade Snowflake warehouse
- Add more memory/CPU

## Cost Optimization

### Streamlit Cloud
- Free tier: 1 private app
- Team plan: $250/month (5 apps)
- Enterprise: Custom pricing

### Snowflake
- Use auto-suspend for warehouses
- Set appropriate warehouse size
- Monitor credit usage
- Use resource monitors
- Schedule tasks efficiently

### Cloud Providers
- Use spot/preemptible instances
- Enable auto-scaling
- Use reserved instances for production
- Monitor and optimize resource usage

## Backup and Recovery

### Application Code
- Version control with Git
- Regular backups of secrets
- Document configuration

### Snowflake Data
- Enable Time Travel (90 days)
- Use Fail-safe (7 days)
- Regular data exports
- Test restore procedures

## Support

For deployment issues:
1. Check logs (Streamlit, Snowflake)
2. Review documentation
3. Open GitHub issue
4. Contact support team

## Next Steps

After deployment:
1. Configure monitoring
2. Set up alerts
3. Train users
4. Plan regular maintenance
5. Schedule backups
6. Review security
7. Optimize performance
