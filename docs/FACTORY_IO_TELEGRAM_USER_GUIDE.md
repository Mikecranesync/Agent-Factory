# Factory.io Telegram Bot - User Guide

**Last Updated:** 2026-01-01
**Version:** 1.0 (Force/Release API Integration)
**Status:** Production Ready

---

## What is This?

A Telegram bot that turns your phone into a **PLC HMI** (Human-Machine Interface) for controlling Factory.io simulations in real-time. Monitor sensors, control motors, and manage industrial automation from anywhere.

---

## Features

### Real-Time Monitoring
- **Live I/O Status**: See inputs (sensors) and outputs (motors) update every 5 seconds
- **Connection Status**: Instant alerts when Factory.io goes offline
- **Visual Indicators**: 🟢 ON / ⚫ OFF status with emoji labels

### Manual Control (Force Mode)
- **ON/OFF Buttons**: Force outputs to specific states (bypasses PLC logic)
- **Emergency Stop**: Instantly shut down all configured outputs
- **Clear Forces**: Release individual forced tags
- **Refresh**: Clear all forced tags and return to normal operation

### Persistent Messaging
- **Single Message**: Bot updates ONE message continuously (no spam)
- **Last Update Timestamp**: See when data was last refreshed
- **Force Indicators**: See which tags are forced with ⚠️ FORCED label

---

## Setup Guide

### Prerequisites

1. **Factory.io** installed on Windows
2. **Telegram account** and Telegram Desktop or mobile app
3. **Python 3.10+** and Poetry installed
4. **Factory.io Web API** enabled (see below)

### Step 1: Enable Factory.io Web API

1. Launch Factory.io
2. Load your scene (or create a new one)
3. Press **Ctrl + ~** (opens console)
4. Type: `app.web_server = True`
5. Verify: `app.web_server_url` (should show `http://localhost:7410`)

Test it works:
```bash
curl http://localhost:7410/api/tags
```

You should see a JSON response with your scene's tags.

---

### Step 2: Configure machines.yaml

Edit `agent_factory/config/machines.yaml`:

```yaml
machines:
  - machine_id: scene1_sorting        # Unique ID
    scene_name: "Sorting System"      # Display name
    factory_io_url: "http://localhost:7410"
    telegram_chat_id: -1234567890     # Your Telegram group chat ID
    poll_interval_seconds: 5          # How often to check Factory.io

    # Input tags to monitor (sensors, switches, etc.)
    monitored_inputs:
      - tag: "Sensor"                  # Tag name in Factory.io
        label: "Sensor"                # Display label
        comment: "Input Sensor"        # Description
        emoji: "📦"                    # Visual indicator

    # Output tags you can control (motors, lights, etc.)
    controllable_outputs:
      - tag: "Conveyor"
        label: "Conveyor"
        comment: "Conveyor Motor"
        emoji: "▶️"

    # Tags to turn OFF on emergency stop
    emergency_stop_tags:
      - "Conveyor"
```

**How to get telegram_chat_id:**
```bash
# Run the bot once, send a message to it, then check logs
poetry run python test_telegram_live.py
# Look for "Chat ID: -1234567890" in console output
```

---

### Step 3: Start the Bot

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
poetry run python test_telegram_live.py
```

You should see:
```
INFO:agent_factory.platform.telegram.telegram_adapter:TelegramAdapter initialized
INFO:agent_factory.platform.state.machine_state_manager:Starting background tasks for 1 machine(s)
INFO:agent_factory.platform.state.machine_state_manager:Started polling scene1_sorting (every 5s)
Bot started. Press Ctrl+C to stop.
```

---

## Using the Bot

### Message Layout

```
SORTING SYSTEM (🟢 ONLINE)

📥 INPUTS:
🟢 Sensor (Input Sensor)

📤 OUTPUTS:
⚫ Conveyor (Conveyor Motor)

Last update: 18:46:08

[ON] [OFF] [Clear]
[⛔ EMERGENCY STOP]
[🔄 Refresh]
```

### Button Functions

#### ON Button
- **Purpose**: Force output tag to TRUE (motor runs)
- **Use Case**: Manual operation, testing, maintenance
- **Example**: Click [ON] → Conveyor forced ON → Physical conveyor moves in Factory.io
- **Indicator**: "⚠️ FORCED" appears next to tag

#### OFF Button
- **Purpose**: Force output tag to FALSE (motor stops)
- **Use Case**: Manual shutdown, safety
- **Example**: Click [OFF] → Conveyor forced OFF → Physical conveyor stops
- **Indicator**: "⚠️ FORCED" appears next to tag

#### Clear Button
- **Purpose**: Release force from ONE specific tag
- **Use Case**: Return single output to normal operation
- **Example**: Click [Clear] next to Conveyor → Conveyor returns to logic control (if no logic, stays OFF)
- **Result**: "⚠️ FORCED" indicator disappears

#### Emergency Stop Button
- **Purpose**: Force ALL configured outputs to OFF immediately
- **Use Case**: Safety hazard, equipment malfunction
- **Example**: Click [⛔ EMERGENCY STOP] → All outputs in `emergency_stop_tags` turn OFF
- **Toast**: "⛔ EMERGENCY STOP ACTIVATED"

#### Refresh Button
- **Purpose**: Clear ALL forced tags across entire machine
- **Use Case**: Reset to normal operation after manual intervention
- **Example**: Click [🔄 Refresh] → All forced tags released → Message updates to show actual Factory.io state
- **Toast**: "🔄 Refreshed - All forces cleared"

---

## Understanding Force Mode

### What is "Force"?

**Force** means overriding PLC logic and holding an output at a specific value.

**Without PLC Logic:**
- Regular writes don't "stick" - output immediately returns to default state
- Force is **MANDATORY** to manually control outputs
- This is the current implementation

**With PLC Logic:**
- Force overrides logic (motor runs even if logic says stop)
- Release force → output returns to logic-controlled state

### Force vs Write (Technical)

| Action | API Endpoint | When to Use |
|--------|-------------|-------------|
| **Force** | `/api/tag/values-force/by-name` | Manual HMI control (no logic running) |
| **Write** | `/api/tag/values/by-name` | With PLC logic (normal operation) |
| **Release** | `/api/tag/values-release/by-name` | Return to normal operation |

Current implementation uses **Force** for ON/OFF buttons.

---

## Troubleshooting

### Bot Shows "🔴 OFFLINE"

**Symptoms:**
- Message shows "OFFLINE" instead of "ONLINE"
- All tags show ⚫ (off)
- Circuit breaker status: OPEN

**Diagnosis:**
- Factory.io Web API not enabled
- Factory.io not running
- Wrong port (should be 7410)

**Solution:**
1. Open Factory.io console (Ctrl+~)
2. Run: `app.web_server = True`
3. Verify: `app.web_server_url`
4. Test: `curl http://localhost:7410/api/tags`
5. Bot will auto-recover in 5-30 seconds (circuit breaker)

---

### Buttons Show Success But Nothing Happens

**Symptoms:**
- Toast shows "✅ Forced conveyor = ON"
- Factory.io conveyor doesn't move
- No errors in bot logs

**Diagnosis:**
- Tag name mismatch (case-sensitive)
- Tag doesn't exist in current scene
- Factory.io scene not loaded

**Solution:**
1. Check available tags: `curl http://localhost:7410/api/tags`
2. Verify tag name matches EXACTLY (case-sensitive)
3. Update `machines.yaml` with correct tag names
4. Restart bot: Ctrl+C → `poetry run python test_telegram_live.py`

---

### Message Spam (Multiple Messages)

**Symptoms:**
- New message created every 5+ seconds
- Chat flooded with duplicate messages

**Diagnosis:**
- `edit_threshold_seconds` too low
- Message tracking issue

**Solution:**
- Check `agent_factory/platform/telegram/telegram_adapter.py` line 234
- Should be: `edit_threshold_seconds: int = 3600` (1 hour)
- Restart bot to pick up changes

---

### Rate Limiting Error

**Symptoms:**
- Toast shows "⏳ Please wait before pressing another button"
- Buttons temporarily disabled

**This is NORMAL:**
- Built-in rate limiting prevents API spam
- Wait 2 seconds between button clicks
- Prevents Factory.io errors from rapid requests

---

## Configuration Reference

### machines.yaml Schema

```yaml
machines:
  - machine_id: string              # Required - Unique ID (alphanumeric + underscores)
    scene_name: string              # Required - Display name
    factory_io_url: string          # Default: http://localhost:7410
    telegram_chat_id: integer       # Required - Telegram group ID
    poll_interval_seconds: integer  # Default: 5 (range: 1-60)

    monitored_inputs:               # List of input tags
      - tag: string                 # Tag name (case-sensitive)
        label: string               # Display label
        comment: string             # Description (optional)
        emoji: string               # Visual indicator (optional)

    controllable_outputs:           # List of output tags
      - tag: string
        label: string
        comment: string
        emoji: string

    emergency_stop_tags:            # List of tag names to force OFF on E-Stop
      - string
```

---

## Architecture

```
Telegram Chat
    ↓
TelegramAdapter (handles button clicks, message formatting)
    ↓
MachineStateManager (polls Factory.io every 5s, detects changes)
    ↓
ForceProvider (tracks forced tag states)
    ↓
FactoryIOReadWriteTool (communicates with Factory.io Web API)
    ↓
Factory.io Simulation (localhost:7410)
```

### Data Flow

1. **Background Polling**: MachineStateManager polls Factory.io every 5 seconds
2. **Change Detection**: Compares new state to cached state
3. **Message Update**: If changes detected, updates Telegram message
4. **Button Click**: User clicks button → TelegramAdapter handles callback
5. **Force Tag**: FactoryIOReadWriteTool forces tag via Web API
6. **Update UI**: Message shows "⚠️ FORCED" indicator

---

## Advanced Usage

### Multiple Machines

Monitor multiple Factory.io instances or scenes:

```yaml
machines:
  - machine_id: scene1_sorting
    scene_name: "Sorting System"
    telegram_chat_id: -1111111111
    controllable_outputs:
      - tag: "Conveyor"

  - machine_id: scene2_bottling
    scene_name: "Bottling Line"
    telegram_chat_id: -2222222222
    controllable_outputs:
      - tag: "Filler"
      - tag: "Capper"
```

Each machine sends updates to its own Telegram group.

---

### Custom Poll Intervals

Adjust polling frequency per machine:

```yaml
poll_interval_seconds: 1   # Fast (1s) - High CPU usage
poll_interval_seconds: 5   # Recommended (5s)
poll_interval_seconds: 30  # Slow (30s) - Low CPU usage
```

---

### Tag Name Discovery

Don't know your tag names?

```bash
# List all tags in current scene
curl http://localhost:7410/api/tags

# Get specific tag by name
curl http://localhost:7410/api/tags/by-name/Conveyor

# Get tag values
curl -X GET http://localhost:7410/api/tag/values/by-name \
  -H "Content-Type: application/json" \
  -d '["Conveyor", "Sensor"]'
```

---

## Known Limitations

1. **No Scene Reset API**: Factory.io Web API doesn't support scene reset. Refresh button only clears forces, doesn't reload scene.

2. **Polling Delay**: State updates every 5 seconds (configurable). There's a slight lag between Factory.io changes and Telegram updates.

3. **Tag Name Case Sensitivity**: Tag names must match EXACTLY between `machines.yaml` and Factory.io scene.

4. **Single Chat Per Machine**: Each machine can only send updates to one Telegram chat.

5. **No PLC Logic Integration**: Current implementation assumes NO PLC logic running (force-only mode).

---

## Future Enhancements

- **START/STOP Controls**: Add normal automation sequences (requires PLC logic)
- **Multi-User Access Control**: Permissions per user
- **Historical State Logging**: Database logging for audit trail
- **Scene Reset Integration**: If Factory.io adds API support
- **Webhook Support**: Replace polling for production use
- **Mobile-Friendly Dashboard**: Web UI complement

---

## API Reference

### Factory.io Web API Endpoints Used

| Endpoint | Method | Purpose | Example Body |
|----------|--------|---------|--------------|
| `/api/tags` | GET | List all tags | N/A |
| `/api/tags/by-name/{name}` | GET | Get tag metadata | N/A |
| `/api/tag/values/by-name` | GET | Read tag values | `["Conveyor", "Sensor"]` |
| `/api/tag/values-force/by-name` | PUT | Force tags | `[{"name": "Conveyor", "value": true}]` |
| `/api/tag/values-release/by-name` | PUT | Release forced tags | `["Conveyor"]` |

---

## Support

**Issues:** Report bugs or feature requests at GitHub Issues

**Documentation:**
- `TELEGRAM_BOT_TESTING.md` - Testing procedures and troubleshooting
- `agent_factory/platform/telegram/telegram_adapter.py` - Implementation code
- `agent_factory/tools/factoryio/readwrite_tool.py` - Factory.io API client

**Community:** Join the Agent Factory Discord for support and discussions

---

## License

MIT License - See LICENSE file for details

---

**End of User Guide**
