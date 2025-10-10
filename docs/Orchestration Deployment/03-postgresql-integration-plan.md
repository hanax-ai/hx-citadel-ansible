# Component 3: PostgreSQL Integration
## Knowledge Graph Storage and Job Tracking - Ansible Deployment Plan

**Component:** PostgreSQL Integration  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Database Server:** hx-sqldb-server (192.168.10.48)  
**Timeline:** Week 2, Days 1-2 (4-6 hours)  
**Priority:** ⭐ **CRITICAL - DATA LAYER**  
**Dependencies:** Component 1 (Base Setup), Component 2 (FastAPI)

---

## Overview

This plan covers PostgreSQL integration for the Shield Orchestrator, including:

- Database and user creation on hx-sqldb-server
- PostgreSQL client library installation (asyncpg, SQLAlchemy)
- Database models and schema
- Alembic migrations setup
- Connection pooling configuration
- Health check integration

---

## Database Setup (On hx-sqldb-server)

### **SQL Schema Creation**

**File:** `database/schema/001_initial_setup.sql`

```sql
-- Execute on hx-sqldb-server (192.168.10.48)
-- As postgres superuser

-- Create database
CREATE DATABASE shield_orchestrator
  OWNER orchestrator
  ENCODING 'UTF8'
  LC_COLLATE 'en_US.UTF-8'
  LC_CTYPE 'en_US.UTF-8'
  TEMPLATE template0;

COMMENT ON DATABASE shield_orchestrator IS 'Shield Orchestrator - Knowledge Graph and Job Tracking';

-- Create user (if not exists)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'orchestrator') THEN
    CREATE USER orchestrator WITH PASSWORD '{{ vault_postgres_orchestrator_password }}';
  END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE shield_orchestrator TO orchestrator;

-- Connect to database
\c shield_orchestrator

-- Create required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Text search (trigram matching)
CREATE EXTENSION IF NOT EXISTS "pgvector";       -- Vector operations (optional)

-- Create schemas
CREATE SCHEMA IF NOT EXISTS lightrag AUTHORIZATION orchestrator;
CREATE SCHEMA IF NOT EXISTS jobs AUTHORIZATION orchestrator;
CREATE SCHEMA IF NOT EXISTS events AUTHORIZATION orchestrator;

COMMENT ON SCHEMA lightrag IS 'LightRAG Knowledge Graph storage';
COMMENT ON SCHEMA jobs IS 'Job tracking and task management';
COMMENT ON SCHEMA events IS 'Event log and audit trail';

-- Grant schema privileges
GRANT ALL ON SCHEMA lightrag TO orchestrator;
GRANT ALL ON SCHEMA jobs TO orchestrator;
GRANT ALL ON SCHEMA events TO orchestrator;

-- Grant default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA lightrag GRANT ALL ON TABLES TO orchestrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA jobs GRANT ALL ON TABLES TO orchestrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA events GRANT ALL ON TABLES TO orchestrator;

-- Verify setup
SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('lightrag', 'jobs', 'events');
```

---

## Ansible Role Structure

```
roles/orchestrator_postgresql/
├── defaults/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── 01-database-setup.yml
│   ├── 02-python-client.yml
│   ├── 03-alembic-setup.yml
│   ├── 04-models.yml
│   └── 05-validation.yml
├── templates/
│   ├── database/schema/001_initial_setup.sql.j2
│   ├── database/connection.py.j2
│   ├── database/models.py.j2
│   └── database/migrations/env.py.j2
├── files/
│   └── requirements-postgresql.txt
└── handlers/
    └── main.yml
```

---

## files/requirements-postgresql.txt

```
# PostgreSQL Dependencies
# Component 3: PostgreSQL Integration

# PostgreSQL async driver
asyncpg>=0.29.0

# ORM (optional but recommended)
sqlalchemy[asyncio]>=2.0.0

# Database migrations
alembic>=1.13.0

# Utilities
psycopg2-binary>=2.9.9     # For pg_dump/restore scripts
greenlet>=3.0.0            # For SQLAlchemy async support
```

---

## templates/database/connection.py.j2

```python
"""
PostgreSQL connection management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from config.settings import settings
import logging

logger = logging.getLogger("shield-orchestrator.database")

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL debugging
    pool_size=20,  # Max connections
    max_overflow=10,  # Extra connections under load
    pool_pre_ping=True,  # Test connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """
    Dependency injection for database sessions.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Model))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database connection pool"""
    logger.info("Initializing database connection pool...")
    
    # Test connection
    async with engine.begin() as conn:
        await conn.execute("SELECT 1")
    
    logger.info("✅ Database connection pool initialized")


async def close_database():
    """Close database connections gracefully"""
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("✅ Database connections closed")


async def check_database_health() -> dict:
    """
    Check database health for /health/detailed endpoint.
    
    Returns:
        dict with status, latency, and connection info
    """
    import time
    
    try:
        start = time.time()
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        latency_ms = (time.time() - start) * 1000
        
        # Get connection pool stats
        pool = engine.pool
        
        return {
            "status": "up",
            "latency_ms": round(latency_ms, 2),
            "connections": {
                "active": pool.checkedout(),
                "idle": pool.size() - pool.checkedout(),
                "max": pool.size()
            }
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "down",
            "error": str(e),
            "latency_ms": 0
        }
```

---

## templates/database/models.py.j2

```python
"""
SQLAlchemy database models
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from database.connection import Base
from datetime import datetime
import uuid


# ============================================================
# JOBS SCHEMA - Job Tracking
# ============================================================

class JobStatus(Base):
    """Job status tracking"""
    __tablename__ = "job_status"
    __table_args__ = {"schema": "jobs"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False, index=True)  # crawl_web, ingest_doc
    status = Column(String(20), nullable=False, index=True)    # queued, processing, completed, failed
    chunks_total = Column(Integer, default=0)
    chunks_processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, default={})
    error_message = Column(Text, nullable=True)


class JobResult(Base):
    """Processed chunk results"""
    __tablename__ = "job_results"
    __table_args__ = {"schema": "jobs"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.job_status.id"), index=True)
    chunk_id = Column(String(255), index=True)
    source_uri = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    entities_extracted = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, default={})


# ============================================================
# LIGHTRAG SCHEMA - Knowledge Graph Storage
# ============================================================

class Entity(Base):
    """Extracted entities from LightRAG"""
    __tablename__ = "entities"
    __table_args__ = (
        Index("idx_entity_name", "name"),
        Index("idx_entity_type", "entity_type"),
        {"schema": "lightrag"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    entity_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    confidence = Column(Integer, default=0)  # 0-100
    source_chunks = Column(JSON, default=[])  # List of chunk IDs
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Relationship(Base):
    """Entity relationships from LightRAG"""
    __tablename__ = "relationships"
    __table_args__ = (
        Index("idx_relationship_type", "relationship_type"),
        Index("idx_source_entity", "source_entity_id"),
        Index("idx_target_entity", "target_entity_id"),
        {"schema": "lightrag"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_entity_id = Column(UUID(as_uuid=True), ForeignKey("lightrag.entities.id"))
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey("lightrag.entities.id"))
    relationship_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    confidence = Column(Integer, default=0)  # 0-100
    source_chunks = Column(JSON, default=[])  # List of chunk IDs
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class GraphMetadata(Base):
    """Knowledge Graph metadata and statistics"""
    __tablename__ = "graph_metadata"
    __table_args__ = {"schema": "lightrag"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    statistics = Column(JSON, default={})
```

---

## tasks/01-database-setup.yml

```yaml
---
# Database creation on hx-sqldb-server
- name: Check if database exists
  ansible.builtin.command: >
    psql -h 192.168.10.48 -U postgres -tAc 
    "SELECT 1 FROM pg_database WHERE datname='shield_orchestrator'"
  delegate_to: localhost
  register: db_exists
  changed_when: false
  ignore_errors: yes

- name: Deploy database setup script
  ansible.builtin.template:
    src: database/schema/001_initial_setup.sql.j2
    dest: "{{ orchestrator_app_dir }}/database/001_initial_setup.sql"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes

- name: Execute database setup script
  ansible.builtin.shell: >
    PGPASSWORD='{{ vault_postgres_superuser_password }}' 
    psql -h 192.168.10.48 -U postgres 
    -f {{ orchestrator_app_dir }}/database/001_initial_setup.sql
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  when: db_exists.stdout != "1"
  tags: [database]

- name: Verify database creation
  ansible.builtin.command: >
    PGPASSWORD='{{ vault_postgres_orchestrator_password }}'
    psql -h 192.168.10.48 -U orchestrator -d shield_orchestrator -c 
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('lightrag', 'jobs', 'events');"
  register: schema_check
  changed_when: false
  tags: [database, validation]

- name: Display database setup results
  ansible.builtin.debug:
    msg: "✅ Database schemas created: {{ schema_check.stdout_lines }}"
  tags: [database]
```

---

## tasks/02-python-client.yml

```yaml
---
# PostgreSQL Python client installation
- name: Copy PostgreSQL requirements
  ansible.builtin.copy:
    src: requirements-postgresql.txt
    dest: "{{ orchestrator_app_dir }}/requirements-postgresql.txt"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes

- name: Install PostgreSQL Python dependencies
  ansible.builtin.pip:
    requirements: "{{ orchestrator_app_dir }}/requirements-postgresql.txt"
    virtualenv: "{{ orchestrator_venv_dir }}"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  notify: restart orchestrator
  tags: [dependencies]

- name: Verify asyncpg installation
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import asyncpg; print(asyncpg.__version__)'
  register: asyncpg_version
  changed_when: false
  tags: [dependencies, validation]

- name: Verify SQLAlchemy installation
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import sqlalchemy; print(sqlalchemy.__version__)'
  register: sqlalchemy_version
  changed_when: false
  tags: [dependencies, validation]

- name: Display client library versions
  ansible.builtin.debug:
    msg:
      - "asyncpg: {{ asyncpg_version.stdout }}"
      - "SQLAlchemy: {{ sqlalchemy_version.stdout }}"
  tags: [dependencies]
```

---

## tasks/03-alembic-setup.yml

```yaml
---
# Alembic migrations setup
- name: Create Alembic configuration directory
  ansible.builtin.file:
    path: "{{ orchestrator_app_dir }}/database/migrations"
    state: directory
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0755"
  become: yes

- name: Initialize Alembic (if not exists)
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/alembic init database/migrations
  args:
    chdir: "{{ orchestrator_app_dir }}"
    creates: "{{ orchestrator_app_dir }}/alembic.ini"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  tags: [migrations]

- name: Deploy Alembic environment configuration
  ansible.builtin.template:
    src: database/migrations/env.py.j2
    dest: "{{ orchestrator_app_dir }}/database/migrations/env.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  tags: [migrations]

- name: Generate initial migration
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/alembic revision --autogenerate -m "Initial schema"
  args:
    chdir: "{{ orchestrator_app_dir }}"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  register: migration_created
  changed_when: "'Generating' in migration_created.stdout"
  tags: [migrations]

- name: Apply database migrations
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/alembic upgrade head
  args:
    chdir: "{{ orchestrator_app_dir }}"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  register: migration_applied
  changed_when: "'Running upgrade' in migration_applied.stdout"
  tags: [migrations]

- name: Display migration results
  ansible.builtin.debug:
    msg: "{{ migration_applied.stdout_lines }}"
  tags: [migrations]
```

---

## tasks/04-models.yml

```yaml
---
# Deploy database models
- name: Deploy database connection module
  ansible.builtin.template:
    src: database/connection.py.j2
    dest: "{{ orchestrator_app_dir }}/database/connection.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [models]

- name: Deploy database models
  ansible.builtin.template:
    src: database/models.py.j2
    dest: "{{ orchestrator_app_dir }}/database/models.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [models]

- name: Test model imports
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'from database.models import JobStatus, Entity, Relationship; print("Models imported successfully")'
  args:
    chdir: "{{ orchestrator_app_dir }}"
  register: model_import_test
  changed_when: false
  tags: [models, validation]
```

---

## tasks/05-validation.yml

```yaml
---
# PostgreSQL integration validation
- name: Test database connection from orchestrator
  ansible.builtin.command: >
    PGPASSWORD='{{ vault_postgres_orchestrator_password }}'
    psql -h 192.168.10.48 -U orchestrator -d shield_orchestrator -c "SELECT current_database();"
  register: db_connection_test
  changed_when: false
  tags: [validation]

- name: Verify database schemas
  ansible.builtin.command: >
    PGPASSWORD='{{ vault_postgres_orchestrator_password }}'
    psql -h 192.168.10.48 -U orchestrator -d shield_orchestrator -tAc 
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('lightrag', 'jobs', 'events');"
  register: schema_verification
  failed_when: "'lightrag' not in schema_verification.stdout or 'jobs' not in schema_verification.stdout"
  changed_when: false
  tags: [validation]

- name: Check Alembic migration status
  ansible.builtin.command: "{{ orchestrator_venv_dir }}/bin/alembic current"
  args:
    chdir: "{{ orchestrator_app_dir }}"
  register: alembic_status
  changed_when: false
  tags: [validation]

- name: Verify tables created
  ansible.builtin.command: >
    PGPASSWORD='{{ vault_postgres_orchestrator_password }}'
    psql -h 192.168.10.48 -U orchestrator -d shield_orchestrator -c "\dt lightrag.*"
  register: tables_check
  changed_when: false
  tags: [validation]

- name: Display PostgreSQL validation summary
  ansible.builtin.debug:
    msg:
      - "✅ Database: {{ db_connection_test.stdout_lines[2] }}"
      - "✅ Schemas: {{ schema_verification.stdout_lines | length }} schemas"
      - "✅ Alembic: {{ alembic_status.stdout }}"
      - "✅ PostgreSQL integration complete!"
  tags: [validation]
```

---

## Success Criteria

```yaml
✅ Database (on hx-sqldb-server):
   • Database created: shield_orchestrator
   • User created: orchestrator
   • Extensions: uuid-ossp, pg_trgm, pgvector
   • Schemas: lightrag, jobs, events

✅ Python Dependencies:
   • asyncpg >=0.29.0 installed
   • SQLAlchemy >=2.0.0 installed
   • Alembic >=1.13.0 installed

✅ Models:
   • database/connection.py deployed
   • database/models.py deployed
   • Connection pooling configured (20 connections)
   • Models importable

✅ Migrations:
   • Alembic initialized
   • Initial migration generated
   • Migration applied (alembic upgrade head)
   • Tables created in all schemas

✅ Validation:
   • Connection from orchestrator successful
   • All schemas visible
   • All tables created
   • Models can be imported
```

---

## Timeline

**Estimated Time:** 4-6 hours

```yaml
Task Breakdown:
  • Database setup (DBA): 1 hour
  • Python client install: 1 hour
  • Alembic setup: 1.5 hours
  • Model deployment: 1 hour
  • Validation: 30 minutes
  • Buffer: 1 hour

Total: 5 hours
```

---

## Next Component

**After PostgreSQL integration, proceed to:**

→ **Component 4: Redis Streams Integration** (`04-redis-streams-integration-plan.md`)

---

**PostgreSQL Integration Plan Complete!** ✅
**Ready for Ansible deployment!** 🚀

