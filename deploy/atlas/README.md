# Atlas CMMS Local Deployment

Local Docker deployment of Atlas CMMS for development and testing.

## Prerequisites

- Docker Desktop installed and running
- Ports 8080 and 5433 available

## Quick Start

```bash
# Start Atlas CMMS
cd deploy/atlas
docker-compose up -d

# Watch logs
docker-compose logs -f atlas-app

# Wait ~60 seconds for startup, then test
curl http://localhost:8080/api/health
```

## Default Credentials

**Admin User:**
- Email: `admin@example.com`
- Password: `admin`

**Database:**
- Host: `localhost`
- Port: `5433`
- Database: `atlas_cmms`
- Username: `atlas`
- Password: `atlas_dev_pass`

## Testing Authentication

```bash
# Test login endpoint
curl -X POST http://localhost:8080/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin"
  }'

# Expected response:
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "user": {...}
# }
```

## Management Commands

```bash
# Stop Atlas
docker-compose down

# Stop and remove data (fresh start)
docker-compose down -v

# View application logs
docker-compose logs -f atlas-app

# View database logs
docker-compose logs -f atlas-db

# Check container status
docker-compose ps

# Execute SQL in database
docker exec -it atlas-postgres psql -U atlas -d atlas_cmms
```

## Troubleshooting

**Container won't start:**
```bash
# Check logs
docker-compose logs atlas-app

# Common issue: Port 8080 already in use
# Solution: Stop other services or change port in docker-compose.yml
```

**Database connection errors:**
```bash
# Verify database is healthy
docker-compose ps

# Should show:
# atlas-postgres   Up (healthy)
```

**Authentication fails:**
- Wait 60 seconds after startup for database migrations
- Check logs: `docker-compose logs atlas-app | grep -i migration`
- Default admin account is created on first startup

## API Endpoints

Base URL: `http://localhost:8080/api`

**Authentication:**
- `POST /auth/signin` - Login (get JWT token)
- `POST /auth/signup` - Register new user

**Work Orders:**
- `GET /work-orders` - List work orders
- `POST /work-orders` - Create work order
- `GET /work-orders/{id}` - Get work order details
- `PUT /work-orders/{id}` - Update work order
- `DELETE /work-orders/{id}` - Delete work order
- `POST /work-orders/search` - Search work orders

**Assets:**
- `GET /assets` - List assets
- `POST /assets` - Create asset
- `GET /assets/{id}` - Get asset details

**Users:**
- `GET /users` - List users (admin only)
- `POST /users` - Create user (admin only)

## Next Steps

After successful deployment:
1. Test authentication flow manually
2. Implement AtlasClient in `agent_factory/integrations/atlas/client.py`
3. Test AtlasClient with live Atlas instance
4. Wire up work order endpoints in `agent_factory/api/routers/work_orders.py`

## Notes

- This configuration is for **development only**
- Uses simplified setup (no MinIO file storage)
- File uploads disabled (work orders still work)
- For production deployment on VPS, see Phase 2 plan
