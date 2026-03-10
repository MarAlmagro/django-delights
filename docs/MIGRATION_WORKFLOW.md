# Django Migration Workflow

This document outlines the migration workflow and best practices for Django Delights.

## Overview

Django migrations are automatically validated in the CI/CD pipeline to prevent conflicts and ensure database schema consistency across environments.

## CI Migration Checks

The CI pipeline includes a dedicated migration validation job that runs:

1. **Missing Migrations Check** - Ensures all model changes have corresponding migrations
2. **Migration Conflicts Check** - Detects conflicting migrations
3. **Migration List Validation** - Verifies migration files are properly structured

### What Gets Checked

```bash
# Check for missing migrations
python manage.py makemigrations --check --dry-run

# Check for migration conflicts
python manage.py migrate --check

# List all migrations
python manage.py showmigrations --list
```

## Creating Migrations

### Standard Workflow

1. **Make model changes** in your Django models
2. **Create migrations locally**:
   ```bash
   python manage.py makemigrations
   ```
3. **Review the generated migration** file
4. **Test the migration**:
   ```bash
   python manage.py migrate
   ```
5. **Commit the migration file** to version control
6. **Push and create PR** - CI will validate migrations

### Best Practices

- **Always review generated migrations** before committing
- **Keep migrations small and focused** - one logical change per migration
- **Test migrations on a copy of production data** when possible
- **Never edit migrations** that have been deployed to production
- **Use data migrations** for complex data transformations

## Handling Migration Conflicts

### Detecting Conflicts

CI will fail if there are migration conflicts. Common scenarios:

1. **Multiple branches creating migrations** for the same app
2. **Parallel development** on the same models
3. **Merge conflicts** in migration files

### Resolving Conflicts

If CI detects a migration conflict:

1. **Pull the latest changes** from the target branch
2. **Delete your conflicting migration** (if not yet deployed)
3. **Recreate the migration**:
   ```bash
   python manage.py makemigrations
   ```
4. **Test the new migration**
5. **Commit and push**

### Using Migration Squashing

For apps with many migrations:

```bash
# Squash migrations 0001 through 0010
python manage.py squashmigrations delights 0001 0010
```

## Deployment Migration Strategy

### Staging Deployment

1. Migrations run automatically during staging deployment
2. Command: `railway run python manage.py migrate --noinput`
3. Verify migrations applied successfully in Railway logs

### Production Deployment

1. Migrations run automatically during production deployment
2. **Zero-downtime migrations** - ensure migrations are backwards compatible
3. Monitor application during migration

### Backwards Compatible Migrations

For zero-downtime deployments, follow these rules:

#### Adding Fields

✅ **Safe** - Add nullable fields or fields with defaults:
```python
class MenuItem(models.Model):
    new_field = models.CharField(max_length=100, null=True)
    # or
    new_field = models.CharField(max_length=100, default='')
```

❌ **Unsafe** - Adding required fields without defaults

#### Removing Fields

Use a two-step process:

**Step 1** - Make field nullable and stop using it in code:
```python
class MenuItem(models.Model):
    old_field = models.CharField(max_length=100, null=True)  # Make nullable
```

**Step 2** - After deployment, remove the field in a new migration

#### Renaming Fields

Use a three-step process:

1. Add new field
2. Copy data from old to new field
3. Remove old field (after deployment)

## Data Migrations

### Creating Data Migrations

```bash
python manage.py makemigrations --empty delights --name populate_default_data
```

### Example Data Migration

```python
from django.db import migrations

def populate_data(apps, schema_editor):
    MenuItem = apps.get_model('delights', 'MenuItem')
    MenuItem.objects.create(
        name='Default Item',
        price=10.00
    )

def reverse_populate(apps, schema_editor):
    MenuItem = apps.get_model('delights', 'MenuItem')
    MenuItem.objects.filter(name='Default Item').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('delights', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_data, reverse_populate),
    ]
```

## Rollback Procedures

### Rolling Back Migrations Locally

```bash
# Rollback to specific migration
python manage.py migrate delights 0005

# Rollback all migrations for an app
python manage.py migrate delights zero
```

### Rolling Back in Production

1. Use the **Rollback Workflow** in GitHub Actions
2. Select the environment (staging/production)
3. Enter the commit SHA before the problematic migration
4. The rollback will deploy the previous code version
5. Migrations will be at the state of that commit

### Emergency Rollback

If you need to manually rollback migrations in Railway:

```bash
# Connect to Railway
railway link [project-id]

# Run migration rollback
railway run python manage.py migrate delights [migration-number]
```

## Migration Testing

### Local Testing

1. **Test forward migration**:
   ```bash
   python manage.py migrate
   ```

2. **Test reverse migration**:
   ```bash
   python manage.py migrate delights [previous-migration]
   python manage.py migrate delights [current-migration]
   ```

3. **Test with production-like data**:
   ```bash
   # Load production data dump
   python manage.py loaddata production_dump.json
   
   # Run migrations
   python manage.py migrate
   ```

### CI Testing

Migrations are automatically tested in CI:
- Run on PostgreSQL 15 (same as production)
- Tested against empty database
- Validated for conflicts and missing migrations

## Common Issues

### Issue: "Conflicting migrations detected"

**Solution**: Merge the latest changes and recreate your migration

### Issue: "No migrations to apply"

**Solution**: Ensure migration files are committed and pushed

### Issue: "Migration fails in production"

**Solution**: 
1. Check Railway logs for specific error
2. Verify database connectivity
3. Check for data integrity issues
4. Use rollback workflow if needed

### Issue: "Migration is too slow"

**Solution**:
1. Add database indexes before large data migrations
2. Use `RunPython` with batch processing
3. Consider running migration during maintenance window

## Migration Checklist

Before merging a PR with migrations:

- [ ] Migration file is committed
- [ ] Migration tested locally (forward and reverse)
- [ ] Migration is backwards compatible (for zero-downtime)
- [ ] Data migration includes reverse operation
- [ ] CI migration checks pass
- [ ] Migration reviewed by team member
- [ ] Documentation updated if schema changes affect API

## Additional Resources

- [Django Migrations Documentation](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [Django Migration Operations](https://docs.djangoproject.com/en/stable/ref/migration-operations/)
- [Zero-Downtime Migrations](https://pankrat.github.io/2015/django-migrations-without-downtimes/)
