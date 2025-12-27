# Atlas CMMS API Documentation

## Overview
Atlas CMMS is a self-hosted maintenance management system (Spring Boot/Java backend).

**Repository**: https://github.com/Grashjs/cmms
**Demo**: https://atlas-cmms.com

## Key Features
- Work order management (create, assign, track, automate)
- Asset tracking with downtime monitoring
- Inventory management with stock alerts
- User roles and permissions
- Location management with Google Maps integration

## API Architecture

### Technology Stack
- **Backend**: Java Spring Boot
- **Database**: PostgreSQL 16
- **Storage**: MinIO (S3-compatible) or Google Cloud Storage
- **Authentication**: JWT tokens
- **API Port**: 8080 (default)
- **Frontend Port**: 3000 (default)

### Authentication
**Endpoint**: `POST /auth/signin`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "type": "EMAIL"
}
```

**Response**:
```json
{
  "token": "eyJhbGc...",
  "user": { ... }
}
```

**Usage**: Include JWT in Authorization header:
```
Authorization: Bearer eyJhbGc...
```

## Core API Endpoints

### Work Orders

#### Search Work Orders
```
POST /work-orders/search
Content-Type: application/json
Authorization: Bearer {token}

{
  "filterFields": [],
  "criteria": []
}
```

#### Get Work Order by ID
```
GET /work-orders/{id}
Authorization: Bearer {token}
```

#### Create Work Order
```
POST /work-orders
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "Fix Pump #3",
  "description": "Pump making unusual noise",
  "priority": "HIGH",
  "assetId": 123,
  "locationId": 45
}
```

#### Update Work Order
```
PATCH /work-orders/{id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "status": "IN_PROGRESS",
  "assignedToId": 789
}
```

#### Delete Work Order
```
DELETE /work-orders/{id}
Authorization: Bearer {token}
```

#### Get Work Orders by Asset
```
GET /work-orders/asset/{assetId}
Authorization: Bearer {token}
```

### Assets

#### Search Assets
```
POST /assets/search
Content-Type: application/json
Authorization: Bearer {token}

{
  "filterFields": ["name", "description"],
  "criteria": []
}
```

#### Get Asset by ID
```
GET /assets/{id}
Authorization: Bearer {token}
```

#### Get Assets by Location
```
GET /assets/location/{locationId}
Authorization: Bearer {token}
```

### Users

#### Sign Up (Create User)
```
POST /auth/signup
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "securepass",
  "firstName": "John",
  "lastName": "Doe"
}
```

## Docker Deployment

### Services
1. **postgres** - PostgreSQL 16 database (port 5432)
2. **api** - Atlas backend (port 8080)
3. **frontend** - React frontend (port 3000)
4. **minio** - S3-compatible storage (port 9000)

### Environment Variables (.env required)
```bash
# Database
POSTGRES_USER=rootUser
POSTGRES_PWD=mypassword

# MinIO
MINIO_USER=minio
MINIO_PWD=minio123

# JWT
JWT_SECRET_KEY=your_jwt_secret

# URLs
PUBLIC_API_URL=http://localhost:8080
PUBLIC_FRONT_URL=http://localhost:3000

# Email (optional)
ENABLE_EMAIL_NOTIFICATIONS=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PWD=
```

### Deployment for VPS (72.60.175.144)
```yaml
# /deploy/atlas/docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    container_name: rivet_atlas_db
    environment:
      POSTGRES_DB: rivet_atlas
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PWD}
    ports:
      - "5433:5432"  # Use 5433 to avoid conflict with main Neon DB
    volumes:
      - atlas_postgres_data:/var/lib/postgresql/data

  api:
    image: intelloop/atlas-cmms-backend
    container_name: rivet_atlas_api
    depends_on:
      - postgres
      - minio
    environment:
      DB_URL: postgres/rivet_atlas
      DB_USER: ${POSTGRES_USER}
      DB_PWD: ${POSTGRES_PWD}
      PUBLIC_API_URL: http://72.60.175.144:8080
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      MINIO_ENDPOINT: http://minio:9000
      MINIO_ACCESS_KEY: ${MINIO_USER}
      MINIO_SECRET_KEY: ${MINIO_PASSWORD}
      STORAGE_TYPE: minio
    ports:
      - "8080:8080"

  minio:
    image: minio/minio:latest
    container_name: rivet_atlas_minio
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - atlas_minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    command: server --address ":9000" --console-address ":9001" /data

volumes:
  atlas_postgres_data:
  atlas_minio_data:
```

## Integration Notes for Rivet

### Required AtlasClient Methods
```python
class AtlasClient:
    async def create_work_order(self, data: WorkOrderCreate) -> WorkOrder
    async def get_work_order(self, wo_id: str) -> WorkOrder
    async def list_work_orders(self, user_id: str) -> List[WorkOrder]
    async def get_asset(self, asset_id: str) -> Asset
    async def search_assets(self, query: str) -> List[Asset]
    async def create_user(self, email: str, tier: str) -> User
```

### Authentication Flow
1. Admin credentials stored in Agent Factory `.env`
2. Use `/auth/signin` to get JWT token
3. Cache token (refresh every 24h or on 401)
4. Include in all API requests

### Error Handling
- **400**: Bad request (validation error)
- **401**: Unauthorized (token expired)
- **403**: Forbidden (insufficient permissions)
- **404**: Not found
- **422**: Invalid credentials

## Next Steps
1. ✅ Research complete
2. Create Python AtlasClient wrapper
3. Deploy Atlas to VPS 72.60.175.144
4. Wire up Rivet API endpoints
