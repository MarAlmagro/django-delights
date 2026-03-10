# CI/CD Setup Guide

This guide covers the setup and configuration of the CI/CD pipeline for Django Delights.

## Overview

The CI/CD pipeline includes:
- **Continuous Integration**: Automated testing, linting, security scanning, and Docker builds
- **Continuous Deployment**: Automated deployments to staging and production environments
- **Rollback Capability**: Manual workflow to rollback to previous versions
- **Dependency Management**: Automated dependency updates via Dependabot

## GitHub Actions Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and pull request to `main` and `develop` branches.

**Jobs:**
1. **Lint** - Code formatting and style checks (Black, isort, flake8)
2. **Migrations** - Validates Django migrations
3. **Test** - Runs test suite with coverage reporting
4. **Security** - Security scanning (Bandit, Safety)
5. **Build** - Builds and pushes Docker image to GitHub Container Registry
6. **Pre-deploy Checks** - Validates deployment readiness
7. **Deploy Staging** - Deploys to staging on `develop` branch
8. **Deploy Production** - Deploys to production on `main` branch

### 2. Rollback Workflow (`.github/workflows/rollback.yml`)

Manually triggered workflow to rollback deployments.

**Usage:**
1. Go to Actions → Rollback Deployment
2. Click "Run workflow"
3. Select environment (staging/production)
4. Enter the commit SHA or tag to rollback to
5. Click "Run workflow"

## Required GitHub Secrets

Configure these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

| Secret | Description | Example |
|--------|-------------|---------|
| `RAILWAY_TOKEN_STAGING` | Railway API token for staging | `railway_xxx...` |
| `RAILWAY_TOKEN_PRODUCTION` | Railway API token for production | `railway_xxx...` |
| `RAILWAY_PROJECT_ID_STAGING` | Railway project ID for staging | `abc123...` |
| `RAILWAY_PROJECT_ID_PRODUCTION` | Railway project ID for production | `def456...` |
| `STAGING_URL` | Staging environment URL | `https://staging.example.com` |
| `PRODUCTION_URL` | Production environment URL | `https://example.com` |

### How to Get Railway Tokens

1. Go to [Railway Dashboard](https://railway.app/account/tokens)
2. Click "Create Token"
3. Give it a descriptive name (e.g., "GitHub Actions Staging")
4. Copy the token and add it to GitHub Secrets

### How to Get Railway Project IDs

1. Go to your Railway project
2. Click on Settings
3. Copy the Project ID from the URL or settings page

## Railway Environment Setup

### 1. Create Railway Projects

Create two Railway projects:
- `django-delights-staging`
- `django-delights-production`

### 2. Configure Environment Variables

For each Railway project, set these environment variables:

**Required:**
- `SECRET_KEY` - Django secret key (generate with `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`)
- `DATABASE_URL` - PostgreSQL connection string (auto-configured by Railway)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `DJANGO_SETTINGS_MODULE` - `django_delights.settings.staging` or `django_delights.settings.prod`
- `DJANGO_ENV` - `staging` or `prod`

**Optional:**
- `SENTRY_DSN` - Sentry error tracking DSN
- `REDIS_URL` - Redis connection string for caching
- `EMAIL_HOST` - SMTP server host
- `EMAIL_HOST_USER` - SMTP username
- `EMAIL_HOST_PASSWORD` - SMTP password
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins
- `CSRF_TRUSTED_ORIGINS` - Comma-separated list of trusted CSRF origins

### 3. Add PostgreSQL Database

1. In Railway project, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically set `DATABASE_URL`

## GitHub Container Registry Setup

### Enable Package Permissions

1. Go to repository Settings → Actions → General
2. Scroll to "Workflow permissions"
3. Select "Read and write permissions"
4. Check "Allow GitHub Actions to create and approve pull requests"
5. Click "Save"

### Pull Docker Images

Images are automatically pushed to `ghcr.io/[owner]/[repo]`:

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull latest image
docker pull ghcr.io/[owner]/django-delights:latest

# Pull specific commit
docker pull ghcr.io/[owner]/django-delights:[commit-sha]
```

## Dependabot Configuration

Dependabot is configured to automatically create PRs for:
- Python dependencies (weekly on Mondays)
- GitHub Actions (weekly)
- Docker base images (weekly)

### Enable GitHub Security Features

1. Go to Settings → Security → Code security and analysis
2. Enable:
   - ✅ Dependency graph
   - ✅ Dependabot alerts
   - ✅ Dependabot security updates
   - ✅ Secret scanning
   - ✅ Push protection

## Deployment Flow

### Staging Deployment

1. Create feature branch from `develop`
2. Make changes and commit
3. Push to remote and create PR to `develop`
4. CI runs automatically (lint, test, security, build)
5. Merge PR to `develop`
6. Automatic deployment to staging environment
7. Verify deployment at staging URL

### Production Deployment

1. Create PR from `develop` to `main`
2. Review changes and get approvals
3. Merge PR to `main`
4. Automatic deployment to production environment
5. Verify deployment at production URL

### Rollback Procedure

If a deployment causes issues:

1. Go to Actions → Rollback Deployment
2. Select environment (staging/production)
3. Enter the last known good commit SHA
4. Run workflow
5. Verify rollback was successful

## Monitoring and Notifications

### Current Setup

- ✅ Deployment success/failure messages in workflow logs
- ✅ GitHub Actions notifications
- ✅ Security scan results uploaded to GitHub Security tab

### Future Enhancements

To add Slack notifications, configure:

1. Create Slack webhook URL
2. Add `SLACK_WEBHOOK_URL` to GitHub Secrets
3. Uncomment Slack notification steps in workflows

## Troubleshooting

### Deployment Fails with "Railway CLI not found"

The workflow installs Railway CLI automatically. If it fails:
- Check Railway CLI is available: `npm install -g @railway/cli`
- Verify npm is installed in the runner

### Migration Errors

If migrations fail during deployment:
1. Check migration files are committed
2. Verify database connectivity
3. Run migrations manually: `railway run python manage.py migrate`

### Docker Build Fails

Common issues:
- Missing dependencies in `requirements.txt`
- Dockerfile syntax errors
- Base image not available

Check the build logs in GitHub Actions for specific errors.

### Health Check Fails

If deployment verification fails:
1. Verify health endpoint exists: `/api/health/`
2. Check application logs in Railway
3. Ensure application starts successfully
4. Verify environment variables are set

## Performance Optimization

### CI Caching

The workflow uses caching for:
- Python pip packages
- Pre-commit hooks
- Docker layers (GitHub Actions cache)

Expected CI time: **< 10 minutes**

### Improving Build Times

1. Keep dependencies minimal
2. Use `.dockerignore` to exclude unnecessary files
3. Leverage Docker layer caching
4. Run tests in parallel when possible

## Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **Rotate tokens regularly** - Update Railway tokens every 90 days
3. **Review Dependabot PRs** - Don't auto-merge without testing
4. **Monitor security alerts** - Check GitHub Security tab weekly
5. **Use branch protection** - Require PR reviews before merging

## Maintenance

### Weekly Tasks

- Review and merge Dependabot PRs
- Check security alerts
- Monitor deployment success rates

### Monthly Tasks

- Review and update CI/CD workflows
- Audit Railway environment variables
- Check Docker image sizes and optimize

### Quarterly Tasks

- Rotate Railway API tokens
- Review and update security policies
- Performance audit of CI/CD pipeline

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
