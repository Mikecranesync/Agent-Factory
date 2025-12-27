# VPS Bot Rollback Instructions

## Date: 2025-12-27 02:30 AM

## Current State (BEFORE changes)

### Running Processes:
```
PID 3539:  orchestrator_bot (systemd service)
PID 4159623: telegram_bot.py (manual nohup)
```

### Tokens:
- TELEGRAM_BOT_TOKEN: 8208278660:AAGz6v7dIPMnfepp-UFMCwdUpOAeqYeOT84
- ORCHESTRATOR_BOT_TOKEN: 7910254197:AAGeEqMI_rvJExOsZVrTLc_0fb26CQKqlHQ

## Changes Made

1. ✅ Killed old telegram_bot.py (PID 4159623, 4159622)
2. ✅ Started production bot: `python -m agent_factory.integrations.telegram` (PID 5809)
3. ✅ Production bot running cleanly - NO CONFLICTS!
4. ⚠️ Orchestrator service remains running (PID 3539, different token, no conflict)
5. 🔄 Local scheduled task needs to be disabled (next step)

## Production Bot Status (FINAL)
- Bot: orchestrator-bot (PID: 16587)
- Service: systemd orchestrator-bot.service
- Status: ✅ Running successfully, no conflicts
- Features:
  - ✅ Voice → Whisper → Orchestrator routing (WS-3 COMPLETE)
  - ✅ Photo OCR with Claude Vision
  - ✅ Text messages → A/B/C/D orchestrator routing
  - ✅ KB search integration (5 atoms cited)
  - ✅ Safety warnings + Citations
  - ✅ 30+ commands (library, kb, fieldeye, etc.)

## WS-3 Test Results (2025-12-27 03:27 AM)
- Voice: "How do I tell if a motor is good or bad?"
- Transcription: ✅ Perfect (Whisper-1)
- Routing: ✅ Route B (SME enrichment, 71% confidence)
- KB: ✅ 5 Siemens atoms cited
- Response: ✅ Complete troubleshooting guide with safety warnings

## Rollback Steps (if needed)

### SSH into VPS:
```bash
ssh root@72.60.175.144
```

### Stop new production bot:
```bash
pkill -f 'python -m agent_factory.integrations.telegram'
```

### Restart old telegram_bot.py:
```bash
cd /root/Agent-Factory
nohup /root/.cache/pypoetry/virtualenvs/agent-factory-5pZqsWAA-py3.12/bin/python telegram_bot.py > bot_logs.txt 2>&1 &
```

### Verify old bot is running:
```bash
ps aux | grep telegram_bot.py | grep -v grep
tail -f /root/Agent-Factory/bot_logs.txt
```

## Notes
- Local scheduled task will be disabled (was causing conflicts)
- Orchestrator service remains enabled (uses different token)
- Production bot has all WS-3 features (voice, photos, full handlers)
