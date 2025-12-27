# Atlas CMMS Deployment for Rivet MVP

Deploy Atlas CMMS to VPS **72.60.175.144** for Rivet work order management.

## Quick Start

### 1. Prepare Environment

```bash
# SSH into VPS
ssh root@72.60.175.144

# Create deployment directory
mkdir -p /opt/rivet/atlas
cd /opt/rivet/atlas

# Copy deployment files
# (Upload docker-compose.yml and .env from this directory)
```

### 2. Configure Environment

```bash
# Copy and edit .env file
cp .env.example .env
nano .env

# Generate JWT secret
openssl rand -base64 32

# Update .env with:
# - Strong POSTGRES_PWD
# - Strong MINIO_PWD
# - Generated JWT_SECRET_KEY
# - Admin email (ALLOWED_ORGANIZATION_ADMINS)
```

### 3. Deploy

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify all services healthy
docker-compose ps
```

### 4. Access Points

- **Frontend**: http://72.60.175.144:3000
- **API**: http://72.60.175.144:8080
- **MinIO Console**: http://72.60.175.144:9001

### 5. Create Admin User

1. Navigate to http://72.60.175.144:3000
2. Click "Sign Up"
3. Use email from `ALLOWED_ORGANIZATION_ADMINS` in .env
4. Create account (this becomes organization admin)
5. Save credentials - these will be used in Agent Factory .env

## Configuration for Agent Factory

After Atlas is deployed, update Agent Factory `.env`:

```bash
# Atlas CMMS Configuration
ATLAS_BASE_URL=http://72.60.175.144:8080
ATLAS_ADMIN_EMAIL=admin@rivet.com
ATLAS_ADMIN_PASSWORD=your_atlas_admin_password
```

## Service Management

```bash
# Stop all services
docker-compose down

# Restart specific service
docker-compose restart api

# View logs
docker-compose logs -f api

# Update to latest images
docker-compose pull
docker-compose up -d

# Backup database
docker exec rivet_atlas_db pg_dump -U atlas_admin rivet_atlas > backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### API Won't Start

```bash
# Check logs
docker-compose logs api

# Verify database connection
docker exec rivet_atlas_db psql -U atlas_admin -d rivet_atlas -c "SELECT 1"

# Reset database (CAUTION: deletes all data)
docker-compose down -v
docker-compose up -d
```

### MinIO Issues

```bash
# Access MinIO console
# http://72.60.175.144:9001
# Login: MINIO_USER / MINIO_PWD from .env

# Check bucket creation
docker-compose logs minio
```

### Port Conflicts

If ports 8080, 3000, or 9000 are already in use:

1. Edit `docker-compose.yml`
2. Change host ports (e.g., `8080:8080` → `8081:8080`)
3. Update `PUBLIC_API_URL` and `ATLAS_BASE_URL` accordingly

## Security Checklist

- [ ] Strong, unique passwords in .env
- [ ] JWT_SECRET_KEY is randomly generated
- [ ] ALLOWED_ORGANIZATION_ADMINS limits who can sign up
- [ ] Firewall rules configured (ports 3000, 8080, 9000-9001)
- [ ] Regular backups scheduled
- [ ] SSL/TLS configured (optional, via reverse proxy)

## Integration with Rivet API

Atlas Client is ready at `agent_factory/integrations/atlas/`:

```python
from agent_factory.integrations.atlas import AtlasClient

async with AtlasClient() as atlas:
    # Create work order
    wo = await atlas.create_work_order(...)

    # Search assets
    assets = await atlas.search_assets("pump")

    # Create user
    user = await atlas.create_user("user@example.com", "beta")
```

## Next Steps

After deployment:

1. ✅ Deploy Atlas CMMS to VPS
2. ✅ Create admin user
3. ✅ Update Agent Factory .env
4. Wire up Rivet API endpoints (`agent_factory/api/routers/work_orders.py`)
5. Wire up user provisioning endpoints
6. Test end-to-end flow

## Support

- **Atlas Docs**: https://github.com/Grashjs/cmms
- **API Reference**: `agent_factory/integrations/atlas/ATLAS_API_DOCUMENTATION.md`
