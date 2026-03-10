# CI/CD & DevOps Improvement Plan

**Priority:** Medium  
**Estimated Effort:** 1-2 sprints  
**Related Review:** Review-Summary.md

---

## Overview

This plan addresses CI/CD and DevOps gaps identified during the comprehensive project review, focusing on completing deployment configuration and adding production-readiness features.

---

## 1. High: Complete Railway Deployment Configuration

**Current Issue:** Deploy steps are placeholder `echo` statements

### Update CI Workflow

```yaml
# .github/workflows/ci.yml - Replace deploy-staging job

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
    environment: staging
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway Staging
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN_STAGING }}
        run: |
          railway link ${{ secrets.RAILWAY_PROJECT_ID_STAGING }}
          railway up --service web

      - name: Run Migrations
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN_STAGING }}
        run: |
          railway run python manage.py migrate --noinput

      - name: Verify Deployment
        run: |
          sleep 30
          curl --fail ${{ secrets.STAGING_URL }}/api/health/ || exit 1

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway Production
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN_PRODUCTION }}
        run: |
          railway link ${{ secrets.RAILWAY_PROJECT_ID_PRODUCTION }}
          railway up --service web

      - name: Run Migrations
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN_PRODUCTION }}
        run: |
          railway run python manage.py migrate --noinput

      - name: Verify Deployment
        run: |
          sleep 30
          curl --fail ${{ secrets.PRODUCTION_URL }}/api/health/ || exit 1

      - name: Notify on Success
        if: success()
        run: echo "Deployment successful!"
        # Add Slack/Discord notification here
```

### Required Secrets

| Secret | Description |
|--------|-------------|
| `RAILWAY_TOKEN_STAGING` | Railway API token for staging |
| `RAILWAY_TOKEN_PRODUCTION` | Railway API token for production |
| `RAILWAY_PROJECT_ID_STAGING` | Railway project ID for staging |
| `RAILWAY_PROJECT_ID_PRODUCTION` | Railway project ID for production |
| `STAGING_URL` | Staging environment URL |
| `PRODUCTION_URL` | Production environment URL |

### Tasks
- [ ] Create Railway staging project
- [ ] Create Railway production project
- [ ] Add secrets to GitHub repository
- [ ] Update CI workflow with actual deployment
- [ ] Test staging deployment
- [ ] Test production deployment
- [ ] Add deployment notifications

---

## 2. High: Add Migration Validation in CI

**Current Issue:** Migrations run but not validated for conflicts

### Add Migration Check Job

```yaml
# .github/workflows/ci.yml - Add after lint job

  migrations:
    name: Check Migrations
    runs-on: ubuntu-latest
    needs: lint
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Check for missing migrations
        run: |
          python manage.py makemigrations --check --dry-run
        env:
          SECRET_KEY: ${{ env.SECRET_KEY }}

      - name: Check migration conflicts
        run: |
          python manage.py migrate --check
        env:
          SECRET_KEY: ${{ env.SECRET_KEY }}

      - name: Validate migration files
        run: |
          python manage.py showmigrations --list
```

### Tasks
- [ ] Add migrations job to CI
- [ ] Add `--check` flag to makemigrations
- [ ] Add migration conflict detection
- [ ] Document migration workflow

---

## 3. High: Push Docker Images to Registry

**Current Issue:** Images built but not pushed to registry

### Add Container Registry Push

```yaml
# .github/workflows/ci.yml - Update build job

  build:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    needs: [test, security]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix=
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

### Tasks
- [ ] Enable GitHub Container Registry for repository
- [ ] Update build job to push images
- [ ] Add image tagging strategy
- [ ] Upload security scan results to GitHub Security
- [ ] Document image pull instructions

---

## 4. Medium: Add Rollback Strategy

**Current Issue:** No deployment rollback configuration

### Rollback Workflow

```yaml
# .github/workflows/rollback.yml
name: Rollback Deployment

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to rollback'
        required: true
        type: choice
        options:
          - staging
          - production
      version:
        description: 'Version/SHA to rollback to'
        required: true
        type: string

jobs:
  rollback:
    name: Rollback ${{ inputs.environment }}
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Rollback deployment
        env:
          RAILWAY_TOKEN: ${{ inputs.environment == 'production' && secrets.RAILWAY_TOKEN_PRODUCTION || secrets.RAILWAY_TOKEN_STAGING }}
        run: |
          railway link ${{ inputs.environment == 'production' && secrets.RAILWAY_PROJECT_ID_PRODUCTION || secrets.RAILWAY_PROJECT_ID_STAGING }}
          railway up --service web

      - name: Verify rollback
        run: |
          sleep 30
          curl --fail ${{ inputs.environment == 'production' && secrets.PRODUCTION_URL || secrets.STAGING_URL }}/api/health/

      - name: Notify rollback
        run: echo "Rolled back ${{ inputs.environment }} to ${{ inputs.version }}"
```

### Tasks
- [ ] Create rollback workflow
- [ ] Document rollback procedure
- [ ] Test rollback process
- [ ] Add rollback notifications

---

## 5. Medium: Add GitHub Secret Scanning

**Current Issue:** No automated secret scanning

### Enable GitHub Security Features

1. Go to Repository Settings > Security > Code security and analysis
2. Enable:
   - Dependency graph ✓
   - Dependabot alerts ✓
   - Dependabot security updates ✓
   - Secret scanning ✓
   - Push protection ✓

### Add Dependabot Configuration

```yaml
# .github/dependabot.yml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "deps"
    groups:
      django:
        patterns:
          - "django*"
          - "drf*"
      testing:
        patterns:
          - "pytest*"
          - "factory*"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "github-actions"
    commit-message:
      prefix: "ci"

  # Docker
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"
```

### Tasks
- [ ] Enable GitHub security features
- [ ] Create dependabot.yml
- [ ] Review existing security alerts
- [ ] Set up alert notifications
- [ ] Document security update process

---

## 6. Medium: Add Staging Environment

**Current Issue:** Only dev and prod environments mentioned

### Environment Configuration

```python
# django_delights/settings/staging.py
"""
Django staging settings.
Similar to production but with additional debugging.
"""

from .prod import *  # noqa

# Allow more verbose logging in staging
LOGGING['root']['level'] = 'DEBUG'

# Enable Django Debug Toolbar in staging (optional)
if os.getenv('ENABLE_DEBUG_TOOLBAR', 'False').lower() == 'true':
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1']

# Staging-specific settings
STAGING = True
```

### Update railway.toml

```toml
# railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "gunicorn django_delights.wsgi:application --bind 0.0.0.0:$PORT"
healthcheckPath = "/api/health/"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[environments.staging]
DJANGO_ENV = "staging"
DJANGO_SETTINGS_MODULE = "django_delights.settings.staging"

[environments.production]
DJANGO_ENV = "prod"
DJANGO_SETTINGS_MODULE = "django_delights.settings.prod"
```

### Tasks
- [ ] Create staging.py settings file
- [ ] Update railway.toml with environments
- [ ] Create staging Railway project
- [ ] Configure staging database
- [ ] Document staging environment

---

## 7. Low: Improve CI Caching

**Current Issue:** Could improve CI speed with better caching

### Optimized CI Configuration

```yaml
# .github/workflows/ci.yml - Improved caching

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: |
            ~/.cache/pip
            ~/.local/lib/python${{ env.PYTHON_VERSION }}/site-packages
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Cache pre-commit
        uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: ${{ runner.os }}-pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt -r requirements-dev.txt

      # ... rest of test job
```

### Tasks
- [ ] Add pip caching to all jobs
- [ ] Add pre-commit caching
- [ ] Add Docker layer caching
- [ ] Measure CI time improvements
- [ ] Document caching strategy

---

## 8. Low: Add Deployment Notifications

**Current Issue:** No notifications on deployment success/failure

### Slack Notification

```yaml
# Add to deploy jobs
      - name: Notify Slack on Success
        if: success()
        uses: slackapi/slack-github-action@v1.25.0
        with:
          payload: |
            {
              "text": "✅ Deployment to ${{ inputs.environment || 'production' }} succeeded",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Successful*\n• Environment: ${{ inputs.environment || 'production' }}\n• Commit: ${{ github.sha }}\n• Actor: ${{ github.actor }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

      - name: Notify Slack on Failure
        if: failure()
        uses: slackapi/slack-github-action@v1.25.0
        with:
          payload: |
            {
              "text": "❌ Deployment to ${{ inputs.environment || 'production' }} failed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Failed*\n• Environment: ${{ inputs.environment || 'production' }}\n• Commit: ${{ github.sha }}\n• Actor: ${{ github.actor }}\n• <${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Logs>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Tasks
- [ ] Set up Slack webhook
- [ ] Add success notifications
- [ ] Add failure notifications
- [ ] Add deployment summary
- [ ] Document notification setup

---

## 9. Low: Add Pre-deployment Checks

**Current Issue:** No pre-deployment validation

### Pre-deployment Job

```yaml
# .github/workflows/ci.yml - Add before deploy

  pre-deploy-checks:
    name: Pre-deployment Checks
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Check for breaking changes
        run: |
          # Check if migrations are backwards compatible
          # Check if API changes are backwards compatible
          echo "Running pre-deployment checks..."

      - name: Verify environment variables
        run: |
          # List required env vars
          REQUIRED_VARS="SECRET_KEY DATABASE_URL ALLOWED_HOSTS"
          echo "Required environment variables: $REQUIRED_VARS"

      - name: Check database connectivity
        run: |
          echo "Database connectivity check would run here"
          # In real scenario, connect to staging DB

      - name: Smoke test
        run: |
          echo "Smoke tests would run here"
          # Run minimal tests against staging
```

### Tasks
- [ ] Create pre-deployment checks job
- [ ] Add migration compatibility check
- [ ] Add API compatibility check
- [ ] Add environment variable validation
- [ ] Document pre-deployment requirements

---

## Summary of Required Secrets

| Secret | Purpose |
|--------|---------|
| `RAILWAY_TOKEN_STAGING` | Railway API token for staging |
| `RAILWAY_TOKEN_PRODUCTION` | Railway API token for production |
| `RAILWAY_PROJECT_ID_STAGING` | Railway project ID for staging |
| `RAILWAY_PROJECT_ID_PRODUCTION` | Railway project ID for production |
| `STAGING_URL` | Staging environment URL |
| `PRODUCTION_URL` | Production environment URL |
| `SLACK_WEBHOOK_URL` | Slack notifications |

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | Complete deployment, migrations check | 1 sprint |
| Phase 2 | Container registry, rollback | 0.5 sprint |
| Phase 3 | Notifications, caching | 0.5 sprint |

---

## Success Metrics

- [ ] Automated deployments to staging on develop branch
- [ ] Automated deployments to production on main branch
- [ ] Docker images pushed to GHCR
- [ ] Rollback workflow tested and documented
- [ ] Dependabot enabled and configured
- [ ] CI time < 10 minutes
- [ ] Deployment notifications working
- [ ] Zero manual deployment steps
