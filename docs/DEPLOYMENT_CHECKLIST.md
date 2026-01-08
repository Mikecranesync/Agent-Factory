# RIVET Pro - Deployment Checklist

**Purpose:** Step-by-step deployment guide from test to production
**Created:** January 8, 2026
**Current Phase:** 3 (Testing & Configuration)

---

## How to Use This Checklist

1. **Check each box** as you complete each step
2. **Do not skip steps** - order matters
3. **Test thoroughly** in test mode before production
4. **Document issues** as you find them
5. **Get approval** before production deployment

---

## Phase 0: Prerequisites ✅ COMPLETE

- [x] RIVET Pro Sprint worktree created
- [x] Repository cloned to local machine
- [x] Git branch: `rivet-test-sprint`
- [x] Claude CLI configured

---

## Phase 1: Database Schema ✅ COMPLETE

- [x] Neon PostgreSQL database accessible
- [x] Connection string obtained and saved to .env
- [x] Schema file reviewed (sql/rivet_pro_schema.sql)
- [x] Deployment script created (scripts/deploy_schema.py)
- [x] Schema deployed successfully
- [x] All 4 tables created (rivet_users, rivet_usage_log, rivet_print_sessions, rivet_stripe_events)
- [x] All 8 functions created and tested
- [x] Deployment logged in docs/DEPLOYMENT_LOG.md
- [x] Changes committed (commit: cdcd4552)

---

## Phase 2: n8n Workflows ✅ COMPLETE

- [x] 5 workflow JSON files created:
  - [x] rivet_usage_tracker.json (13 nodes)
  - [x] rivet_stripe_checkout.json (9 nodes)
  - [x] rivet_stripe_webhook.json (16 nodes)
  - [x] rivet_chat_with_print.json (17 nodes)
  - [x] rivet_commands.json (11 nodes)
- [x] All workflows use NATIVE n8n nodes only
- [x] No hardcoded API keys in workflows
- [x] Credentials referenced by ID or placeholder
- [x] README updated with deployment guide
- [x] Changes committed (commit: 45bd14fd)

---

## Phase 3: Configuration & Testing ⏳ IN PROGRESS

### Part 3A: Stripe Dashboard Setup

- [ ] Stripe account created/accessed
- [ ] Test mode enabled (toggle in top right)
- [ ] **Product created:**
  - [ ] Name: "RIVET Pro"
  - [ ] Description: "Unlimited equipment lookups + Chat with Print-it"
- [ ] **Price created:**
  - [ ] Amount: $29.00 USD
  - [ ] Billing: Monthly
  - [ ] Price ID copied: `price_________________`
- [ ] **Webhook endpoint configured:**
  - [ ] URL: `http://72.60.175.144:5678/webhook/stripe-webhook-rivet`
  - [ ] Events selected:
    - [ ] checkout.session.completed
    - [ ] customer.subscription.deleted
    - [ ] invoice.payment_failed
  - [ ] Webhook secret copied (optional): `whsec_________________`

**Reference:** See `docs/STRIPE_SETUP_GUIDE.md` Part 1

---

### Part 3B: n8n Credentials Setup

- [ ] **Neon RIVET credential created:**
  - [ ] Type: Postgres
  - [ ] Name: `Neon RIVET`
  - [ ] Host: `ep-purple-hall-ahimeyn0-pooler.c-3.us-east-1.aws.neon.tech`
  - [ ] Database: `neondb`
  - [ ] User: `neondb_owner`
  - [ ] Password: `npg_c3UNa4KOlCeL`
  - [ ] SSL: Required ✅
  - [ ] Connection tested successfully

- [ ] **Stripe RIVET credential created:**
  - [ ] Type: Stripe API
  - [ ] Name: `Stripe RIVET`
  - [ ] Secret Key: `sk_test_________________` (test mode)
  - [ ] Saved successfully

- [ ] **Telegram Bot credential exists:**
  - [ ] Credential ID: `if4EOJbvMirfWqCC`
  - [ ] Name: `Telegram Bot`
  - [ ] Already configured ✅

**Reference:** See `docs/STRIPE_SETUP_GUIDE.md` Part 2.1-2.2

---

### Part 3C: Workflow Import & Configuration

- [ ] **Import workflows to n8n:** http://72.60.175.144:5678
  - [ ] Method chosen: ☐ Manual ☐ API
  - [ ] rivet_commands.json imported
  - [ ] rivet_stripe_webhook.json imported
  - [ ] rivet_stripe_checkout.json imported
  - [ ] rivet_chat_with_print.json imported
  - [ ] rivet_usage_tracker.json imported

- [ ] **Configure credentials in each workflow**
  - [ ] All Telegram nodes → `Telegram Bot`
  - [ ] All Postgres nodes → `Neon RIVET`
  - [ ] All Stripe nodes → `Stripe RIVET`

- [ ] **Update Stripe Price ID:**
  - [ ] Opened `rivet_stripe_checkout.json` in n8n
  - [ ] Found "Create Stripe Checkout" node
  - [ ] Replaced `REPLACE_WITH_STRIPE_PRICE_ID` with actual Price ID
  - [ ] Workflow saved

**Reference:** See `docs/STRIPE_SETUP_GUIDE.md` Part 2.3 & Part 3

---

### Part 3D: Workflow Activation (IN ORDER!)

**CRITICAL:** Activate in this exact order:

1. [ ] **Commands** (`rivet_commands.json`)
   - [ ] Activated
   - [ ] Test: `/start`, `/help`

2. [ ] **Stripe Webhook** (`rivet_stripe_webhook.json`)
   - [ ] Activated
   - [ ] Test: Stripe CLI event

3. [ ] **Stripe Checkout** (`rivet_stripe_checkout.json`)
   - [ ] Activated
   - [ ] Test: `/upgrade`

4. [ ] **Chat with Print** (`rivet_chat_with_print.json`)
   - [ ] Activated
   - [ ] Test: PDF upload

5. [ ] **Usage Tracker** (`rivet_usage_tracker.json`)
   - [ ] Activated
   - [ ] Test: Photo upload
   - [ ] **Keep production bot active during testing!**

---

### Part 3E: Individual Workflow Testing

- [ ] Commands: All tests pass (see TESTING_GUIDE.md)
- [ ] Stripe Webhook: All tests pass
- [ ] Stripe Checkout: All tests pass
- [ ] Usage Tracker: All tests pass
- [ ] Chat with Print: All tests pass

---

### Part 3F: End-to-End Journeys

- [ ] Journey 1: Free User Discovery (complete)
- [ ] Journey 2: Upgrade Flow (complete)
- [ ] Journey 3: Pro User Full Features (complete)

---

### Part 3G: Database Validation

- [ ] rivet_users table populated correctly
- [ ] rivet_usage_log logging all actions
- [ ] rivet_print_sessions storing PDFs
- [ ] rivet_stripe_events logging webhooks

---

## Phase 4: Production Preparation

### Part 4A: Stripe Production Setup

- [ ] Switch to Live Mode in Stripe
- [ ] Create LIVE product & price
- [ ] **LIVE Price ID:** `price_________________`
- [ ] Configure LIVE webhook endpoint

### Part 4B: n8n Production Credentials

- [ ] Create `Stripe RIVET LIVE` credential
- [ ] Update workflows to use LIVE credentials
- [ ] Update LIVE Price ID in workflow

### Part 4C: Pre-Production Testing

- [ ] Test `/upgrade` with LIVE credentials (don't complete payment)
- [ ] Verify checkout shows LIVE mode
- [ ] Test webhook delivery in LIVE mode

### Part 4D: Production Deployment

- [ ] Deactivate test versions
- [ ] Activate production versions (in order!)
- [ ] Monitor first users closely

### Part 4E: Rollback Plan

- [ ] Document rollback procedure
- [ ] Keep production workflow ID: 7LMKcMmldZsu1l6g
- [ ] Test rollback before go-live

---

## Phase 5: Post-Launch Monitoring

### First 24 Hours

- [ ] Monitor all executions
- [ ] Check Stripe dashboard
- [ ] Verify database integrity
- [ ] Respond to user feedback

### Metrics to Track

- [ ] MRR (Monthly Recurring Revenue)
- [ ] Conversion rate (free → Pro)
- [ ] Churn rate
- [ ] Workflow success rate
- [ ] Error rate

---

## Sign-Off

- [ ] All tests passed
- [ ] Documentation complete
- [ ] Ready for production
- [ ] Name: _________________ Date: _______

---

## Current Status

**Last Updated:** January 8, 2026

**Phase Status:**
- ✅ Phase 0: Prerequisites
- ✅ Phase 1: Database Schema
- ✅ Phase 2: n8n Workflows
- ⏳ Phase 3: Configuration & Testing (IN PROGRESS)

**Next Action:**
Complete Part 3A: Stripe Dashboard Setup

---

## Quick Reference

### Important URLs
- n8n: http://72.60.175.144:5678
- Stripe Dashboard: https://dashboard.stripe.com
- Telegram Bot: @rivet_local_dev_bot

### Important IDs
- Production Workflow: 7LMKcMmldZsu1l6g
- Telegram Credential: if4EOJbvMirfWqCC

### Test Card
- Number: 4242 4242 4242 4242
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

---

**See detailed guides:**
- `docs/STRIPE_SETUP_GUIDE.md` - Complete Stripe configuration
- `docs/TESTING_GUIDE.md` - Comprehensive testing procedures

