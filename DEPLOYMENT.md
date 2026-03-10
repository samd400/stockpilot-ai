# StockPilot Deployment Guide

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [AWS Deployment](#aws-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Production Checklist](#production-checklist)

---

## Local Development

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Git

### Setup Steps

1. **Clone Repository**
```bash
git clone <repository-url>
cd stockpilot-backend
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your local settings
```

5. **Initialize Database**
```bash
# Create database
createdb stockpilot_db

# Run migrations
alembic upgrade head

# Seed initial data
python -m app.scripts.seed_plans
```

6. **Start Services**

Terminal 1 - FastAPI Server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Celery Worker:
```bash
celery -A app.core.celery_config worker --loglevel=info
```

Terminal 3 - Celery Beat:
```bash
celery -A app.core.celery_config beat --loglevel=info
```

7. **Access Application**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Quick Start

1. **Clone Repository**
```bash
git clone <repository-url>
cd stockpilot-backend
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start Services**
```bash
docker-compose up -d
```

4. **Verify Services**
```bash
docker-compose ps
docker-compose logs -f backend
```

5. **Access Application**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Commands

```bash
# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild images
docker-compose build --no-cache

# Run migrations
docker-compose exec backend alembic upgrade head

# Access database
docker-compose exec postgres psql -U postgres -d stockpilot_db
```

---

## AWS Deployment

### Architecture
- **Compute**: EC2 or ECS
- **Database**: RDS PostgreSQL
- **Cache**: ElastiCache Redis
- **Storage**: S3 for PDFs
- **CDN**: CloudFront
- **Load Balancer**: ALB

### Step 1: Prepare AWS Resources

1. **Create RDS PostgreSQL Instance**
```bash
# Using AWS CLI
aws rds create-db-instance \
  --db-instance-identifier stockpilot-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password <strong-password> \
  --allocated-storage 20 \
  --publicly-accessible false
```

2. **Create ElastiCache Redis Cluster**
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id stockpilot-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

3. **Create S3 Bucket**
```bash
aws s3 mb s3://stockpilot-pdfs-<account-id>
```

### Step 2: Deploy with ECS

1. **Create ECR Repository**
```bash
aws ecr create-repository --repository-name stockpilot-backend
```

2. **Build and Push Docker Image**
```bash
# Build image
docker build -t stockpilot-backend .

# Tag image
docker tag stockpilot-backend:latest <account-id>.dkr.ecr.<region>.amazonaws.com/stockpilot-backend:latest

# Push to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/stockpilot-backend:latest
```

3. **Create ECS Task Definition**
```json
{
  "family": "stockpilot-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "stockpilot-backend",
      "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/stockpilot-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql+psycopg://postgres:<password>@<rds-endpoint>:5432/stockpilot_db"
        },
        {
          "name": "CELERY_BROKER_URL",
          "value": "redis://<redis-endpoint>:6379/0"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/stockpilot-backend",
          "awslogs-region": "<region>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

4. **Create ECS Service**
```bash
aws ecs create-service \
  --cluster stockpilot-cluster \
  --service-name stockpilot-backend \
  --task-definition stockpilot-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=stockpilot-backend,containerPort=8000
```

### Step 3: Configure Domain and SSL

1. **Create Route 53 Record**
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id <zone-id> \
  --change-batch file://change-batch.json
```

2. **Create SSL Certificate**
```bash
aws acm request-certificate \
  --domain-name api.stockpilot.com \
  --validation-method DNS
```

---

## Kubernetes Deployment

### Prerequisites
- kubectl configured
- Helm 3+
- Kubernetes cluster (EKS, GKE, or AKS)

### Step 1: Create Kubernetes Manifests

**deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stockpilot-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: stockpilot-backend
  template:
    metadata:
      labels:
        app: stockpilot-backend
    spec:
      containers:
      - name: backend
        image: <account-id>.dkr.ecr.<region>.amazonaws.com/stockpilot-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: stockpilot-secrets
              key: database-url
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: stockpilot-secrets
              key: celery-broker-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

**service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: stockpilot-backend
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  selector:
    app: stockpilot-backend
```

**ingress.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: stockpilot-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.stockpilot.com
    secretName: stockpilot-tls
  rules:
  - host: api.stockpilot.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: stockpilot-backend
            port:
              number: 80
```

### Step 2: Deploy to Kubernetes

1. **Create Secrets**
```bash
kubectl create secret generic stockpilot-secrets \
  --from-literal=database-url='postgresql+psycopg://...' \
  --from-literal=celery-broker-url='redis://...'
```

2. **Apply Manifests**
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

3. **Verify Deployment**
```bash
kubectl get pods
kubectl get svc
kubectl logs -f deployment/stockpilot-backend
```

4. **Scale Deployment**
```bash
kubectl scale deployment stockpilot-backend --replicas=5
```

---

## Production Checklist

### Security
- [ ] Change SECRET_KEY to a strong random value
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up WAF (Web Application Firewall)
- [ ] Enable database encryption
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting
- [ ] Set up DDoS protection

### Performance
- [ ] Enable database connection pooling
- [ ] Configure Redis caching
- [ ] Set up CDN for static files
- [ ] Enable gzip compression
- [ ] Configure database indexes
- [ ] Set up monitoring and alerting
- [ ] Enable query optimization

### Reliability
- [ ] Set up automated backups
- [ ] Configure database replication
- [ ] Implement health checks
- [ ] Set up auto-scaling
- [ ] Configure load balancing
- [ ] Implement circuit breakers
- [ ] Set up error tracking (Sentry)

### Monitoring
- [ ] Set up CloudWatch/DataDog
- [ ] Configure log aggregation
- [ ] Set up performance monitoring
- [ ] Configure uptime monitoring
- [ ] Set up alerting rules
- [ ] Create dashboards

### Compliance
- [ ] Enable audit logging
- [ ] Implement data retention policies
- [ ] Set up GDPR compliance
- [ ] Configure backup retention
- [ ] Document security procedures
- [ ] Conduct security audit

---

## Troubleshooting

### Database Connection Issues
```bash
# Test connection
psql -h <host> -U postgres -d stockpilot_db

# Check connection pool
SELECT count(*) FROM pg_stat_activity;
```

### Redis Connection Issues
```bash
# Test connection
redis-cli -h <host> ping

# Check memory usage
redis-cli info memory
```

### Celery Issues
```bash
# Check worker status
celery -A app.core.celery_config inspect active

# Purge queue
celery -A app.core.celery_config purge

# Check scheduled tasks
celery -A app.core.celery_config inspect scheduled
```

### Performance Issues
```bash
# Check slow queries
SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

# Check indexes
SELECT * FROM pg_stat_user_indexes;
```

---

## Support

For deployment support, contact: devops@stockpilot.com
