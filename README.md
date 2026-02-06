# Transaction Aggregation System

A high-performance, asynchronous backend service built with FastAPI that ingests transaction data from CSV files, aggregates it by payment method and day, and provides a REST API for querying statistical data. The system employs a dual-storage architecture using Redis for hot data and MongoDB for historical persistence.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Redis Key Design](#redis-key-design)
- [Data Flow](#data-flow)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)

---

## Architecture Overview

The system implements a **multi-layered asynchronous architecture** with three concurrent background tasks:

```
CSV File → Redis Queue → Aggregation Engine → Redis (Hot) + MongoDB (Historical) → REST API
```

### Key Design Principles

1. **Fully Asynchronous**: All I/O operations use `async/await` to prevent blocking the FastAPI event loop
2. **Dual Storage Strategy**: Redis for recent data (configurable cutoff), MongoDB for historical records
3. **Background Task Orchestration**: Three independent workers running concurrently
4. **Graceful Shutdown**: Proper cleanup with configurable timeouts and force-shutdown fallback
5. **Type Safety**: Pydantic models for data validation and serialization

---

## Project Structure

```
AppBackUp/
├── main.py                          # Application entry point and FastAPI setup
├── AppConfig.py                     # Configuration management (Pydantic Settings)
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container image definition
├── docker-compose.yml               # Multi-container orchestration
├── transactions_1_month.csv         # Sample transaction data
│
├── Api/                             # REST API Layer
│   ├── Router/
│   │   └── StatsRouter.py          # /stats endpoint definition
│   ├── Services/
│   │   └── StatsServices.py        # Business logic for stats retrieval
│   └── Models/
│       └── ApiDailyAggregateResponse.py  # API response schema
│
├── AppBuilder/                      # Application Lifecycle Management
│   ├── AppBuilder.py               # Startup/shutdown orchestration
│   └── AppStateBuilder.py          # Dependency injection and state initialization
│
├── BackgroundTask/                  # Asynchronous Workers
│   ├── DataImporter.py             # CSV → Redis Queue
│   ├── DataAggregator.py           # Queue → Redis Aggregates
│   ├── DataDumper.py               # Redis → MongoDB Persistence
│   ├── CancellationToken.py        # Shutdown signal coordination
│   └── CriticalTaskDecorator.py    # Error handling decorator
│
├── Db/                              # Data Persistence Layer
│   ├── Schema.py                   # MongoDB collection schemas and indices
│   └── Repositories/
│       ├── BaseRepository.py       # Generic MongoDB operations
│       └── DailyAggregatesRepository.py  # Aggregate-specific queries
│
├── Models/                          # Domain Models
│   ├── Transaction.py              # Transaction record schema
│   └── DailyAggregate.py           # Aggregated daily data schema
│
├── RedisHelper/                     # Redis Utilities
│   └── RedisServices.py            # Key scanning and aggregate retrieval
│
├── Exceptions/                      # Error Handling
│   ├── Exceptions.py               # Custom exception types
│   └── ExceptionHandlers.py        # FastAPI exception handlers
│
└── HelperMethods.py                 # Shared utilities (key design, dependency injection)
```

---

## Core Components

### 1. **DataImporter** (Background Task)
**File**: `BackgroundTask/DataImporter.py`

**Responsibility**: Stream CSV transactions into Redis queue with rate limiting

**Key Features**:
- Asynchronous file reading with `aiofiles`
- Respects `sleep_ms` field to avoid overwhelming the queue
- Uses `lpush` for FIFO queue semantics
- Runs once on startup and completes when CSV is fully processed

**Flow**:
```python
CSV Line → Parse Transaction → Push to Redis Queue → Sleep(sleep_ms)
```

---

### 2. **DataAggregator** (Background Task)
**File**: `BackgroundTask/DataAggregator.py`

**Responsibility**: Consume transactions from queue and update Redis aggregates

**Key Features**:
- Blocking pop with timeout (`brpop`) to avoid busy-waiting
- Atomic increments using `hincrbyfloat` for thread safety
- Runs continuously until cancellation token is set
- Respects graceful shutdown signals

**Aggregation Logic**:
```python
Transaction → Extract (Date, Type, PaymentMethod, Amount)
              ↓
              Build Redis Key: agg:{YYYY-MM-DD}:{type}s
              ↓
              HINCRBYFLOAT key payment_method amount
```

---

### 3. **DataDumper** (Background Task)
**File**: `BackgroundTask/DataDumper.py`

**Responsibility**: Periodically persist Redis aggregates to MongoDB

**Key Features**:
- Scheduled execution every N seconds (configurable via `DumperTaskScheduleInterval`)
- Scans all aggregate keys in Redis
- Bulk upsert operations for efficiency
- Logs dump statistics (inserted, updated, matched)

**Persistence Strategy**:
```python
Every 10s:
  1. Scan Redis for agg:* keys
  2. Fetch all aggregate hashes
  3. Bulk upsert to MongoDB (Date+Type unique constraint)
  4. Log operation results
```

---

### 4. **StatsRouter** (API Endpoint)
**File**: `Api/Router/StatsRouter.py`

**Endpoint**: `GET /stats?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`

**Responsibility**: Query aggregated statistics across date ranges

**Smart Data Retrieval**:
- **Recent Data** (within cutoff): Fetched from Redis
- **Historical Data** (before cutoff): Fetched from MongoDB
- **Hybrid Queries**: Seamlessly combines both sources

**Example Response**:
```json
{
  "data": {
    "2026-01-01": {
      "deposits": {
        "paypal": 52763.85,
        "crypto": 48123.48,
        "visa": 48992.1
      },
      "withdrawals": {
        "crypto": 75816.03,
        "visa": 55796.91
      }
    }
  }
}
```

---

### 5. **AppBuilder** (Lifecycle Manager)
**File**: `AppBuilder/AppBuilder.py`

**Responsibility**: Orchestrate application startup and shutdown

**Startup Sequence**:
1. Initialize Redis connection
2. Initialize MongoDB connection
3. Spawn three background tasks (Importer, Aggregator, Dumper)
4. Store tasks in `app.state` for lifecycle management

**Graceful Shutdown**:
```python
1. Set cancellation token (stops Aggregator + Dumper loops)
2. Wait for tasks to finish (timeout: GracefulShutDownTimeout)
3. Close Redis connection
4. Close MongoDB connection
5. If timeout exceeded → Force shutdown
```

---

### 6. **MongoDB Schema** (Data Persistence)
**File**: `Db/Schema.py`

**Collection**: `DailyAggregates`

**Document Schema**:
```javascript
{
  _id: ObjectId,
  Date: "2026-01-15",           // YYYY-MM-DD format
  Type: "deposits",             // "deposits" | "withdrawals"
  TotalAmount: {
    "paypal": 12345.67,
    "crypto": 9876.54,
    "visa": 5432.10,
    // ... other payment methods
  },
  LastUpdated: ISODate("2026-01-15T10:30:00Z")
}
```

**Indices**:
- `idx_date`: Single field index on `Date` (range queries)
- `idx_type`: Single field index on `Type` (filtering)
- `idx_date_type`: **Unique compound index** on `(Date, Type)` (prevents duplicates)

**Validation**:
- `Date`: Must match `YYYY-MM-DD` pattern
- `Type`: Enum constraint (`deposits` | `withdrawals`)
- `TotalAmount`: Object with double values

---

## Redis Key Design

### Key Pattern
```
agg:{Date}:{Type}s
```

**Examples**:
- `agg:2026-01-15:deposits`
- `agg:2026-01-15:withdrawals`
- `agg:2026-01-20:deposits`

### Data Structure: **Hash**
```
Key: agg:2026-01-15:deposits

Hash Fields:
  paypal  → "52763.85"
  crypto  → "48123.48"
  visa    → "48992.10"
  wire    → "41802.69"
```

### Design Rationale

**Why Hashes?**
1. **Atomic Operations**: `HINCRBYFLOAT` allows concurrent updates without race conditions
2. **Memory Efficiency**: Single hash per day+type instead of separate keys per payment method
3. **Atomic Retrieval**: `HGETALL` fetches all payment methods in one operation
4. **Expiration Support**: Can set TTL on entire hash (if needed)

**Why This Key Structure?**
1. **Lexicographic Ordering**: Date-first enables efficient range scans
2. **Type Isolation**: Separate keys for deposits/withdrawals simplify aggregation
3. **Pattern Matching**: `SCAN` with `agg:2026-01-*` for date-based queries
4. **Conflict Prevention**: Impossible to confuse different transaction types

**Search Patterns**:
```python
# All aggregates
GetRedisKeyDesignPattern()  → "agg:*"

# Specific day (all types)
GetRedisKeyDesignPattern(Day="2026-01-15")  → "agg:2026-01-15:*"

# Specific day and type
GetRedisKeyDesignPattern(Day="2026-01-15", TransactionType="deposit")  
  → "agg:2026-01-15:deposits"
```

---

## Data Flow

### Complete Transaction Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CSV FILE                                   │
│  timestamp,type,payment_method,amount,sleep_ms                      │
│  2026-01-15T10:30:00,deposit,paypal,1234.56,100                     │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  │ [1] DataImporter reads line-by-line
                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      REDIS QUEUE                                    │
│  Key: TransactionQueue                                              │
│  Type: List                                                          │
│  Operation: LPUSH (head insertion)                                  │
│                                                                      │
│  ["{"Timestamp":"2026-01-15T10:30:00",...}", ...]                   │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  │ [2] DataAggregator continuously polls with BRPOP
                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    REDIS AGGREGATES (Hot Data)                      │
│  Keys:                                                               │
│    agg:2026-01-15:deposits                                          │
│    agg:2026-01-15:withdrawals                                       │
│                                                                      │
│  Hash Structure:                                                     │
│    paypal  → 52763.85                                               │
│    crypto  → 48123.48                                               │
│    visa    → 48992.10                                               │
│                                                                      │
│  Operation: HINCRBYFLOAT agg:2026-01-15:deposits paypal 1234.56     │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  │ [3] DataDumper scans every 10 seconds
                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 MONGODB (Historical Persistence)                    │
│  Collection: DailyAggregates                                        │
│                                                                      │
│  Document:                                                           │
│  {                                                                   │
│    _id: ObjectId("..."),                                            │
│    Date: "2026-01-15",                                              │
│    Type: "deposits",                                                │
│    TotalAmount: {                                                   │
│      paypal: 52763.85,                                              │
│      crypto: 48123.48,                                              │
│      visa: 48992.10                                                 │
│    },                                                                │
│    LastUpdated: ISODate("2026-01-15T10:30:00Z")                    │
│  }                                                                   │
│                                                                      │
│  Operation: Bulk Upsert (Date + Type unique constraint)            │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  │ [4] StatsService queries on API request
                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                          REST API                                    │
│  GET /stats?from_date=2026-01-01&to_date=2026-01-31                │
│                                                                      │
│  Query Logic:                                                        │
│    1. Calculate cutoff date (today - CutOffDays)                    │
│    2. For dates >= cutoff: Fetch from Redis                         │
│    3. For dates < cutoff: Fetch from MongoDB                        │
│    4. Merge results and return                                      │
│                                                                      │
│  Response: JSON with nested structure                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Diagram

```
┌──────────────┐
│   main.py    │  FastAPI Lifespan
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────┐
│                    AppStateBuilder                           │
│  • Creates Redis connection                                  │
│  • Creates MongoDB connection                                │
│  • Spawns background tasks                                   │
└──────┬───────────────────────────────────────────────────────┘
       │
       ├─────────────┬─────────────┬─────────────┐
       ↓             ↓             ↓             ↓
  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Redis   │  │ MongoDB  │  │   Task   │  │   Task   │
  │ Client  │  │ Client   │  │ Pool [3] │  │ Manager  │
  └─────────┘  └──────────┘  └──────────┘  └──────────┘
       │             │             │
       │             │             │
       ↓             ↓             ↓
  ┌─────────────────────────────────────────────────────┐
  │           Background Tasks (Concurrent)             │
  │                                                      │
  │  [DataImporter]     [DataAggregator]  [DataDumper]  │
  │       ↓                    ↓                ↓        │
  │   CSV File          Redis Queue      Redis → Mongo  │
  └─────────────────────────────────────────────────────┘
                       │
                       ↓
              ┌─────────────────┐
              │  StatsRouter    │
              │  (REST API)     │
              └─────────────────┘
```

### Concurrency Model

**Three Independent Workers**:
1. **DataImporter**: Runs once, completes when CSV is fully loaded
2. **DataAggregator**: Infinite loop with `brpop` blocking, exits on cancellation token
3. **DataDumper**: Infinite loop with `sleep` intervals, exits on cancellation token

**Thread Safety**:
- Redis operations are atomic (`HINCRBYFLOAT`, `LPUSH`, `BRPOP`)
- MongoDB bulk operations use transactions internally
- No shared mutable state between tasks (except cancellation token)

---

## API Documentation

### Endpoint: Get Statistics

**URL**: `GET /stats`

**Query Parameters**:
| Parameter | Type | Format | Required | Description |
|-----------|------|--------|----------|-------------|
| `from_date` | string | YYYY-MM-DD | Yes | Start date (inclusive) |
| `to_date` | string | YYYY-MM-DD | Yes | End date (inclusive) |

**Example Request**:
```bash
curl "http://localhost:8000/stats?from_date=2026-01-01&to_date=2026-01-07"
```

**Response Schema**:
```json
{
  "data": {
    "<date>": {
      "deposits": {
        "<payment_method>": <float>,
        ...
      },
      "withdrawals": {
        "<payment_method>": <float>,
        ...
      }
    },
    ...
  }
}
```

**Success Response (200)**:
```json
{
  "data": {
    "2026-01-01": {
      "deposits": {
        "paypal": 52763.85,
        "crypto": 48123.48,
        "visa": 48992.1,
        "wire": 41802.69,
        "apple_pay": 55609.74
      },
      "withdrawals": {
        "crypto": 75816.03,
        "visa": 55796.91,
        "paypal": 38878.71,
        "wire": 27937.32,
        "apple_pay": 46718.82
      }
    },
    "2026-01-02": {
      "deposits": {
        "crypto": 36970.83,
        "visa": 62546.07
      },
      "withdrawals": {
        "visa": 65824.89,
        "wire": 81960.93
      }
    }
  }
}
```

**Error Response (400)**:
```json
{
  "detail": "From parameter must be before or equal to To"
}
```

**Data Source Strategy**:
```python
# Example: Query 2026-01-01 to 2026-01-31
# Assume today is 2026-01-20, CutOffDays = 7
# Cutoff date = 2026-01-13

Dates 2026-01-01 to 2026-01-12:  ← MongoDB (historical)
Dates 2026-01-13 to 2026-01-31:  ← Redis (hot data)
```

---

## Configuration

### Environment Variables

Defined in `docker-compose.yml` and loaded via `AppConfig.py` (Pydantic Settings):

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RedisHost` | string | `redis` | Redis server hostname |
| `RedisPort` | int | `6379` | Redis server port |
| `RedisTransactionQueueKeyName` | string | `TransactionQueue` | Redis list key for transaction queue |
| `CsvFilePath` | string | `/app/data/transactions_1_month.csv` | Path to CSV file inside container |
| `MongoDbUri` | string | `mongodb://mongodb:27017/` | MongoDB connection string |
| `MongoDbName` | string | `TransactionsDb` | MongoDB database name |
| `GracefulShutDownTimeout` | int | `10` | Seconds to wait for graceful shutdown |
| `ForceShutDownTimeout` | int | `2` | Seconds before force termination |
| `TransactionCkeckTimeout` | float | `0.5` | Seconds for `BRPOP` timeout (polling interval) |
| `CutOffDays` | int | `7` | Days to keep in Redis (older data in MongoDB) |
| `CutOffMinutes` | int | `0` | Additional minutes for cutoff calculation |
| `CutOffSeconds` | int | `0` | Additional seconds for cutoff calculation |
| `DumperTaskScheduleInterval` | int | `10` | Seconds between MongoDB dump operations |

### Cutoff Date Calculation

```python
cutoff_date = today - timedelta(
    days=CutOffDays, 
    minutes=CutOffMinutes, 
    seconds=CutOffSeconds
)
```

**Example**:
- Today: `2026-01-20`
- `CutOffDays=7`, `CutOffMinutes=0`, `CutOffSeconds=0`
- Cutoff: `2026-01-13`
- Redis contains: `2026-01-13` onwards
- MongoDB contains: Everything before `2026-01-13`

---

## Running the Project

See [DockerGuide.md](./DockerGuide.md) for detailed instructions on:
- Starting the application
- Viewing logs
- Testing the API
- Debugging with database shells
- Running tests

**Quick Start**:
```bash
# Build and start all services
docker-compose up --build

# Test the API
curl "http://localhost:8000/stats?from_date=2026-01-01&to_date=2026-01-31" | jq

# View logs
docker-compose logs -f app

