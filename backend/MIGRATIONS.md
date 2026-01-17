# Database Migrations with Alembic

This guide explains how to manage database schema evolution using Alembic.

## Quick Start

```bash
# Navigate to backend directory
cd backend

# Apply all pending migrations
alembic upgrade head

# Check current revision
alembic current

# View migration history
alembic history
```

## Common Commands

### Applying Migrations

```bash
# Apply all migrations
alembic upgrade head

# Apply next migration only
alembic upgrade +1

# Apply specific revision
alembic upgrade 0001_initial
```

### Rolling Back

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 0001_initial

# Rollback all (WARNING: drops all tables)
alembic downgrade base
```

### Creating New Migrations

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add user profile fields"

# Create empty migration
alembic revision -m "Custom migration"
```

### Viewing Status

```bash
# Show current database revision
alembic current

# Show full revision history  
alembic history --verbose

# Show pending migrations
alembic history --indicate-current
```

## Workflow for Schema Changes

1. **Modify models** in `app/models/`
2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```
3. **Review the generated file** in `alembic/versions/`
4. **Apply migration**:
   ```bash
   alembic upgrade head
   ```

## Best Practices

### ✅ Do
- Always review auto-generated migrations before applying
- Use descriptive migration messages
- Test migrations on development DB first
- Commit migration files to version control

### ❌ Don't
- Manually edit applied migrations
- Delete migration files that have been applied
- Use `Base.metadata.create_all()` in production

## File Structure

```
backend/
├── alembic.ini           # Alembic configuration
├── alembic/
│   ├── env.py            # Environment configuration
│   ├── script.py.mako    # Migration template
│   └── versions/         # Migration scripts
│       ├── __init__.py
│       └── 20260117_0001_initial.py
```

## Environment Configuration

Database URL is read from application settings (`app/config.py`), which loads from environment variables or `.env` file:

```env
DATABASE_URL=postgresql://homegpu:password@localhost:5432/homegpu
```

## Troubleshooting

### "Target database is not up to date"
```bash
alembic stamp head  # Mark current DB as up to date
```

### "Can't locate revision"
```bash
alembic history     # Check revision IDs
alembic upgrade head --sql  # Generate SQL without applying
```

### Multiple heads (branches)
```bash
alembic heads                  # List heads
alembic merge heads -m "merge" # Merge branches
```
