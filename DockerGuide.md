# Docker Guide

Complete guide for running, debugging, and testing the Transaction Aggregation System using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Commands Reference](#docker-commands-reference)
- [Viewing Logs](#viewing-logs)
- [Database Access](#database-access)
- [Testing the API](#testing-the-api)
- [Common Issues & Solutions](#common-issues--solutions)
- [Running Tests](#running-tests)
- [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher

### Verify Installation

```bash
# Check Docker version
docker --version
# Expected: Docker version 20.10.x or higher

# Check Docker Compose version
docker-compose --version
# Expected: Docker Compose version 2.x.x or higher

# Verify Docker is running
docker ps
# Should show a list of running containers (may be empty)
```

---

## Quick Start

### 1. Clone and Navigate to Project

```bash
cd /path/to/AppBackUp
```

### 2. Start All Services

```bash
# Build images and start containers
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

**What happens during startup:**
1. ✅ Builds FastAPI application Docker image
2. ✅ Pulls Redis 7 Alpine image
3. ✅ Pulls MongoDB 7 image
4. ✅ Creates network: `transaction-network`
5. ✅ Creates volume: `mongodb_data`
6. ✅ Starts Redis container (waits for healthcheck)
7. ✅ Starts MongoDB container (waits for healthcheck)
8. ✅ Starts FastAPI app container
9. ✅ Begins CSV import in background
10. ✅ API available at http://localhost:8000

### 3. Verify Services Are Running

```bash
docker-compose ps
```

**Expected Output:**
```
NAME                   IMAGE              STATUS         PORTS
transaction-app        appbackup-app      Up 10 seconds  0.0.0.0:8000->8000/tcp
transaction-mongodb    mongo:7            Up 15 seconds  0.0.0.0:27017->27017/tcp
transaction-redis      redis:7-alpine     Up 15 seconds  0.0.0.0:6379:6379/tcp
```

### 4. Test the API

```bash
# Basic health check
curl http://localhost:8000/

# Query statistics
curl "http://localhost:8000/stats?from_date=2026-01-01&to_date=2026-01-07" | jq
```

### 5. Stop All Services

```bash
# Stop containers (preserve data)
docker-compose down

# Stop and remove volumes (delete all data)
docker-compose down -v
```

---

## Docker Commands Reference

### Container Management

#### Start Services

```bash
# Build and start (foreground - see logs)
docker-compose up --build

# Start in background
docker-compose up -d

# Rebuild specific service
docker-compose up -d --build app

# Force recreate containers
docker-compose up -d --force-recreate
```

#### Stop Services

```bash
# Stop containers (data persists)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (deletes all data)
docker-compose down -v

# Stop and remove containers + images
docker-compose down --rmi all
```

#### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart app
docker-compose restart mongodb
docker-compose restart redis
```

#### View Container Status

```bash
# List running containers
docker-compose ps

# Detailed container info
docker-compose ps -a

# View resource usage (CPU, Memory)
docker stats transaction-app transaction-redis transaction-mongodb
```

### Service-Specific Commands

#### Application Container

```bash
# Execute command in app container
docker exec -it transaction-app bash

# View Python version
docker exec transaction-app python --version

# List files in /app
docker exec transaction-app ls -la /app

# Check environment variables
docker exec transaction-app env | grep -E 'Redis|Mongo'
```

#### Redis Container

```bash
# Access Redis CLI
docker exec -it transaction-redis redis-cli

# Inside Redis CLI:
PING                          # Test connection
KEYS *                        # List all keys
LLEN TransactionQueue         # Check queue length
LRANGE TransactionQueue 0 5   # View first 5 transactions
HGETALL agg:2026-01-01:deposits  # View specific aggregate

# One-liner commands
docker exec transaction-redis redis-cli KEYS "agg:*"
docker exec transaction-redis redis-cli LLEN TransactionQueue
docker exec transaction-redis redis-cli INFO memory
```

#### MongoDB Container

```bash
# Access MongoDB shell
docker exec -it transaction-mongodb mongosh

# Inside mongosh:
show dbs                              # List databases
use TransactionsDb                    # Switch to database
show collections                      # List collections
db.DailyAggregates.find().limit(5)    # View first 5 documents
db.DailyAggregates.countDocuments()   # Count total documents

# One-liner commands
docker exec transaction-mongodb mongosh --eval "db.DailyAggregates.countDocuments()"
docker exec transaction-mongodb mongosh --eval "db.DailyAggregates.find().limit(3)"
```

---

## Viewing Logs

### Real-Time Logs

```bash
# Follow logs for all services
docker-compose logs -f

# Follow logs for specific service
docker-compose logs -f app
docker-compose logs -f redis
docker-compose logs -f mongodb

# Follow with timestamps
docker-compose logs -f --timestamps app
```

### Historical Logs

```bash
# View last 100 lines
docker-compose logs --tail=100 app

# View logs from specific time
docker-compose logs --since 2024-01-15T10:00:00 app

# View logs until specific time
docker-compose logs --until 2024-01-15T12:00:00 app
```

### Filtering Logs

```bash
# Search for errors
docker-compose logs app | grep -i error

# Search for specific pattern
docker-compose logs app | grep "Dumped.*records"

# Export logs to file
docker-compose logs app > app_logs.txt
```

### Key Log Messages to Monitor

**Successful Startup:**
```
✅ Test Worked
✅ Redis connection established
✅ MongoDB connection established
✅ Data Imported Successfully from CSV File
```

**MongoDB Dump Operation:**
```
Dumped 60 records in Database:
  - Inserted Documents 0
  - Upserted Documents 0
  - Matched Documents 60
  - Modified Documents 60
```

**Graceful Shutdown:**
```
✅ DataImporter was Cancelled
✅ DataAggregator was Cancelled
✅ DataDumper Finished and shutdown completely
✅ Redis connection closed
✅ MongoDb connection closed
```

---

## Database Access

### Redis Inspection

#### Connect to Redis CLI

```bash
docker exec -it transaction-redis redis-cli
```

#### Useful Redis Commands

```redis
# Check connection
PING

# View all keys
KEYS *

# View aggregate keys only
KEYS agg:*

# Check transaction queue
LLEN TransactionQueue
LRANGE TransactionQueue 0 10

# View specific aggregate
HGETALL agg:2026-01-15:deposits
HGETALL agg:2026-01-15:withdrawals

# Get all payment methods for a day
HKEYS agg:2026-01-15:deposits

# Get specific payment method total
HGET agg:2026-01-15:deposits paypal

# Memory usage
INFO memory

# Database size
DBSIZE

# Monitor commands in real-time
MONITOR

# Exit Redis CLI
EXIT
```

### MongoDB Inspection

#### Connect to MongoDB Shell

```bash
docker exec -it transaction-mongodb mongosh
```

#### Useful MongoDB Commands

```javascript
// Switch to database
use TransactionsDb

// List collections
show collections

// Count documents
db.DailyAggregates.countDocuments()

// View all documents (limited)
db.DailyAggregates.find().limit(5).pretty()

// Query by date
db.DailyAggregates.find({ Date: "2026-01-15" }).pretty()

// Query by date range
db.DailyAggregates.find({
  Date: { $gte: "2026-01-01", $lte: "2026-01-07" }
}).sort({ Date: 1 })

// View deposits only
db.DailyAggregates.find({ Type: "deposits" }).limit(5)

// Aggregate total deposits
db.DailyAggregates.aggregate([
  { $match: { Type: "deposits" } },
  { $group: { _id: null, total: { $sum: 1 } } }
])

// View indices
db.DailyAggregates.getIndexes()

// Collection stats
db.DailyAggregates.stats()

// Exit mongosh
exit
```

### Using GUI Tools

#### MongoDB Compass (Recommended)

1. Download: https://www.mongodb.com/products/tools/compass
2. Connection String: `mongodb://localhost:27017`
3. Database: `TransactionsDb`
4. Collection: `DailyAggregates`

#### RedisInsight (Optional)

1. Download: https://redis.io/insight/
2. Host: `localhost`
3. Port: `6379`

---

## Testing the API

### Using cURL

#### Basic Queries

```bash
# Health check
curl http://localhost:8000/

# Query single day
curl "http://localhost:8000/stats?from_date=2026-01-15&to_date=2026-01-15"

# Query date range
curl "http://localhost:8000/stats?from_date=2026-01-01&to_date=2026-01-31"

# Pretty print with jq
curl "http://localhost:8000/stats?from_date=2026-01-01&to_date=2026-01-07" | jq

# Save response to file
curl "http://localhost:8000/stats?from_date=2026-01-01&to_date=2026-01-31" > stats.json
```

#### Error Cases

```bash
# Invalid date format
curl "http://localhost:8000/stats?from_date=2026/01/01&to_date=2026-01-31"

# from_date after to_date
curl "http://localhost:8000/stats?from_date=2026-01-31&to_date=2026-01-01"

# Missing parameter
curl "http://localhost:8000/stats?from_date=2026-01-01"
```

### Using HTTPie (Alternative)

```bash
# Install HTTPie
pip install httpx[cli]

# Query with HTTPie
http GET "localhost:8000/stats" from_date==2026-01-01 to_date==2026-01-31
```

### Using Python Script

```python
import requests
import json

# Query API
response = requests.get(
    "http://localhost:8000/stats",
    params={"from_date": "2026-01-01", "to_date": "2026-01-31"}
)

# Check status
print(f"Status: {response.status_code}")

# Pretty print JSON
print(json.dumps(response.json(), indent=2))

# Access specific data
data = response.json()["data"]
for date, aggregates in data.items():
    print(f"\n{date}:")
    if "deposits" in aggregates:
        total_deposits = sum(aggregates["deposits"].values())
        print(f"  Total Deposits: ${total_deposits:,.2f}")
    if "withdrawals" in aggregates:
        total_withdrawals = sum(aggregates["withdrawals"].values())
        print(f"  Total Withdrawals: ${total_withdrawals:,.2f}")
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils  # Ubuntu/Debian
brew install apache2                # macOS

# Run 1000 requests with 10 concurrent
ab -n 1000 -c 10 "http://localhost:8000/stats?from_date=2026-01-01&to_date=2026-01-31"
```

---

## Common Issues & Solutions

### Issue: Container Fails to Start

**Symptom**: `docker-compose up` fails

**Solutions**:

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up

# Check port conflicts
sudo lsof -i :8000  # FastAPI
sudo lsof -i :6379  # Redis
sudo lsof -i :27017 # MongoDB
```

### Issue: MongoDB Exit Code 14

**Symptom**: `container transaction-mongodb exited (14)`

**Solution**:

```yaml
# Add to docker-compose.yml under mongodb service
tmpfs:
  - /tmp
```

**Or clean volume and restart:**

```bash
docker-compose down -v
docker volume rm appbackup_mongodb_data
docker-compose up -d
```

### Issue: CSV Import Not Starting

**Symptom**: No logs about data import

**Diagnosis**:

```bash
# Check if CSV file is mounted
docker exec transaction-app ls -la /app/data/

# Check environment variable
docker exec transaction-app env | grep CsvFilePath
```

**Solution**: Ensure CSV is in project root and docker-compose.yml has:

```yaml
volumes:
  - ./transactions_1_month.csv:/app/data/transactions_1_month.csv:ro
```

### Issue: API Returns Empty Data

**Symptom**: `/stats` returns `{"data": {}}`

**Diagnosis**:

```bash
# Check if import completed
docker-compose logs app | grep "Data Imported"

# Check Redis queue
docker exec transaction-redis redis-cli LLEN TransactionQueue

# Check Redis aggregates
docker exec transaction-redis redis-cli KEYS "agg:*"

# Check MongoDB documents
docker exec transaction-mongodb mongosh --eval "db.DailyAggregates.countDocuments()"
```

**Solutions**:

1. Wait for import to complete (check logs)
2. Verify date range matches CSV data
3. Ensure background tasks are running

### Issue: Duplicate Logs

**Symptom**: Every log line appears twice

**Solution**:

Add to `docker-compose.yml` under app service:

```yaml
environment:
  - PYTHONUNBUFFERED=1
```

### Issue: Network Errors

**Symptom**: App can't connect to Redis/MongoDB

**Diagnosis**:

```bash
# Check network
docker network ls
docker network inspect transaction-network

# Check if services are on same network
docker inspect transaction-app | grep -A 10 Networks
docker inspect transaction-redis | grep -A 10 Networks
```

**Solution**: All services should be on `transaction-network`

---

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx
```

### Unit Tests (Example Structure)

Create `tests/test_api.py`:

```python
import pytest
from httpx import AsyncClient
from main import App

@pytest.mark.asyncio
async def test_stats_endpoint_success():
    async with AsyncClient(app=App, base_url="http://test") as client:
        response = await client.get(
            "/stats",
            params={"from_date": "2026-01-01", "to_date": "2026-01-07"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

@pytest.mark.asyncio
async def test_stats_invalid_date_format():
    async with AsyncClient(app=App, base_url="http://test") as client:
        response = await client.get(
            "/stats",
            params={"from_date": "2026/01/01", "to_date": "2026-01-07"}
        )
        assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_stats_from_after_to():
    async with AsyncClient(app=App, base_url="http://test") as client:
        response = await client.get(
            "/stats",
            params={"from_date": "2026-01-31", "to_date": "2026-01-01"}
        )
        assert response.status_code == 400
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/test_api.py

# Verbose output
pytest -v tests/
```

### Integration Tests with Docker

```bash
# Start services
docker-compose up -d

# Wait for import to complete
sleep 30

# Run integration tests
pytest tests/integration/

# Cleanup
docker-compose down -v
```

### Manual Verification Script

Create `scripts/verify_data.py`:

```python
import asyncio
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

async def verify_system():
    # Connect to Redis
    r = await redis.Redis(host='localhost', port=6379)
    
    # Check queue
    queue_len = await r.llen('TransactionQueue')
    print(f"✅ Redis Queue Length: {queue_len}")
    
    # Check aggregates
    agg_keys = []
    async for key in r.scan_iter(match='agg:*'):
        agg_keys.append(key.decode())
    print(f"✅ Redis Aggregate Keys: {len(agg_keys)}")
    
    await r.close()
    
    # Connect to MongoDB
    mongo_client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = mongo_client.TransactionsDb
    
    # Check documents
    doc_count = await db.DailyAggregates.count_documents({})
    print(f"✅ MongoDB Documents: {doc_count}")
    
    # Sample document
    sample = await db.DailyAggregates.find_one()
    if sample:
        print(f"✅ Sample Document: {sample['Date']} - {sample['Type']}")
    
    mongo_client.close()

if __name__ == "__main__":
    asyncio.run(verify_system())
```

Run:

```bash
docker-compose up -d
sleep 30
python scripts/verify_data.py
```

---

## Production Deployment

### Security Hardening

1. **MongoDB Authentication**:

```yaml
mongodb:
  environment:
    - MONGO_INITDB_ROOT_USERNAME=admin
    - MONGO_INITDB_ROOT_PASSWORD=secure_password
```

Update app connection string:
```
MongoDbUri=mongodb://admin:secure_password@mongodb:27017/
```

2. **Redis Password**:

```yaml
redis:
  command: redis-server --requirepass your_redis_password
```

Update app:
```
RedisPassword=your_redis_password
```

3. **Remove Port Exposure**:

```yaml
# Remove public port bindings
# ports:
#   - "6379:6379"
#   - "27017:27017"
```

### Performance Tuning

```yaml
app:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G

mongodb:
  command: mongod --wiredTigerCacheSizeGB 2

redis:
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

### Logging Configuration

```yaml
app:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

### Health Checks

Already configured in `docker-compose.yml`:

```yaml
app:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## Useful Docker Compose Commands Summary

```bash
# Build
docker-compose build
docker-compose build --no-cache

# Start
docker-compose up
docker-compose up -d
docker-compose up --build

# Stop
docker-compose stop
docker-compose down
docker-compose down -v

# Logs
docker-compose logs
docker-compose logs -f app
docker-compose logs --tail=100 app

# Status
docker-compose ps
docker-compose ps -a

# Restart
docker-compose restart
docker-compose restart app

# Execute
docker exec -it transaction-app bash
docker exec -it transaction-redis redis-cli
docker exec -it transaction-mongodb mongosh

# Cleanup
docker-compose down --rmi all
docker system prune -a
docker volume prune
```

---

## Troubleshooting Checklist

✅ **Before starting:**
- [ ] Docker is running
- [ ] Ports 8000, 6379, 27017 are free
- [ ] CSV file exists: `transactions_1_month.csv`

✅ **After starting:**
- [ ] All 3 containers are running: `docker-compose ps`
- [ ] No error logs: `docker-compose logs`
- [ ] API responds: `curl http://localhost:8000/`
- [ ] Redis has keys: `docker exec transaction-redis redis-cli KEYS "*"`
- [ ] MongoDB has data: `docker exec transaction-mongodb mongosh --eval "db.DailyAggregates.countDocuments()"`

✅ **If problems:**
- [ ] Check logs: `docker-compose logs -f`
- [ ] Rebuild: `docker-compose down -v && docker-compose up --build`
- [ ] Verify network: `docker network inspect transaction-network`
- [ ] Check disk space: `df -h`

---

## Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Redis Commands**: https://redis.io/commands
- **MongoDB Manual**: https://docs.mongodb.com
- **Docker Compose**: https://docs.docker.com/compose/

---

**Happy Coding! 🚀**
