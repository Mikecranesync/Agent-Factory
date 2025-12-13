# PLC Project Progression: Beginner to Medium Complexity
## From "Hello World" to Pilot Watchdog MVP

---

## Overview

This document outlines a **learning progression** of PLC projects, starting from absolute basics and building up to a medium-complexity **Pilot Watchdog MVP** system. Each project builds on skills from previous projects, following the spiral curriculum approach.

**Philosophy:** Learn by building. Each project introduces 1-3 new concepts while reinforcing previous skills.

**Target Timeline:** 8-12 weeks, spending 1-2 weeks per project depending on experience level.

**Hardware Requirements Progression:**
- **Beginner Projects (1-3):** Simulator only (free software)
- **Early Intermediate (4-6):** Basic PLC (~$150-200) + digital I/O
- **Late Intermediate (7-8):** Add sensors and actuators (~$100-200 total)
- **Medium Complexity (9):** Full demo rig (~$300-500 total)

---

## Project Progression Overview

| Project | Name | Complexity | Time | Hardware | Key Skills |
|---------|------|------------|------|----------|------------|
| 1 | LED Blink | Beginner | 1-2 days | Simulator | Basic I/O, outputs |
| 2 | Push Button Light | Beginner | 2-3 days | Simulator | Digital inputs, logic |
| 3 | Start/Stop Motor | Beginner | 3-5 days | Simulator | Seal-in circuits, interlocks |
| 4 | Traffic Light Sequencer | Early Intermediate | 1 week | Simulator/PLC | Timers, sequencing |
| 5 | Conveyor with Sensors | Early Intermediate | 1 week | PLC + sensors | Real I/O, troubleshooting |
| 6 | Batch Counter | Intermediate | 1 week | PLC + sensors | Counters, process control |
| 7 | Temperature Monitor | Intermediate | 1-2 weeks | PLC + analog | Analog I/O, scaling, alarms |
| 8 | Pneumatic Cylinder Control | Intermediate | 1-2 weeks | PLC + pneumatics | Actuators, state machines, timing |
| 9 | Pilot Watchdog MVP | Medium | 2-4 weeks | Full demo rig | Baseline learning, anomaly detection, visualization |

---

## Beginner Projects (Projects 1-3)
### Goal: Master basic PLC concepts using free simulators

---

### Project 1: LED Blink
**"Hello World" of PLCs**

#### Objectives
- Understand PLC scan cycle
- Learn to write first rung of ladder logic
- Use timer to create blinking pattern

#### Concepts Introduced
- PLC scan cycle
- Output coils
- Timer On-Delay (TON)
- Done bit

#### Hardware
- **Simulator:** Factory IO + free PLC simulator (e.g., OpenPLC, CODESYS soft PLC)
- **Alternative:** Siemens S7-PLCSIM, Allen-Bradley Emulate 5000 (if available)

#### Specifications
- LED output blinks on/off every 1 second
- Use timer preset = 1000ms

#### Sample Program (Pseudo-Ladder)
```
Rung 0: Timer_Blink.DN (NC) → Timer_Blink (TON, 1000ms)
Rung 1: Timer_Blink.DN → LED_Output (OTE)
Rung 2: Timer_Blink.DN → Timer_Blink (RES)
```

#### Success Criteria
- [ ] LED blinks at 1 Hz (on 1 second, off 1 second)
- [ ] You can explain why the LED turns on when timer.DN = TRUE
- [ ] You understand the scan cycle (input scan → program scan → output scan)

#### Time Estimate
1-2 days (includes learning software navigation)

---

### Project 2: Push Button Light
**Adding User Input**

#### Objectives
- Use digital inputs
- Understand normally open (NO) contacts
- Add interlocking logic

#### Concepts Introduced
- Digital inputs
- Normally open (NO) vs normally closed (NC) contacts
- AND logic (series contacts)
- OR logic (parallel contacts)

#### Hardware
- Simulator (Factory IO or equivalent)

#### Specifications
- Push button turns light ON
- Second push button turns light OFF
- If both buttons pressed simultaneously, light stays OFF (safety interlock)

#### Sample Program (Pseudo-Ladder)
```
Rung 0: Button_ON (XIC) && Button_OFF (XIC, NC) → Light (OTE)
```

#### Challenge Variations
1. **Easy:** Add a third button that toggles the light
2. **Medium:** Add a "master enable" switch that must be ON for any button to work
3. **Hard:** Add a timer delay—light turns on 3 seconds after button press

#### Success Criteria
- [ ] Light responds correctly to both buttons
- [ ] Safety interlock works (both buttons → light off)
- [ ] You can draw a truth table for the logic

#### Time Estimate
2-3 days

---

### Project 3: Start/Stop Motor Control
**The Classic 3-Wire Control Circuit**

#### Objectives
- Implement seal-in circuit
- Understand latching logic
- Add stop button with safety priority

#### Concepts Introduced
- Seal-in circuits (self-holding logic)
- 3-wire control (start, stop, seal)
- Safety interlock (stop has priority)

#### Hardware
- Simulator (Factory IO with motor model)

#### Specifications
- Press START → motor runs
- Release START → motor continues running (sealed in)
- Press STOP → motor stops
- STOP button has priority (even if START held)

#### Sample Program (Pseudo-Ladder)
```
Rung 0: (Start_PB (XIC) || Motor_Running (XIC)) && Stop_PB (XIC, NC) → Motor_Running (OTE)
Rung 1: Motor_Running → Motor_Contactor (OTE)
```

#### Challenge Variations
1. **Add run light:** Green LED when motor running
2. **Add fault condition:** E-stop button (NC contact) must be closed for motor to run
3. **Add timer:** Motor auto-stops after 30 seconds of continuous run

#### Success Criteria
- [ ] Motor seals in after START released
- [ ] STOP button immediately stops motor
- [ ] You can explain why the motor auxiliary contact is needed

#### Time Estimate
3-5 days

#### Milestone Achievement
🎉 **You've mastered the fundamentals!** You now understand:
- Basic I/O
- Timers
- Latching logic
- Safety interlocks

**Ready for real hardware?** Time to move to intermediate projects.

---

## Early Intermediate Projects (Projects 4-5)
### Goal: Add complexity with timers and sequences

---

### Project 4: Traffic Light Sequencer
**Multi-Step State Machine**

#### Objectives
- Create multi-step sequence
- Use multiple timers
- Transition between states

#### Concepts Introduced
- State machines
- Cascading timers
- Sequencing logic

#### Hardware
- **Simulator:** Factory IO (traffic intersection scene)
- **Real PLC:** Click PLC or S7-1200 (optional but recommended)

#### Specifications
- **Green:** 10 seconds
- **Yellow:** 3 seconds
- **Red:** 10 seconds
- **Repeat** continuously

#### Sample Program (Pseudo-Ladder)
```
State 0 (GREEN):
  Rung 0: State = 0 → Green_Light (OTE)
  Rung 1: State = 0 && Timer_Green.DN (NC) → Timer_Green (TON, 10000ms)
  Rung 2: State = 0 && Timer_Green.DN → MOV 1 to State
  Rung 3: State != 0 → Timer_Green (RES)

State 1 (YELLOW):
  Rung 4: State = 1 → Yellow_Light (OTE)
  Rung 5: State = 1 && Timer_Yellow.DN (NC) → Timer_Yellow (TON, 3000ms)
  Rung 6: State = 1 && Timer_Yellow.DN → MOV 2 to State
  Rung 7: State != 1 → Timer_Yellow (RES)

State 2 (RED):
  Rung 8: State = 2 → Red_Light (OTE)
  Rung 9: State = 2 && Timer_Red.DN (NC) → Timer_Red (TON, 10000ms)
  Rung 10: State = 2 && Timer_Red.DN → MOV 0 to State
  Rung 11: State != 2 → Timer_Red (RES)
```

#### Challenge Variations
1. **Add pedestrian button:** Press button → cycle to red within 5 seconds
2. **Add night mode:** After 10 PM, flash red only
3. **Add two-way intersection:** Coordinate two traffic lights (one green → other red)

#### Success Criteria
- [ ] Traffic light cycles correctly (green → yellow → red → repeat)
- [ ] Timing is accurate (no overlaps, no gaps)
- [ ] You can draw a state diagram

#### Time Estimate
1 week

---

### Project 5: Conveyor with Sensors
**First Real Hardware Project**

#### Objectives
- Wire real sensors to PLC
- Handle sensor debouncing
- Log cycle counts

#### Concepts Introduced
- Real digital I/O wiring
- Sensor types (photoelectric, inductive)
- Sinking vs sourcing I/O
- Counter (CTU)

#### Hardware
**Required:**
- PLC (Click, S7-1200, or CompactLogix)
- 24V power supply
- Photoelectric sensor (retroreflective or through-beam)
- Small conveyor or rotating disk (to simulate parts)

**Optional:**
- Second sensor for part counting

**Budget:** ~$200-250 total

#### Specifications
- Conveyor runs continuously
- Photoelectric sensor detects parts passing
- Counter increments for each part
- Display count on HMI or PLC indicator
- Reset button clears count

#### Wiring Diagram (Conceptual)
```
24V Power Supply:
  (+) → Sensor Vcc
  (+) → PLC Input Common (depending on sinking/sourcing)
  (GND) → PLC Ground

Sensor Output → PLC Digital Input (e.g., I:0/0)
Reset Button → PLC Digital Input (e.g., I:0/1)
Conveyor Motor Contactor ← PLC Digital Output (e.g., O:0/0)
```

#### Sample Program (Pseudo-Ladder)
```
Rung 0: Start_Button (XIC) → Conveyor_Running (OTE, seal-in logic)
Rung 1: Part_Sensor (XIC, one-shot) → Part_Counter (CTU)
Rung 2: Reset_Button (XIC) → Part_Counter (RES)
Rung 3: Part_Counter.ACC → Display (move to HMI tag)
```

#### Challenge Variations
1. **Add batch control:** Stop conveyor after 10 parts counted
2. **Add reject logic:** If sensor blocked for >2 seconds, trigger alarm (jam detected)
3. **Add second sensor:** Measure time between sensors to calculate part speed

#### Success Criteria
- [ ] Sensor detects parts reliably (no false triggers)
- [ ] Counter increments correctly
- [ ] You understand sinking vs sourcing wiring
- [ ] You can troubleshoot a sensor not reading

#### Time Estimate
1 week (includes hardware assembly and troubleshooting)

#### Milestone Achievement
🎉 **First real hardware project complete!** You've now:
- Wired real sensors
- Debugged physical I/O issues
- Built a functional system

---

## Intermediate Projects (Projects 6-8)
### Goal: Add analog I/O, state machines, and real actuators

---

### Project 6: Batch Counter System
**Process Control with Multi-Step Logic**

#### Objectives
- Implement batch control logic
- Use counters and comparisons
- Add alarm conditions

#### Concepts Introduced
- Comparison instructions (GRT, LES, EQU)
- Alarm logic
- Batch process control

#### Hardware
- PLC + sensors from Project 5
- Add: Stack light (red/yellow/green) or indicator LEDs

#### Specifications
- Operator sets batch size (e.g., 50 parts) via HMI or thumbwheel
- Conveyor runs until count reaches batch size
- Yellow light: conveyor running
- Green light: batch complete
- Red light: fault condition (sensor blocked >5 seconds)

#### Sample Program (Pseudo-Ladder)
```
Rung 0: Start_Button && (Part_Counter.ACC < Batch_Setpoint) → Conveyor_Running (OTE)
Rung 1: Part_Counter.ACC >= Batch_Setpoint → Batch_Complete (OTE)
Rung 2: Batch_Complete → Green_Light (OTE)
Rung 3: Conveyor_Running → Yellow_Light (OTE)
Rung 4: Sensor_Blocked_Timer.DN → Fault_Alarm (OTE) → Red_Light (OTE)
```

#### Challenge Variations
1. **Add material low warning:** If batch count >80% and supply sensor not triggered, warn operator
2. **Add cycle time tracking:** Measure time to complete batch, display average cycle time
3. **Add recipe management:** Store 3 different batch sizes, operator selects via switches

#### Success Criteria
- [ ] Batch stops at correct count
- [ ] Alarm triggers on fault condition
- [ ] Operator can reset and start new batch

#### Time Estimate
1 week

---

### Project 7: Temperature Monitoring System
**First Analog I/O Project**

#### Objectives
- Wire analog input (4-20mA or 0-10V)
- Scale analog signal to engineering units
- Implement alarm thresholds

#### Concepts Introduced
- Analog I/O
- Scaling (raw counts → engineering units)
- Math instructions (MUL, DIV, ADD)
- Alarm management

#### Hardware
**Required:**
- PLC with analog input module
- Analog temperature sensor (4-20mA output) or simulator (potentiometer)
- Stack light or buzzer for alarm

**Budget:** ~$50-100 for analog module + sensor

#### Specifications
- Read temperature sensor (4-20mA = 0-200°F)
- Display temperature on HMI or PLC indicator
- **Yellow alarm:** Temp >150°F (warning)
- **Red alarm:** Temp >180°F (critical)
- Critical alarm triggers buzzer/red light

#### Scaling Formula
```
Engineering_Value = ((Raw_Input - Raw_Min) / (Raw_Max - Raw_Min)) * (Eng_Max - Eng_Min) + Eng_Min

Example (4-20mA sensor, 12-bit ADC):
  Raw_Min = 4915 (4mA equivalent in counts)
  Raw_Max = 24576 (20mA equivalent)
  Eng_Min = 0°F
  Eng_Max = 200°F

Temperature_F = ((Raw_Input - 4915) / (24576 - 4915)) * 200 + 0
```

#### Sample Program (Pseudo-Ladder)
```
Rung 0: [Scaling logic using MUL, DIV, SUB instructions]
Rung 1: Temperature_F > 150 → Yellow_Alarm (OTE)
Rung 2: Temperature_F > 180 → Red_Alarm (OTE)
Rung 3: Red_Alarm → Buzzer (OTE)
```

#### Challenge Variations
1. **Add hysteresis:** Yellow alarm clears at <145°F (prevents alarm flapping)
2. **Add data logging:** Log temperature every 10 seconds to PLC memory (circular buffer)
3. **Add trending:** Display min/max/average over last hour

#### Success Criteria
- [ ] Temperature displays correctly (accurate scaling)
- [ ] Alarms trigger at correct thresholds
- [ ] You understand how to scale analog signals

#### Time Estimate
1-2 weeks

---

### Project 8: Pneumatic Cylinder Control
**Foundation for Pilot Watchdog**

#### Objectives
- Control pneumatic actuator
- Measure cycle timing
- Detect position with sensors
- Build state machine with timing capture

#### Concepts Introduced
- Pneumatic actuators (solenoid valves)
- Position sensors (reed switches, inductive)
- Cycle timing
- State machine with timeout faults

#### Hardware
**Required:**
- PLC
- Single-acting or double-acting pneumatic cylinder (1-2" bore)
- 2x 3/2 solenoid valves (or 1x 5/2 valve)
- 2x position sensors (extended, retracted)
- Air compressor + pressure regulator
- 24V power supply

**Budget:** ~$150-200 (pneumatics kit from AutomationDirect or McMaster)

#### Specifications
- **Automatic cycle mode:**
  - Press START → cylinder extends
  - Sensor confirms extended → wait 1 second
  - Cylinder retracts
  - Sensor confirms retracted → wait 1 second
  - Repeat
- **Timing capture:** Measure extend time and retract time
- **Fault detection:** If extend time >5 seconds, trigger fault

#### State Machine
```
State 0: IDLE
  → START button pressed → State 1

State 1: EXTENDING
  → Extend solenoid ON
  → If extended sensor TRUE → State 2
  → If time >5 seconds → State 99 (FAULT)

State 2: EXTENDED_DWELL
  → Wait 1 second
  → State 3

State 3: RETRACTING
  → Extend solenoid OFF (retract)
  → If retracted sensor TRUE → State 4
  → If time >5 seconds → State 99 (FAULT)

State 4: RETRACTED_DWELL
  → Wait 1 second
  → If AUTO mode → State 1
  → If STOP pressed → State 0

State 99: FAULT
  → All outputs OFF
  → Red light ON
  → Wait for manual reset
```

#### Sample Program (Pseudo-Ladder/Structured Text Hybrid)
```
CASE Machine_State OF
  0: // IDLE
    IF Start_Button THEN
      Machine_State := 1;
      Cycle_Start_Time := NOW;
    END_IF;

  1: // EXTENDING
    Extend_Solenoid := TRUE;
    IF Sensor_Extended THEN
      Extend_Time := NOW - Cycle_Start_Time;
      Machine_State := 2;
      Dwell_Timer := NOW;
    ELSIF (NOW - Cycle_Start_Time) > 5000 THEN
      Machine_Fault := TRUE;
      Machine_State := 99;
    END_IF;

  2: // EXTENDED_DWELL
    IF (NOW - Dwell_Timer) > 1000 THEN
      Machine_State := 3;
      Cycle_Start_Time := NOW;
    END_IF;

  3: // RETRACTING
    Extend_Solenoid := FALSE;
    IF Sensor_Retracted THEN
      Retract_Time := NOW - Cycle_Start_Time;
      Machine_State := 4;
      Dwell_Timer := NOW;
    ELSIF (NOW - Cycle_Start_Time) > 5000 THEN
      Machine_Fault := TRUE;
      Machine_State := 99;
    END_IF;

  4: // RETRACTED_DWELL
    IF (NOW - Dwell_Timer) > 1000 THEN
      IF Auto_Mode THEN
        Machine_State := 1;
        Cycle_Start_Time := NOW;
      ELSIF Stop_Button THEN
        Machine_State := 0;
      END_IF;
    END_IF;

  99: // FAULT
    Extend_Solenoid := FALSE;
    Red_Light := TRUE;
    IF Reset_Button THEN
      Machine_Fault := FALSE;
      Machine_State := 0;
    END_IF;
END_CASE;
```

#### Challenge Variations
1. **Add pressure monitoring:** Read pressure transducer, log pressure during extend/retract
2. **Add manual mode:** Operator can jog extend/retract with buttons
3. **Add cycle counter:** Count total cycles, display on HMI

#### Success Criteria
- [ ] Cylinder extends and retracts reliably
- [ ] Timing is captured correctly (extend_time, retract_time)
- [ ] Fault triggers if timeout exceeded
- [ ] You can troubleshoot pneumatic issues (air leaks, sensor misalignment)

#### Time Estimate
1-2 weeks (includes pneumatic setup and tuning)

#### Milestone Achievement
🎉 **You've built a real automation system!** This is the foundation for Pilot Watchdog.

---

## Medium Complexity Project (Project 9)
### Goal: Build the Pilot Watchdog MVP

---

### Project 9: Pilot Watchdog MVP
**Predictive Maintenance for PLCs**

#### Objectives
- Extend Project 8 with watchdog logic
- Learn baseline cycle timing
- Detect drift and anomalies
- Visualize data with Python dashboard

#### Concepts Introduced
- Baseline learning (moving average)
- Anomaly detection (threshold-based)
- Shadow monitoring (Pilot watches PLC)
- External data logging (Python + SQLite)
- Web dashboard (Flask + Chart.js)

#### Hardware
**Same as Project 8, plus:**
- Laptop/desktop for data logging
- Ethernet connection between PLC and laptop
- Optional: pressure transducer (0-100 psi, 4-20mA) for analog monitoring

#### Architecture Overview
```
PLC Base Program:
  ├── Machine state machine (from Project 8)
  ├── Cycle timing capture (extend_time, retract_time)
  └── Fault detection (5-second timeout)

Pilot Watchdog Logic (runs in PLC):
  ├── Baseline learning (first 10 cycles)
  ├── Drift detection (timing > baseline + margin)
  ├── Disagreement detection (Pilot warns, PLC OK)
  └── Stack light control (green/yellow/red)

External Logger (Python on laptop):
  ├── Reads PLC tags via Modbus/Ethernet IP
  ├── Logs to SQLite database
  └── Serves web dashboard (Flask)

Web Dashboard:
  ├── Real-time chart (extend_time, retract_time)
  ├── Baseline overlay (show normal range)
  ├── Warning indicators (Pilot yellow)
  └── Fault history
```

#### Pilot Watchdog Logic (Pseudo-Code)
```
TASK Pilot_Watch (runs every 100ms):

VAR
  pilot_baseline_extend: DINT := 1000;  // ms, initial guess
  pilot_baseline_retract: DINT := 1000;
  pilot_margin: DINT := 200;  // tolerance
  pilot_confidence: INT := 0;  // 0-100, cycles seen
  pilot_warn_slow_extend: BOOL := FALSE;
  pilot_warn_slow_retract: BOOL := FALSE;
  pilot_disagree: BOOL := FALSE;
END_VAR

// Detect new cycle completion
IF cycle_count > last_cycle_count_seen THEN
  last_cycle_count_seen := cycle_count;

  // Update baseline if no faults (exponential moving average)
  IF pilot_confidence < 100 AND NOT machine_fault THEN
    pilot_baseline_extend := (pilot_baseline_extend * 9 + extend_time) / 10;
    pilot_baseline_retract := (pilot_baseline_retract * 9 + retract_time) / 10;
    pilot_confidence := MIN(100, pilot_confidence + 1);
  END_IF;

  // Check for drift
  pilot_warn_slow_extend := (extend_time > pilot_baseline_extend + pilot_margin);
  pilot_warn_slow_retract := (retract_time > pilot_baseline_retract + pilot_margin);

  // Disagreement: PLC OK but Pilot warns
  pilot_disagree := (NOT machine_fault) AND (pilot_warn_slow_extend OR pilot_warn_slow_retract);

END_IF;

// Stack light control
stack_light_green := (NOT machine_fault) AND (NOT pilot_disagree);
stack_light_yellow := (NOT machine_fault) AND pilot_disagree;
stack_light_red := machine_fault;
```

#### Python Data Logger (Basic Example)
```python
import sqlite3
import time
from datetime import datetime

# Connect to PLC (example using pymodbus)
# Adjust for your PLC type (Modbus TCP, Ethernet/IP, etc.)

conn = sqlite3.connect('pilot_data.db')
c = conn.cursor()

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

last_cycle_id = -1
while True:
    # Read PLC tags
    cycle_id = read_plc_tag('cycle_count')
    extend_time = read_plc_tag('extend_time')
    retract_time = read_plc_tag('retract_time')
    machine_fault = read_plc_tag('machine_fault')
    pilot_ok = read_plc_tag('pilot_ok')
    pilot_warning = read_plc_tag('pilot_warning')

    # Log new cycles
    if cycle_id > last_cycle_id:
        last_cycle_id = cycle_id
        c.execute('''INSERT INTO cycles
                     (timestamp, cycle_id, extend_time, retract_time,
                      machine_fault, pilot_ok, pilot_warning)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.now().isoformat(), cycle_id, extend_time,
                   retract_time, machine_fault, pilot_ok, pilot_warning))
        conn.commit()
        print(f"Cycle {cycle_id}: extend={extend_time}ms, retract={retract_time}ms, pilot_ok={pilot_ok}")

    time.sleep(1)
```

#### Flask Dashboard (Basic Example)
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
                                backgroundColor: 'rgba(255, 0, 0, 0.1)',
                                fill: true
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

#### Demo Scenarios

**Scenario 1: Baseline Learning**
1. Start system, let it run 10-20 cycles
2. Watch baseline settle in dashboard
3. Stack light: GREEN (Pilot and PLC agree, all normal)

**Scenario 2: Induced Degradation (The Money Shot)**
1. During operation, partially restrict air supply to cylinder
2. Extend time drifts from 1000ms → 1300ms → 1500ms
3. **Key moment:** Stack light turns YELLOW (Pilot warning)
4. **But:** PLC still shows GREEN (no fault, still within 5-second timeout)
5. Dashboard shows warning region (yellow background)
6. **Narration:** "Pilot detected degradation 20 cycles ago. PLC has no idea."

**Scenario 3: Push to Failure**
1. Restrict air supply further
2. Extend time exceeds 5000ms
3. PLC timeout fires → Stack light turns RED (PLC fault)
4. Dashboard shows red region
5. **Narration:** "PLC finally faulted, but Pilot was warning the whole time."

#### Video Content (30-Second TikTok/Reel)
```
[0-5s]   Normal operation, green lights, dashboard stable
[5-10s]  Restrict air (show hand turning valve)
[10-15s] Lights turn YELLOW (Pilot warning), PLC still GREEN
[15-20s] Dashboard shows timing drift, warning region
[20-25s] Restrict more, lights turn RED (PLC fault)
[25-30s] Text overlay: "The AI that knows your machine is sick before it does."
```

#### Challenge Variations
1. **Add pressure monitoring:** Correlate pressure drop with timing drift
2. **Add multiple machines:** Monitor 3 cylinders, compare baselines
3. **Add cloud logging:** Send data to AWS/Azure for long-term trending
4. **Add SMS alerts:** Text operator when Pilot warning triggers

#### Success Criteria
- [ ] Pilot learns baseline in first 10-20 cycles
- [ ] Pilot detects drift before PLC fault
- [ ] Dashboard visualizes timing and warnings
- [ ] You can demonstrate "money shot" video (yellow before red)
- [ ] You can explain to a non-technical person why this matters

#### Time Estimate
2-4 weeks (includes PLC logic, Python logger, dashboard, and demo)

#### Business Validation
- [ ] Create 30-second demo video (target: 10K+ views)
- [ ] Create long-form YouTube demo (5-10 minutes)
- [ ] Document case study (pilot_mvp_case_study.md)
- [ ] Identify first customer (local manufacturer, ride operator)

#### Milestone Achievement
🎉🎉🎉 **PILOT WATCHDOG MVP COMPLETE!** 🎉🎉🎉

You've built a production-ready predictive maintenance system. This is a **medium-complexity industrial automation project** that validates:
- Multi-agent orchestration (PLC + Pilot + Logger + Dashboard)
- Real-world anomaly detection
- Data-driven decision making
- Commercial viability (demo-ready for customers)

**Next Steps:**
1. Deploy on customer site (2-week free pilot)
2. Capture real-world fault (case study)
3. Convert to first paying customer ($50-100/mo)
4. Scale to multiple machines
5. Integrate with Agent Factory (MachineHealthAtom schema)

---

## Skills Matrix

| Skill | Proj 1 | Proj 2 | Proj 3 | Proj 4 | Proj 5 | Proj 6 | Proj 7 | Proj 8 | Proj 9 |
|-------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| Basic I/O | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Timers | ✅ | | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Counters | | | | | ✅ | ✅ | | ✅ | ✅ |
| Seal-in Logic | | | ✅ | | ✅ | ✅ | ✅ | ✅ | ✅ |
| Interlocks | | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| State Machines | | | | ✅ | | ✅ | | ✅ | ✅ |
| Analog I/O | | | | | | | ✅ | ✅ | ✅ |
| Math/Scaling | | | | | | | ✅ | ✅ | ✅ |
| Alarms | | | | | ✅ | ✅ | ✅ | ✅ | ✅ |
| Real Sensors | | | | | ✅ | ✅ | ✅ | ✅ | ✅ |
| Actuators | | | ✅ | | ✅ | ✅ | ✅ | ✅ | ✅ |
| Data Logging | | | | | | ✅ | ✅ | ✅ | ✅ |
| External Comms | | | | | | | | | ✅ |
| Anomaly Detection | | | | | | | | | ✅ |
| Visualization | | | | | | | | | ✅ |

---

## Hardware Budget Summary

| Project | Hardware Required | Cumulative Cost |
|---------|-------------------|-----------------|
| 1-3 | Simulator only | $0 |
| 4 | PLC (optional) | $150-200 |
| 5 | PLC + sensor + conveyor | $250-300 |
| 6 | Add stack light | $270-330 |
| 7 | Add analog module + sensor | $320-430 |
| 8 | Add pneumatics kit | $470-630 |
| 9 | Add pressure transducer (optional) | $500-680 |

**Total investment for full progression:** $500-680

**Alternative (budget-conscious):**
- Skip Projects 1-4 (pure simulator) if you already have PLC
- Buy used PLC on eBay ($50-100 for older Click or S7-200)
- Use cheap sensors from AliExpress (~$10 each)
- **Budget path:** ~$250-350 total

---

## Learning Paths

### Path 1: Complete Beginner (12 weeks)
Week 1-2: Projects 1-3 (simulator)
Week 3-4: Project 4 (traffic light)
Week 5-6: Project 5 (conveyor + real hardware)
Week 7-8: Project 6 (batch control)
Week 9-10: Project 7 (analog I/O)
Week 11-12: Project 8 (pneumatics)
**Result:** Ready for Pilot Watchdog MVP

### Path 2: Experienced Technician (6 weeks)
Week 1: Projects 1-4 (review fundamentals, skim through)
Week 2: Project 5 (real hardware)
Week 3: Project 6 (batch control)
Week 4: Project 7 (analog I/O)
Week 5-6: Project 8 (pneumatics, deep dive)
**Result:** Ready for Pilot Watchdog MVP

### Path 3: PLC Programmer (4 weeks)
Week 1: Projects 5-7 (quick build, focus on hardware wiring)
Week 2: Project 8 (pneumatics, state machine practice)
Week 3-4: Project 9 (Pilot Watchdog MVP)
**Result:** Production-ready demo system

---

## Success Metrics

### Technical Milestones
- [ ] Complete all 9 projects
- [ ] Build working Pilot Watchdog demo rig
- [ ] Capture "money shot" video (Pilot warns before PLC faults)
- [ ] Python dashboard showing real-time data

### Business Milestones
- [ ] Demo video gets 10K+ views (TikTok/YouTube/LinkedIn)
- [ ] 5+ sales inquiries from video
- [ ] 1st customer pilot program deployed (free 2-week trial)
- [ ] 1st paying customer secured ($50-100/mo)

### Learning Outcomes
- [ ] You can confidently wire sensors and actuators
- [ ] You can write state machines in ladder logic or structured text
- [ ] You can scale analog signals and handle alarms
- [ ] You can explain anomaly detection to a non-technical person
- [ ] You can troubleshoot PLC hardware and software issues
- [ ] You're ready for industrial automation technician role

---

## Additional Resources

### Recommended Learning Materials
- **Books:**
  - "Programmable Logic Controllers" by Frank Petruzella
  - "Industrial Automated Systems" by Terry Bartelt
- **YouTube Channels:**
  - PLCs.net
  - RealPars
  - The Automation School
- **Forums:**
  - PLCS.net forum
  - Reddit r/PLC
  - LinkedIn PLC Programmers group

### Software Tools
- **Simulators:** Factory IO, OpenPLC, CODESYS
- **PLC Software:** Studio 5000 (Allen-Bradley), TIA Portal (Siemens)
- **Data Logging:** Python (pymodbus, pandas, sqlite3)
- **Visualization:** Flask, Chart.js, Grafana

### Hardware Suppliers
- **PLCs:** AutomationDirect, Automation24, eBay (used)
- **Sensors:** AutomationDirect, McMaster-Carr, AliExpress (budget)
- **Pneumatics:** AutomationDirect, Surplus Center, McMaster-Carr

---

## Conclusion

This progression takes you from **"What is a PLC?"** to **"I built a production-ready predictive maintenance system"** in 8-12 weeks.

**Key Philosophy:**
- Learn by building, not just reading
- Each project builds on previous skills
- Real hardware matters (simulators only get you so far)
- The final project (Pilot Watchdog) is commercially viable

**What You've Achieved:**
1. ✅ Mastered PLC fundamentals (I/O, timers, counters, logic)
2. ✅ Built real automation systems (sensors, actuators, state machines)
3. ✅ Added intelligence (baseline learning, anomaly detection)
4. ✅ Created business value (demo-ready system for customers)

**Next Steps After Project 9:**
1. Deploy on customer site (real-world validation)
2. Integrate with Agent Factory (MachineHealthAtom schema)
3. Scale to multiple machines (multi-line monitoring)
4. Add advanced features (pressure correlation, cloud logging, SMS alerts)
5. Convert to full-time revenue stream ($500-1K MRR → $1-3M ARR)

---

**You're ready. Go build it.** 🚀
