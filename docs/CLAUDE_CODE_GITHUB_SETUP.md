# Claude Code GitHub Actions Setup

**Status:** ✅ Workflow Created
**Cost:** ~$5-15/month (Claude API usage only)
**Replaces:** CodeRabbit ($12-24/month)

---

## What This Does

Automatically runs Claude Code reviews on every pull request using your Agent Factory's `CLAUDE.md` standards.

**Features:**
- ✅ Reviews PRs automatically on open/update
- ✅ Responds to `@claude` mentions in PR comments
- ✅ Uses `CLAUDE.md` for project-specific rules
- ✅ Checks for reward hacking, security issues, missing tests
- ✅ No rate limits (GitHub Actions handles throttling)
- ✅ Full repository context (not just diff like CodeRabbit)

---

## Setup Steps

### 1. Get Your Anthropic API Key

If you don't have one already:

1. Go to: https://console.anthropic.com/
2. Navigate to: **API Keys** → **Create Key**
3. Copy the key (starts with `sk-ant-...`)

**Note:** You likely already have this since you're using Claude Code CLI locally.

### 2. Add GitHub Secret

1. Go to your Agent Factory repository on GitHub
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click: **New repository secret**
4. Add:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Value:** Your API key (e.g., `sk-ant-api03-...`)
5. Click: **Add secret**

### 3. Verify Workflow File Exists

The workflow file should already exist at:
```
.github/workflows/claude-code-review.yml
```

If not, it's in this commit.

### 4. Test It

Create a test PR to verify setup:

```bash
# Create a test branch
git checkout -b test-claude-review

# Make a small change
echo "# Test PR for Claude Code review" >> TEST.md
git add TEST.md
git commit -m "test: Verify Claude Code review workflow"

# Push and create PR
git push -u origin test-claude-review
gh pr create --title "Test: Claude Code Review" --body "Testing automated Claude reviews"
```

**Expected Behavior:**
- Within 30-60 seconds, Claude will comment on the PR
- Comment will include ✅ What's good, ⚠️ Issues, 💡 Suggestions, 🔒 Security
- You can also comment `@claude review this change` to trigger manually

### 5. Merge and Cleanup

Once verified working:

```bash
# Delete test branch
gh pr close --delete-branch
git checkout main
```

---

## Usage

### Automatic Reviews

Claude automatically reviews when:
- PR is opened
- PR is updated (new commits pushed)
- PR is reopened

### Manual Reviews

Trigger Claude by commenting on a PR:
```
@claude review this change
```

Or:
```
@claude check for security issues in this PR
```

Claude will respond inline with a review.

---

## Cost Breakdown

**Estimated Monthly Cost:**
```
Assumptions:
- 50 PRs per month
- Average 500 lines changed per PR
- 5 review turns per PR

Cost Calculation:
- Claude Opus 4.5: ~$0.10 per PR review
- 50 PRs × $0.10 = $5/month

Heavy usage (200 PRs/month): ~$20/month
```

**vs CodeRabbit:**
- CodeRabbit Lite: $12/month (with rate limits)
- CodeRabbit Pro: $24/month

**Savings:** 60-75% cheaper + no rate limits

---

## Customization

### Change Model

To use a cheaper model (e.g., Sonnet 4.5):

Edit `.github/workflows/claude-code-review.yml`:
```yaml
claude_args: |
  --max-turns 5
  --model claude-sonnet-4-5-20250929  # Changed from opus
```

**Cost Savings:** ~80% cheaper ($0.02 per review vs $0.10)
**Trade-off:** Slightly less thorough reviews

### Change Review Depth

For faster reviews (fewer turns):
```yaml
claude_args: |
  --max-turns 3  # Changed from 5
```

For deeper reviews (more turns):
```yaml
claude_args: |
  --max-turns 10  # Increased from 5
```

### Add Custom Checks

Edit the `prompt:` section in the workflow file to add project-specific checks:
```yaml
prompt: |
  Review this PR using CLAUDE.md standards.

  Additionally check:
  - All new agents have comprehensive tests
  - Database migrations include rollback scripts
  - API endpoints have rate limiting
  - ... your custom rules ...
```

---

## Troubleshooting

### Issue: Claude doesn't comment on PR

**Check:**
1. GitHub secret `ANTHROPIC_API_KEY` is set correctly
2. Workflow file exists at `.github/workflows/claude-code-review.yml`
3. PR has actual code changes (not just README updates)
4. GitHub Actions is enabled (Settings → Actions → Allow all actions)

**View logs:**
```bash
gh run list --workflow claude-code-review.yml --limit 5
gh run view <run-id> --log
```

### Issue: API key error

**Error message:** `Authentication failed`

**Fix:**
1. Regenerate API key at https://console.anthropic.com/
2. Update GitHub secret `ANTHROPIC_API_KEY`
3. Re-run the failed workflow:
   ```bash
   gh run rerun <run-id>
   ```

### Issue: Cost too high

**Solutions:**
1. Switch to Sonnet 4.5 (80% cheaper)
2. Reduce `--max-turns` from 5 to 3
3. Only review PRs with `review-needed` label:
   ```yaml
   if: contains(github.event.pull_request.labels.*.name, 'review-needed')
   ```

---

## Comparison: Claude vs CodeRabbit

| Feature | Claude Code | CodeRabbit |
|---------|------------|------------|
| **Cost** | ~$5-15/mo | $12-24/mo |
| **Rate Limits** | None (GitHub Actions) | Easy to hit |
| **Context** | Full repo + CLAUDE.md | Diff only |
| **Customization** | Full prompt control | Limited |
| **Setup Time** | 5 min | 5 min |
| **Works Offline** | No (API only) | Yes (CLI exists) |

**Hybrid Strategy (Recommended):**
- **GitHub:** Claude Code (automatic, free-ish)
- **Pre-commit (local):** CodeRabbit CLI ($12/mo)
- **Total:** ~$15-20/mo vs $24+ for CodeRabbit alone

---

## Next Steps

1. ✅ Workflow file created (`.github/workflows/claude-code-review.yml`)
2. ⏳ **YOU:** Add `ANTHROPIC_API_KEY` to GitHub secrets
3. ⏳ **YOU:** Create test PR to verify
4. ⏳ Optional: Install CodeRabbit CLI for local pre-commit reviews
   ```bash
   npm install -g @coderabbitai/cli
   ```

---

## Documentation References

- Claude Code GitHub Actions: https://code.claude.com/docs/en/github-actions
- Anthropic API Keys: https://console.anthropic.com/
- GitHub Actions Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets

---

**Created:** 2025-12-20
**Author:** Claude Code
**Purpose:** Replace CodeRabbit with cost-effective Claude Code reviews
