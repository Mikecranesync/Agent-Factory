---
id: task-63
title: 'DOCS: Production deployment guide for RIVET'
status: To Do
assignee: []
created_date: '2025-12-21 13:00'
labels:
  - docs
  - rivet
  - deployment
  - week-3-4
  - production-blocker
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create comprehensive production deployment guide for RIVET platform covering Railway, Supabase, VPS, and monitoring setup.

**Context**: Critical for Week 3-4 production launch. Ops team needs clear deployment instructions.

**Guide sections**:
1. Infrastructure overview (Railway + Supabase + VPS architecture)
2. Environment variables setup (.env.production)
3. Database migrations (Supabase schema deployment)
4. Telegram bot deployment (Railway)
5. VPS KB ingestion setup (Hostinger)
6. Monitoring setup (Langfuse + metrics)
7. Rollback procedures
8. Troubleshooting common issues
9. Health check endpoints
10. Zero-downtime deployment strategy

**Files**:
- docs/deployment/PRODUCTION_DEPLOYMENT_RIVET.md (create)
- docs/deployment/RAILWAY_SETUP.md (reference)
- docs/deployment/SUPABASE_SETUP.md (reference)

**Dependencies**:
- None (documentation task, can be done anytime)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Production deployment guide exists at docs/deployment/PRODUCTION_DEPLOYMENT_RIVET.md
- [ ] #2 Guide covers all 10 sections listed
- [ ] #3 Guide includes Railway deployment commands
- [ ] #4 Guide includes Supabase migration scripts
- [ ] #5 Guide includes VPS setup instructions
- [ ] #6 Guide includes monitoring setup (Langfuse + metrics)
- [ ] #7 Guide includes rollback procedures
- [ ] #8 Guide tested by deploying to staging environment
- [ ] #9 Guide reviewed by ops team (if applicable)
<!-- AC:END -->
