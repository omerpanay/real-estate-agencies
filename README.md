# Multi-Tenant SaaS CRM Platform

A modular, multi-tenant CRM platform built with FastAPI and PostgreSQL, designed for vertical industries (Real Estate, Clinics, etc.).

## 🏗️ Product Architecture

### Shared Core + Industry Modules Design

```
┌─────────────────────────────────────────────────────────────┐
│                    SHARED CORE PLATFORM                     │
├─────────────────────────────────────────────────────────────┤
│  Authentication  │  Contacts  │  Deals  │  Multi-tenancy   │
└────────┬────────────────┬────────────────┬─────────────────┘
         │                │                │
    ┌────▼────┐     ┌────▼────┐     ┌─────▼─────┐
    │  Real   │     │  Clinic │     │  Custom   │
    │ Estate  │     │ Module  │     │  Module   │
    └─────────┘     └─────────┘     └───────────┘
```

**Benefits:**
- **Code Reuse**: Core CRM logic (contacts, deals, users) shared across all modules
- **Rapid Deployment**: New industry verticals inherit authentication, multi-tenancy, and CRUD operations
- **Maintainability**: Bug fixes and improvements to core benefit all modules
- **Scalability**: Each module can be developed, tested, and deployed independently

---

## 🔒 Multi-Tenancy: Row-Level Security

### How It Works

Every data model inherits from `TenantMixin`, which automatically adds a `tenant_id` UUID column:

```python
class TenantMixin:
    @declared_attr
    def tenant_id(cls):
        return Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)
```

### Automatic Tenant Isolation

| Operation | Implementation |
|-----------|----------------|
| **CREATE** | `tenant_id` auto-assigned from `current_user.tenant_id` |
| **READ** | Query includes `.where(Model.tenant_id == current_user.tenant_id)` |
| **UPDATE** | Validates record belongs to tenant before modification |
| **DELETE** | Validates ownership before deletion |

**Result**: Tenant B receives `404 Not Found` when attempting to access Tenant A's data—complete isolation at the application layer.

---

## 🛠️ Tech Stack

| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **FastAPI** | Web Framework | Native async/await, automatic OpenAPI docs, type safety with Pydantic |
| **PostgreSQL** | Database | Robust ACID compliance, excellent for multi-tenant data, UUID support |
| **SQLAlchemy 2.0** | ORM | Async support, powerful query building, mature ecosystem |
| **asyncpg** | DB Driver | Fastest PostgreSQL driver for Python (5-10x faster than psycopg2) |
| **JWT (python-jose)** | Authentication | Stateless auth, contains `tenant_id` for zero-lookup tenant context |
| **Passlib + bcrypt** | Password Security | Industry-standard password hashing |
| **Pydantic v2** | Validation | Fast validation, automatic serialisation, schema generation |

### Why Async?
- **Speed**: Handle 10,000+ concurrent connections on modest hardware
- **Efficiency**: Non-blocking I/O for database and external API calls
- **Modern**: Aligns with current Python best practices

---



###  Foundation & Authentication
- [x] Project structure with `/app/api`, `/core`, `/models`, `/schemas`
- [x] PostgreSQL async database configuration
- [x] TenantMixin for multi-tenant row-level security
- [x] User and Tenant models
- [x] JWT authentication with login endpoint
- [x] `get_current_user` dependency injection

###  Core CRM Modules
- [x] Contact model with full CRUD endpoints
- [x] Deal model with stage pipeline (NEW → NEGOTIATION → CLOSED)
- [x] Tenant-scoped queries on all operations
- [x] Search and filtering capabilities
- [x] Input validation with Pydantic schemas

### Industry Specifics & Automation
- [x] Real Estate module: Property and Viewing models
- [x] Property listing with type/status/price filters
- [x] Viewing scheduling linked to Contacts
- [ ] Webhook integrations for external services
- [ ] Notification system (email/SMS templates)

### Security Hardening, QA & Deployment
- [x] Comprehensive test suite with pytest
- [x] Tenant isolation verification tests
- [x] Docker Compose for local development
- [ ] Rate limiting and request throttling
- [ ] Production deployment configuration
- [ ] Monitoring and logging setup

---

## 💰 Cost Model

### MVP Hosting (Estimated £8-16/month)

| Service | Option | Cost |
|---------|--------|------|
| **VPS** | Hetzner CX11 / DigitalOcean Basic | £3-5/month |
| **Managed PostgreSQL** | Supabase Free / Railway | £0-8/month |
| **Domain + SSL** | Cloudflare (free SSL) | £1/month |
| **CI/CD** | GitHub Actions | Free |

### Cost Optimisation Strategy

1. **Modularity**: Only deploy modules customers actually use
2. **Open Source Stack**: Zero licensing fees (FastAPI, PostgreSQL, all libraries)
3. **Containerisation**: Easy scaling with Kubernetes when needed
4. **Connection Pooling**: Efficient database connections with asyncpg

### Scaling Path

| Stage | Users | Infrastructure | Monthly Cost |
|-------|-------|----------------|--------------|
| MVP | 1-100 | Single VPS + Managed DB | £10-20 |
| Growth | 100-1000 | Load balancer + 2 VPS | £50-100 |
| Scale | 1000+ | Kubernetes cluster | £200+ |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (or Docker)

### Local Development

```bash
# Clone and enter directory
cd Internship-Interview

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL with Docker
docker-compose up -d

# Run the application
uvicorn app.main:app --reload
```

### Access Points
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx aiosqlite

# Run tests
pytest tests/ -v
```

---

## 📁 Project Structure

```
app/
├── api/
│   ├── deps.py              # Dependency injection (auth)
│   └── v1/endpoints/
│       ├── auth.py          # Login endpoint
│       ├── contacts.py      # Contact CRUD
│       ├── deals.py         # Deal CRUD
│       └── properties.py    # Property CRUD + Viewings
├── core/
│   ├── config.py            # Environment settings
│   ├── database.py          # Async SQLAlchemy
│   └── security.py          # JWT + password hashing
├── models/
│   ├── base.py              # TenantMixin
│   ├── tenant.py            # Tenant, User
│   ├── crm.py               # Contact, Deal
│   └── real_estate.py       # Property, Viewing
├── schemas/                  # Pydantic models
└── main.py                  # FastAPI application
tests/
├── conftest.py              # Test fixtures
└── test_main.py             # Integration tests
```

---

## 🔐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Authenticate and receive JWT |
| `/api/v1/contacts/` | GET, POST | List/Create contacts |
| `/api/v1/contacts/{id}` | GET, PATCH, DELETE | Contact operations |
| `/api/v1/deals/` | GET, POST | List/Create deals |
| `/api/v1/deals/{id}` | GET, PATCH, DELETE | Deal operations |
| `/api/v1/properties/` | GET, POST | List/Create properties |
| `/api/v1/properties/{id}` | GET, PATCH, DELETE | Property operations |
| `/api/v1/properties/{id}/viewings` | GET, POST | Viewing scheduling |

---

## 📜 Licence

MIT License - Free for commercial and private use.
