# Pilot Watchdog MVP: The Garage Blueprint
## From zero to "AI knows your machine better than you do" in 4-8 weeks

---

## Executive summary

Build a scrappy, self-contained rig that proves **Pilot**: a watchdog system that learns normal PLC cycles and flags drift/degradation *before* the PLC itself faults. Use cheap hardware, simple logic, and visual demos to show the value on social media and to early customers.

**Target outcome:** A YouTube-ready demo where you throttle air to a cylinder, Pilot warns yellow while PLC stays green, then you push it further and PLC faults—all in 30 seconds of compelling video.

---

## Phase 0: Bill of materials (~$300-$500)

### Control & compute
- **PLC**: Click PLC (AutomationDirect) or equivalent ~$150-$200
  - Built-in Ethernet, easy to program, cheap
  - Alternative: cheap Siemens S7-1200 if you want real industrial credibility
- **Laptop/desktop for logging**: anything you have (Python + sqlite3)
- **Network switch or direct Ethernet**: so PLC talks to your logger

### Hardware rig
- **Pneumatics kit** (~$100-$150)
  - Single-acting pneumatic cylinder (small, ~1-2 inch bore)
  - Two 3/2 solenoid valves (one for extend, one for retract)
  - Pressure regulator + gauge
  - Air compressor (borrow or use a cheap pancake compressor if you have one)
  - Quick-disconnect fittings, hose
- **Sensors** (~$50-$80)
  - Two reed switches or inductive sensors (one for cylinder extended, one for retracted)
  - Optional: pressure transducer (0-100 psi, 4-20 mA or 0-10V) if your PLC has analog input
- **Motor** (optional, for more visual appeal)
  - Small 24V DC motor (~$20) or just use a solenoid or relay-driven LED stack light
- **24V power supply** (~$30-$50): runs PLC, solenoids, and sensors
- **Stack light** (~$20-$30): red/yellow/green to show PLC OK vs Pilot warning
- **Miscellaneous**: DIN rail, terminal blocks, wire, connectors (~$30-$50)

### Optional but nice
- Small 7" HMI touchscreen panel (if you want to display cycle times and trends live) ~$100-$150
  - or just use a cheap web dashboard on your laptop

---

## Phase 1: Hardware assembly (Week 1)

### 1a. Mount the rig
- Use a small sheet of plywood or aluminum extrusion frame as your base (~2 ft × 2 ft).
- Mount the PLC, power supply, and valve manifold on DIN rail.
- Mount the cylinder horizontally or vertically (doesn't matter; horizontal is easier to see).
- Wire everything 24V, ground common to PLC.

### 1b. Wiring diagram (conceptual)
```
24V power supply:
  → PLC power input
  → Solenoid valve coils (through 24V relay outputs from PLC)
  → Stack light (through relay or PLC output)

Sensors (24V inputs to PLC):
  - Cylinder extended reed switch → DI0
  - Cylinder retracted reed switch → DI1
  - Optional pressure transducer → AI0 (analog input)

Outputs from PLC (24V):
  - Extend solenoid → DO0
  - Retract solenoid → DO1
  - Yellow light (warning) → DO2
  - Green light (OK) → DO3
```

### 1c. Test basic IO
- Power up, run a manual test:
  - Command extend, confirm solenoid clicks and cylinder extends.
  - Confirm extended sensor reads true on PLC.
  - Repeat for retract.
- This is boring but saves hours of debugging later.

---

## Phase 2: PLC base program (Week 1-2)

### 2a. Define the machine cycle
Simple state machine in structured text (IEC 61131-3) or ladder:

```
MAIN CYCLE (runs every scan):
  CASE machine_state OF
    0 (IDLE):
      IF start_button OR auto_cycle THEN
        machine_state := 1
        cycle_start_time := NOW
        cycle_count := cycle_count + 1
      END_IF

    1 (EXTEND):
      cmd_extend := TRUE
      IF sensor_extended THEN
        machine_state := 2
        extend_time := NOW - cycle_start_time
      ELSIF (NOW - cycle_start_time) > T#5s THEN
        machine_fault := TRUE
        machine_state := 99 (FAULT)
      END_IF

    2 (RETRACT):
      cmd_extend := FALSE
      IF sensor_retracted THEN
        machine_state := 3
        retract_time := NOW - cycle_start_time
      ELSIF (NOW - cycle_start_time) > T#5s THEN
        machine_fault := TRUE
        machine_state := 99 (FAULT)
      END_IF

    3 (DWELL):
      // Optional: hold retracted for a second before next cycle
      IF (NOW - cycle_start_time) > T#1s THEN
        machine_state := 0 (IDLE)
        // Ready for next cycle
      END_IF

    99 (FAULT):
      cmd_extend := FALSE
      stack_light_red := TRUE
      // Wait for manual reset
  END_CASE
```

### 2b. Output control
- `cmd_extend` drives the solenoid relays.
- `stack_light_green` = NOT machine_fault
- `stack_light_red` = machine_fault

### 2c. Data logging block
Store per-cycle info in a structure or array:

```
TYPE Cycle_Record:
  cycle_id: DINT
  cycle_start: TIME
  extend_time: DINT  // ms
  retract_time: DINT  // ms
  sensor_extended: BOOL
  sensor_retracted: BOOL
  machine_fault: BOOL
END_TYPE

VAR
  cycle_log: ARRAY[0..999] OF Cycle_Record
  cycle_idx: DINT := 0
END_VAR

// Log every cycle
IF machine_state = 3 THEN // Just completed a cycle
  cycle_log[cycle_idx].cycle_id := cycle_count
  cycle_log[cycle_idx].extend_time := extend_time
  cycle_log[cycle_idx].retract_time := retract_time
  cycle_log[cycle_idx].sensor_extended := sensor_extended
  cycle_log[cycle_idx].sensor_retracted := sensor_retracted
  cycle_log[cycle_idx].machine_fault := machine_fault
  cycle_idx := (cycle_idx + 1) MOD 1000
END_IF
```

---

## Phase 3: Pilot watchdog logic (Week 2)

### 3a. Pilot state machine (separate task, runs every 100 ms or slower)

```
TASK Pilot_Watch (INTERVAL = T#100ms)

VAR
  pilot_baseline_extend: DINT := 1000  // ms, initial guess
  pilot_baseline_retract: DINT := 1000
  pilot_margin: DINT := 200  // tolerance, ms
  pilot_warn_slow_extend: BOOL := FALSE
  pilot_warn_slow_retract: BOOL := FALSE
  pilot_disagree: BOOL := FALSE
  pilot_cycles_warning: INT := 0
  pilot_confidence: INT := 0  // 0-100, how many good cycles seen
END_VAR

// Detect new cycle completion
last_cycle_count_seen: DINT := 0
IF cycle_count > last_cycle_count_seen THEN
  last_cycle_count_seen := cycle_count

  // Get latest log entry
  latest := cycle_log[(cycle_idx - 1) MOD 1000]

  // Update baseline if we have enough good data and no faults
  IF pilot_confidence < 100 AND NOT latest.machine_fault THEN
    pilot_baseline_extend := (pilot_baseline_extend * 9 + latest.extend_time) / 10
    pilot_baseline_retract := (pilot_baseline_retract * 9 + latest.retract_time) / 10
    pilot_confidence := MIN(100, pilot_confidence + 1)
  END_IF

  // Check for drift
  pilot_warn_slow_extend := (latest.extend_time > pilot_baseline_extend + pilot_margin)
  pilot_warn_slow_retract := (latest.retract_time > pilot_baseline_retract + pilot_margin)

  // Disagreement: PLC thinks OK but Pilot warns
  pilot_disagree := (NOT latest.machine_fault) AND (pilot_warn_slow_extend OR pilot_warn_slow_retract)

  IF pilot_disagree THEN
    pilot_cycles_warning := pilot_cycles_warning + 1
  ELSE
    pilot_cycles_warning := 0
  END_IF

END_IF

// Output bits for HMI/stack light
pilot_ok := NOT pilot_disagree
pilot_warning := pilot_disagree
```

### 3b. Stack light logic
```
// Green: both PLC and Pilot agree, all good
stack_light_green := (NOT machine_fault) AND pilot_ok

// Yellow: PLC says OK but Pilot sees drift
stack_light_yellow := (NOT machine_fault) AND pilot_warning

// Red: PLC fault
stack_light_red := machine_fault
```

### 3c. What you've built
- A machine that runs cycles: extend, retract, repeat.
- A Pilot that learns the "normal" timing over the first ~10 cycles.
- A Pilot that flags when timings drift (yellow light).
- A way to compare "PLC OK" vs "Pilot warning."

---

## Phase 4: External logging & visualization (Week 2-3)

### 4a. Python logger (reads PLC over Modbus or direct socket)
If your PLC has Ethernet, use pymodbus or a simple socket to read tags every second.

```python
import sqlite3
import time
import struct
from datetime import datetime

# Simple SQLite database
conn = sqlite3.connect('pilot_data.db')
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE IF NOT EXISTS cycles (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    cycle_id INTEGER,
    extend_time INTEGER,
    retract_time INTEGER,
    machine_fault BOOLEAN,
    pilot_ok BOOLEAN,
    pilot_warning BOOLEAN
)''')
conn.commit()

# Main loop: read PLC every 1 second
last_cycle_id = -1
while True:
    # Read PLC tags (example using modbus)
    # This depends on your PLC type; adjust accordingly
    cycle_id = read_plc_tag('cycle_count')
    extend_time = read_plc_tag('latest_extend_time')
    retract_time = read_plc_tag('latest_retract_time')
    machine_fault = read_plc_tag('machine_fault')
    pilot_ok = read_plc_tag('pilot_ok')
    pilot_warning = read_plc_tag('pilot_warning')

    # Log new cycles
    if cycle_id > last_cycle_id:
        last_cycle_id = cycle_id
        c.execute('''INSERT INTO cycles
                     (timestamp, cycle_id, extend_time, retract_time, machine_fault, pilot_ok, pilot_warning)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.now().isoformat(), cycle_id, extend_time, retract_time,
                   machine_fault, pilot_ok, pilot_warning))
        conn.commit()
        print(f"Cycle {cycle_id}: extend={extend_time}ms, retract={retract_time}ms, pilot_ok={pilot_ok}")

    time.sleep(1)
```

### 4b. Simple web dashboard (Flask)
```python
from flask import Flask, render_template, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/data')
def get_data():
    conn = sqlite3.connect('pilot_data.db')
    c = conn.cursor()
    c.execute('SELECT timestamp, extend_time, retract_time, pilot_warning FROM cycles ORDER BY id DESC LIMIT 100')
    rows = c.fetchall()
    conn.close()

    return jsonify({
        'cycles': [{'time': r[0], 'extend': r[1], 'retract': r[2], 'warning': r[3]} for r in rows]
    })

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <h1>Pilot Watchdog Dashboard</h1>
            <canvas id="chart"></canvas>
            <script>
                fetch('/data').then(r => r.json()).then(data => {
                    const ctx = document.getElementById('chart').getContext('2d');
                    const chart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.cycles.map(c => c.time),
                            datasets: [{
                                label: 'Extend Time (ms)',
                                data: data.cycles.map(c => c.extend),
                                borderColor: 'blue'
                            }, {
                                label: 'Retract Time (ms)',
                                data: data.cycles.map(c => c.retract),
                                borderColor: 'green'
                            }, {
                                label: 'Pilot Warning',
                                data: data.cycles.map(c => c.warning ? 100 : 0),
                                borderColor: 'red',
                                fill: false
                            }]
                        }
                    });
                });
            </script>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## Phase 5: Demo scenarios & video (Week 3-4)

### 5a. Baseline run
1. Start the rig, let it run 50-100 cycles clean.
2. Watch stack light stay green, baseline timings settle in dashboard.
3. **Video moment**: "Machine running normally, Pilot and PLC in agreement."

### 5b. Induced failure: restrict air (slow cylinder)
1. During live run, partially close the air supply valve to the cylinder.
2. Extend time begins to drift upward (e.g., from 1000 ms to 1500 ms).
3. **Key moment**: Stack light goes YELLOW (Pilot warning), but PLC still GREEN.
4. Dashboard shows extend time trending up; warning counter increments.
5. **Video moment**: "Pilot detected degradation 20 cycles ago; PLC has no idea yet."

### 5c. Push to failure
1. Close air valve more; extend time now 3000+ ms.
2. PLC timeout fires, stack light goes RED.
3. **Video moment**: "PLC finally faults, but Pilot was warning the whole time."

### 5d. Dashboard snapshot
- Screenshot showing the time-series: green (baseline), yellow region (Pilot warning), red region (PLC fault).
- Caption: "Pilot saw it coming 45 minutes of operation before the PLC."

---

## Phase 6: Social & positioning (Week 4+)

### 6a. Short-form video (TikTok, Instagram Reels, YouTube Shorts)
- 30 seconds, no voiceover needed:
  - Normal rig running (green lights).
  - Restrict air (lights go yellow, PLC still green).
  - Restrict more (lights go red).
  - Text overlay: "The AI that knows your machine is sick before it does."
  - Hashtags: #Industrial #AI #Maintenance #PLC #FactoryAI

### 6b. Long-form demo (YouTube, LinkedIn)
- 5-10 minutes:
  - Intro: "Most plants wait for a fault alarm. Here's what happens if your machine tells you it's getting sick days before."
  - Show the rig and hardware.
  - Run the baseline and induce failure in real time.
  - Explain Pilot logic (timeline, learning, pattern matching).
  - Close: "Imagine this on every line in your plant. We call it Pilot."

### 6c. One-pager for sales
- Headline: "Pilot Watchdog: Predictive Maintenance for PLCs"
- Subheading: "Detect machine degradation before downtime."
- Bullet points:
  - Learns normal cycle patterns in ~10-20 cycles.
  - Flags drift in timing, sequences, and anomalies.
  - Works with any PLC; logs over Ethernet.
  - Reduces unplanned downtime by alerting early.
  - No hardware changes needed; runs in shadow mode.
- Call to action: "Let's add Pilot to one of your lines for a pilot program."

---

## Phase 7: Scale from demo rig to real plant (Week 5-8)

### 7a. Generalize Pilot logic into a reusable FB
- Create a standard Pilot function block that you can drop into any PLC.
- Inputs: `cycle_id`, `step_timings[]`, `sensor_states[]`, optional analog values.
- Outputs: `pilot_ok`, `pilot_warning`, `pilot_disagree`, `anomaly_code`.
- Document it clearly so customers can integrate.

### 7b. Standardize logged data
- Define a minimal "Pilot data schema":
  - Cycle ID, step times, sensors, faults, timestamp.
  - Same structure regardless of machine or PLC brand.
- This becomes your competitive moat: every customer's data feeds into your model improvement pipeline.

### 7c. Find a friendly first customer
- Approach a local plant, ride, or crane shop.
- Offer: "We'll monitor one conveyor or assembly step for free for 2 weeks. You'll get a report on what we find."
- Goal: real-world proof that Pilot caught something (slow motor, drifting sensor, recurring micro-stop).

### 7d. Document the win
- Case study: "Pilot found X problem on Customer Y's line, saving them Z hours/year of downtime."
- Use that case study for all future sales pitches and content.

---

## Technical debt & next steps

### 8a. Short term (post-MVP)
- Generalize Pilot FB for multiple PLC types (Siemens, AB, Click).
- Build an SDK so integrators can plug in their own anomaly-detection logic.
- Create a simple mobile app so you can check Pilot status from your phone.

### 8b. Medium term (next 6-12 months)
- Tie Pilot into your agent factory: feed Pilot data into models so robots learn normal cycles.
- Add vision: overlay Pilot PLC data with your flashlight camera feed, so you see what the machine was doing when Pilot flagged a warning.
- Expand to multiple lines: show how Pilot can compare baseline across a plant (e.g., "Line 3 is running 15% slower than Line 2").

### 8c. Long term (1-2 years)
- License Pilot to OEMs and big integrators (Siemens, Beckhoff, etc.) so it ships built-in.
- Fold into your broader "Field Eye" + "inspection tricorder" + "robot standard" vision.

---

## Why this works

1. **Low barrier to entry**: $300-500 hardware, free/cheap software, nothing proprietary.
2. **High compelling value**: Yellow light vs. green light is obvious; the idea is easy to explain and impressive on video.
3. **Scalable pitch**: works on a garage rig, scales to real plants with minimal changes.
4. **Defensible moat**: once you have data and patterns from hundreds of customer machines, your Pilot models are hard to replicate.
5. **Feeds your broader vision**: Pilot is the sensory layer of your agent factory; it's the PLC's confession about what's really happening, and robots will need that to learn safely.

---

## Go/no-go decision checklist

- [ ] You have access to a PLC (or can afford a Click for $150).
- [ ] You can source pneumatics kit (~$100-150) from AutomationDirect or Surplus Center.
- [ ] You have a Windows/Linux laptop that can run Python and a web browser.
- [ ] You have ~20 hours over the next 4 weeks to assemble, code, and film.
- [ ] You're comfortable with basic PLC logic (state machines, timers).
- [ ] You're willing to post short videos and write a one-pager to sell the idea.

If all checked: **Go build it.**

---

## File structure for your GitHub / documentation
```
pilot-mvp/
├── README.md (this file, basically)
├── hardware/
│   ├── BOM.csv
│   ├── wiring_diagram.png
│   └── mounting_notes.md
├── plc_code/
│   ├── main_cycle.st (structured text)
│   ├── pilot_watchdog.st
│   └── README.md (how to load onto your PLC)
├── logger/
│   ├── plc_reader.py (reads PLC via modbus/socket)
│   ├── dashboard.py (Flask web app)
│   └── requirements.txt
├── docs/
│   ├── how_pilot_works.md
│   ├── case_study_template.md
│   └── sales_one_pager.md
├── video/
│   ├── script_30sec.txt
│   ├── script_long_form.txt
│   └── clips/ (screenshots, edited footage)
└── ROADMAP.md (phases 7-8 above)
```

---

## Contact & next steps

Once you've got hardware in hand (week 1), post a photo in your normal channels: "Building the watchdog AI for PLCs. Here's what $300 of garage hardware looks like when it learns to catch machine degradation before it happens. Stay tuned."

By week 3, you'll have a video that will blow up on LinkedIn, TikTok, and YouTube because it's visual, unusual, and very relevant to every plant and maintenance team in the world.

**Good luck. Build it.**
