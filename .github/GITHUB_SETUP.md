# GitHub Claude Integration Setup

## Overview
This repository is configured to respond to `@claude` mentions in issues and pull requests. Claude will have full access to the codebase and follow the instructions in `CLAUDE.md`.

## Setup Steps

### 1. Add API Key to GitHub Secrets

1. Go to your repository settings:
   ```
   https://github.com/Mikecranesync/Agent-Factory/settings/secrets/actions
   ```

2. Click **"New repository secret"**

3. Add the following secret:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Value:** Your Anthropic API key (starts with `sk-ant-`)

   > **Where to get an API key:**
   > - Go to https://console.anthropic.com/
   > - Navigate to "API Keys"
   > - Create a new key or copy an existing one

4. Click **"Add secret"**

### 2. Verify Workflow File

The workflow file is already created at `.github/workflows/claude.yml`. No action needed.

### 3. Test the Integration

After adding the API key:

1. **Create a test issue:**
   - Go to https://github.com/Mikecranesync/Agent-Factory/issues/new
   - Title: "Test Claude Integration"
   - Body: "@claude Please summarize what this repository does"

2. **Wait for Claude to respond:**
   - The GitHub Action will trigger automatically
   - Claude will analyze the repo and respond in a comment
   - First run may take 1-2 minutes

## How to Use

### On Issues
Comment `@claude` followed by your request:
- `@claude What does the AgentFactory class do?`
- `@claude Can you explain the orchestrator pattern?`
- `@claude Where is the Project Twin feature implemented?`

### On Pull Requests
Comment `@claude` on PRs for code review:
- `@claude Please review this PR`
- `@claude Can you suggest improvements to this code?`
- `@claude Does this follow the project patterns in PATTERNS.md?`

### Advanced: Label-Based Triggering
Add a label called `claude` to any issue or PR to have Claude automatically analyze it without needing to comment.

## What Claude Can Do

- ✅ Answer questions about code structure and architecture
- ✅ Explain functions, classes, and patterns
- ✅ Review code changes in pull requests
- ✅ Suggest improvements and optimizations
- ✅ Find bugs and security issues
- ✅ Implement code changes (when requested)
- ✅ Create new files or modify existing ones
- ✅ Follow project-specific guidelines from `CLAUDE.md`

## Permissions

The Claude GitHub Action has the following permissions:
- **Contents:** Write (to make code changes)
- **Issues:** Write (to comment on issues)
- **Pull Requests:** Write (to comment and create PRs)

## Triggers

Claude will activate when:
1. Someone comments `@claude` on an issue
2. Someone comments `@claude` on a PR or PR review
3. An issue is labeled with `claude`
4. A PR is labeled with `claude`

## Security

- API keys are stored securely in GitHub Secrets
- Never commit API keys to the repository
- Claude only has access to this specific repository
- All actions are logged in GitHub Actions tab

## Troubleshooting

### Claude doesn't respond
1. Check that `ANTHROPIC_API_KEY` is set in repository secrets
2. Verify the workflow file exists at `.github/workflows/claude.yml`
3. Check the "Actions" tab for error messages

### Permission errors
1. Ensure workflow has `write` permissions for contents, issues, and pull-requests
2. Check repository settings → Actions → General → Workflow permissions

### Rate limiting
If you see rate limit errors, consider:
- Using fewer Claude requests
- Upgrading your Anthropic API plan
- Using label-based triggering sparingly

## Cost Management

Claude API calls cost money. To manage costs:
- Only use `@claude` when needed (not on every comment)
- Use label-based triggering for important issues only
- Monitor usage at https://console.anthropic.com/usage
- Set billing limits in Anthropic console

## Next Steps

1. Add `ANTHROPIC_API_KEY` to repository secrets (required)
2. Test with a sample issue
3. Start using `@claude` in your development workflow

## Support

- Claude Code documentation: https://code.claude.com/docs
- GitHub Action repo: https://github.com/anthropics/claude-code-action
- Anthropic support: https://support.anthropic.com
