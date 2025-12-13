# Pilot Watchdog Implementation Outline

**Program:** PLC Pilot Watchdog MVP
**Timeline:** 12 weeks (4-8 weeks for demo rig, +4 weeks for first customer)
**Investment:** $300-500 hardware + 80-100 hours engineering
**Target:** Predictive maintenance for PLCs that detects machine degradation before PLC faults

---

## Executive Summary

Build a scrappy, self-contained demo rig that proves the Pilot Watchdog concept: an AI system that learns normal PLC cycle patterns and flags drift/degradation BEFORE the PLC faults. This validates the third vertical for Agent Factory and creates a viral demo for YouTube/TikTok.

**Value Proposition:** "The AI that knows your machine is sick before it does."

---

## Strategic Positioning

### Third Vertical for Agent Factory

```
Agent Factory Platform
├── RIVET (Vertical 1): Industrial maintenance troubleshooting
├── PLC Tutor (Vertical 2): PLC programming education
└── Pilot Watchdog (Vertical 3): Predictive maintenance ← NEW
```

**Why This Matters:**
- Validates Agent Factory as true multi-vertical platform
- Different GTM strategy (demo-driven vs community-driven vs education-driven)
- Cross-selling opportunity (technicians need all three)
- Defensible moat: Once you have baseline data from hundreds of machines, impossible to replicate

---

## Implementation Phases

### Phase 1: Hardware Assembly (Week 1)
**Goal:** Working demo rig with PLC, pneumatic cylinder, sensors

#### Bill of Materials (~$300-500)

**Control & Compute:**
- Click PLC (AutomationDirect) or Siemens S7-1200: $150-200
- Laptop/desktop for data logging: Existing hardware
- Network switch or direct Ethernet: $20-30

**Hardware Rig:**
- Single-acting pneumatic cylinder (1-2" bore): $40-60
- Two 3/2 solenoid valves: $40-60
- Pressure regulator + gauge: $30-40
- Air compressor: Existing or $100-150
- Quick-disconnect fittings, hose: $20-30

**Sensors:**
- Two reed switches or inductive sensors: $30-50
- Optional: Pressure transducer (0-100 psi): $30-50

**Power & Accessories:**
- 24V power supply: $30-50
- RGB stack light (red/yellow/green): $20-30
- DIN rail, terminal blocks, wire: $30-50

**Total:** $300-500

#### Assembly Tasks
- [ ] Mount components on plywood/aluminum frame (2ft x 2ft)
- [ ] Wire 24V power to PLC, solenoids, sensors
- [ ] Test basic I/O (extend, retract, sensor readings)
- [ ] Document wiring diagram

**Deliverable:** Functional pneumatic rig responding to PLC commands

---

### Phase 2: PLC Base Program (Week 1-2)
**Goal:** PLC running repeatable cycles with data logging

#### Core State Machine

```
States:
0. IDLE - Waiting for start command
1. EXTEND - Command cylinder to extend, wait for sensor
2. RETRACT - Command cylinder to retract, wait for sensor
3. DWELL - Optional pause between cycles
99. FAULT - Timeout or safety fault

Cycle Logic:
- Start → Extend → Wait for extended sensor (timeout 5s)
- Extended → Retract → Wait for retracted sensor (timeout 5s)
- Retracted → Dwell → Back to IDLE
- Any timeout → FAULT state
```

#### Data Logging Structure

```
Cycle_Record:
  - cycle_id (INT)
  - timestamp (TIME)
  - extend_time (DINT, milliseconds)
  - retract_time (DINT, milliseconds)
  - sensor_extended (BOOL)
  - sensor_retracted (BOOL)
  - machine_fault (BOOL)
```

#### Implementation Tasks
- [ ] Create PLC state machine (structured text or ladder)
- [ ] Add timing capture for extend/retract phases
- [ ] Implement 1000-element circular buffer for cycle history
- [ ] Add basic fault detection (5s timeouts)
- [ ] Wire stack light outputs (green=OK, red=FAULT)

**Deliverable:** PLC running 50+ cycles autonomously with logged timing data

---

### Phase 3: Pilot Watchdog Logic (Week 2)
**Goal:** Pilot learns baseline and detects drift BEFORE PLC faults

#### Pilot State Machine

```python
Pilot Logic (runs every 100ms):

1. Learning Phase (cycles 1-10):
   - Calculate rolling average of extend_time and retract_time
   - Build baseline with 10% tolerance margin
   - Increment confidence score (0-100)

2. Monitoring Phase (cycles 11+):
   - Compare latest cycle to baseline + margin
   - Flag if extend_time > baseline + margin
   - Flag if retract_time > baseline + margin

3. Disagreement Detection:
   - pilot_disagree = (PLC says OK) AND (Pilot detects drift)
   - Increment warning_cycle_count if disagree
   - Reset warning_cycle_count if agree

4. Stack Light Control:
   - GREEN: Both PLC and Pilot agree (all normal)
   - YELLOW: Pilot warning but PLC OK (degradation detected)
   - RED: PLC fault (too late)
```

#### Implementation Tasks
- [ ] Create separate Pilot task in PLC (100ms interval)
- [ ] Implement baseline learning algorithm
- [ ] Add drift detection with configurable margin (default 200ms)
- [ ] Create pilot_ok, pilot_warning, pilot_disagree output bits
- [ ] Update stack light logic for three-state indication

**Deliverable:** System that learns normal timing in 10 cycles and flags drift

---

### Phase 4: External Logging & Visualization (Week 2-3)
**Goal:** Python dashboard showing real-time cycle data and Pilot warnings

#### Python Logger (reads PLC via Modbus/Ethernet)

```python
Components:
- SQLite database (pilot_data.db)
- Modbus/socket reader (polls PLC every 1 second)
- Cycle detection (log new cycles only)
- Fields: timestamp, cycle_id, extend_time, retract_time,
         machine_fault, pilot_ok, pilot_warning
```

#### Web Dashboard (Flask + Chart.js)

```html
Features:
- Real-time line chart (extend/retract times over last 100 cycles)
- Warning indicator overlay (yellow background when pilot_warning=true)
- Fault indicator overlay (red background when machine_fault=true)
- Live stats: cycle count, baseline times, current drift
```

#### Implementation Tasks
- [ ] Create Python logger script (pymodbus or socket)
- [ ] Set up SQLite database schema
- [ ] Implement cycle detection and logging
- [ ] Create Flask web app with real-time chart
- [ ] Add Chart.js visualization with warning overlays
- [ ] Test end-to-end: PLC → Logger → Dashboard

**Deliverable:** Live dashboard showing PLC cycles with Pilot warnings visible

---

### Phase 5: Demo Scenarios & Video Content (Week 3-4)
**Goal:** Compelling 30-second video showing Pilot detecting failure before PLC

#### Demo Sequence

**Scene 1: Baseline (15 seconds)**
- Rig running normally
- Stack light: GREEN
- Dashboard: Flat timing lines around 1000ms
- Text: "Machine running normally - Pilot and PLC agree"

**Scene 2: Induced Degradation (30 seconds)**
- Slowly close air valve (restrict flow)
- Stack light: GREEN → YELLOW (Pilot warning)
- PLC: Still GREEN (no fault yet)
- Dashboard: Extend time trending upward (1000ms → 1500ms)
- Text: "Pilot detected degradation - PLC has no idea"

**Scene 3: PLC Fault (15 seconds)**
- Close air valve further
- Extend time exceeds 5s timeout
- Stack light: RED (PLC fault)
- Dashboard: Red spike
- Text: "PLC finally faults - but Pilot warned 20 cycles ago"

#### Content Creation Tasks
- [ ] Run 100 baseline cycles, capture video
- [ ] Induce slow failure, capture warning phase
- [ ] Push to fault, capture fault state
- [ ] Edit 30-second short-form video
- [ ] Create 5-10 minute long-form explanation
- [ ] Prepare social media assets (screenshots, clips)

**Deliverables:**
- 30-second TikTok/Instagram Reel
- 5-10 minute YouTube demo
- Dashboard screenshots showing three phases

---

### Phase 6: Agent Factory Integration (Week 4-6)
**Goal:** Integrate Pilot Watchdog into Agent Factory as third vertical

#### Knowledge Atom Schema Extension

```python
MachineHealthAtom:
  - atom_id: str  # "pilot:machine-health:cycle-123"
  - atom_type: "machine_health"
  - machine_id: str
  - cycle_id: int
  - timestamp: datetime
  - baseline_extend_time: int
  - baseline_retract_time: int
  - actual_extend_time: int
  - actual_retract_time: int
  - drift_detected: bool
  - drift_magnitude: float  # Percentage over baseline
  - pilot_confidence: int  # 0-100
  - plc_fault: bool
  - early_warning_cycles: int  # How many cycles before PLC fault
```

#### Pilot Data Ingestion Agent

```python
Agent: PilotDataIngestionAgent
Purpose: Read PLC data and publish to knowledge base
Triggers: Every 1 second
Tools:
  - Modbus/Ethernet IP reader
  - SQLite local buffer
  - Supabase publisher
  - Vector embedding generator
Output: Machine health atoms in database
```

#### Pilot Watchdog Agent

```python
Agent: PilotWatchdogAgent
Purpose: Analyze machine health patterns and detect anomalies
Triggers: Per cycle completion
Tools:
  - Baseline learning algorithm
  - Anomaly detection (statistical + ML)
  - Alerting system (email, SMS, webhook)
  - Trend analysis
Output: Warnings, alerts, degradation reports
```

#### Implementation Tasks
- [ ] Design MachineHealthAtom schema (Pydantic model)
- [ ] Extend Supabase schema for machine health data
- [ ] Create PilotDataIngestionAgent skeleton
- [ ] Create PilotWatchdogAgent skeleton
- [ ] Implement baseline learning in agent
- [ ] Implement anomaly detection algorithm
- [ ] Add agent to orchestrator registry
- [ ] Create test fixtures for agent testing

**Deliverable:** Pilot Watchdog agents integrated into Agent Factory

---

### Phase 7: First Customer Pilot (Week 7-12)
**Goal:** Deploy Pilot on real production machine, capture case study

#### Customer Identification

**Target Profile:**
- Local manufacturer or ride operator
- 1-5 machines with repetitive cycles
- Existing unplanned downtime issues
- Willing to beta test for free

**Pitch:**
"We'll monitor one of your machines for 2 weeks, completely free. You'll get:
- Real-time health monitoring dashboard
- Early warning system for degradation
- Report on what we found
- No hardware changes needed (just network connection to PLC)"

#### Deployment Process

**Week 1: Installation**
- [ ] Site visit: Identify target machine
- [ ] Network setup: Connect to PLC (Modbus/Ethernet IP)
- [ ] Baseline capture: 2-3 days normal operation
- [ ] Dashboard access: Provide customer login

**Week 2: Monitoring**
- [ ] Daily check-ins: Review dashboard with customer
- [ ] Anomaly investigation: When Pilot flags issues
- [ ] Data collection: Capture customer feedback
- [ ] Documentation: Screenshot warnings and outcomes

**Week 3: Case Study**
- [ ] Analysis: Calculate early warning time (hours or days)
- [ ] ROI calculation: Estimated downtime prevented
- [ ] Write case study (1-2 pages)
- [ ] Customer testimonial (video or quote)

#### Success Metrics
- **Technical:** Pilot detects ≥1 issue before PLC fault
- **Business:** Customer agrees to paid subscription ($50-100/mo)
- **Marketing:** Case study published on LinkedIn/website
- **Learning:** Identify 3-5 product improvements needed

**Deliverable:**
- Published case study: "How Pilot saved [Customer] X hours of downtime"
- First paying customer agreement
- Validated product-market fit for Pilot Watchdog

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Factory                        │
│  ┌────────────────────────────────────────────────┐    │
│  │   Orchestrator                                  │    │
│  │   ├── RIVET (Maintenance)                      │    │
│  │   ├── PLC Tutor (Education)                    │    │
│  │   └── Pilot Watchdog (Predictive Maintenance) │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Supabase + pgvector                        │
│  ┌────────────┬─────────────┬─────────────────────┐    │
│  │ RIVET      │ PLC Tutor   │ Pilot Watchdog      │    │
│  │ Atoms      │ Atoms       │ Machine Health      │    │
│  │            │             │ Atoms               │    │
│  └────────────┴─────────────┴─────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              PLC + Machine (Production)                 │
│  ┌───────────────┐    ┌────────────────────────┐       │
│  │   PLC         │───▶│  Python Logger         │       │
│  │   - Base      │    │  - Modbus/Ethernet     │       │
│  │     Program   │    │  - SQLite Buffer       │       │
│  │   - Pilot     │    │  - Supabase Publisher  │       │
│  │     Logic     │    └────────────────────────┘       │
│  └───────────────┘                                      │
│         │                                                │
│         ▼                                                │
│  ┌───────────────┐    ┌────────────────────────┐       │
│  │ Stack Light   │    │  Flask Dashboard       │       │
│  │ (RGB Status)  │    │  - Real-time Chart     │       │
│  └───────────────┘    │  - Warning Indicators  │       │
│                       └────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. PLC executes machine cycle
2. PLC logs cycle data (extend_time, retract_time)
3. Python logger reads PLC data (Modbus/Ethernet)
4. Logger writes to SQLite (local buffer)
5. Logger publishes to Supabase (Machine Health Atoms)
6. PilotWatchdogAgent analyzes new atoms
7. Agent detects anomalies, publishes warnings
8. Dashboard displays warnings to operator
9. Pilot FB in PLC controls stack light
10. Case studies feed back to RIVET knowledge base
```

---

## Business Model

### Revenue Streams

**Month 1-3: Free Pilot Program**
- Target: 5-10 beta customers
- Goal: Validate product, capture case studies
- Investment: $300-500 per rig

**Month 4-6: Paid Pilots ($50-100/mo)**
- Single-machine monitoring
- Dashboard access
- Email alerts
- Monthly report

**Month 7-12: Multi-Machine Subscriptions ($500-1,000/mo)**
- 5-20 machines per site
- Advanced analytics
- Predictive maintenance recommendations
- Integration with CMMS systems

**Year 2: Enterprise ($5K-20K/mo)**
- Plant-wide deployment (50+ machines)
- Custom integrations
- White-label options
- Training and support

**Year 3+: DAAS Licensing**
- Machine health data API
- Cross-plant benchmarking
- Robot training data licensing
- Perpetual revenue model

### Target Metrics

**Year 1:**
- 10 paying customers @ $75/mo avg = $9K ARR
- 3 case studies published
- Proof of concept validated

**Year 2:**
- 50 customers @ $500/mo avg = $300K ARR
- 2 enterprise deals @ $10K/mo = $240K ARR
- Total: $540K ARR

**Year 3:**
- 200 customers @ $750/mo avg = $1.8M ARR
- 10 enterprise deals @ $15K/mo = $1.8M ARR
- DAAS licensing = $200K ARR
- Total: $3.8M ARR

### Combined Agent Factory Revenue (3 Verticals)

```
Year 3 Projections:
├── RIVET: $2.5M ARR
├── PLC Tutor: $2.5M ARR
└── Pilot Watchdog: $3.8M ARR
────────────────────────────
Total: $8.8M ARR
```

---

## Risk Mitigation

### Technical Risks

**Risk:** PLC brands have different protocols (Modbus, Ethernet/IP, Profinet)
**Mitigation:** Start with Modbus (universal), expand incrementally

**Risk:** Machine cycles vary too much (no stable baseline)
**Mitigation:** Filter by machine type, only target repetitive processes

**Risk:** False positive warnings (Pilot cries wolf)
**Mitigation:** Configurable sensitivity, learning period tuning

### Business Risks

**Risk:** Market too niche (not enough customers)
**Mitigation:** Pilot is third vertical, not primary revenue driver

**Risk:** Customers don't pay after free trial
**Mitigation:** Demonstrate clear ROI (X hours downtime prevented)

**Risk:** Large competitors (Siemens, Rockwell) build similar tools
**Mitigation:** Move fast, capture data moat, become their data provider

### Operational Risks

**Risk:** Customer site network restrictions
**Mitigation:** Offline mode (local logging), VPN access

**Risk:** Support burden (24/7 monitoring expectations)
**Mitigation:** Start with dashboard-only, no real-time alerts (Year 1)

---

## Success Criteria

### Phase 1-5 (Demo Rig): Complete
- [ ] Working demo rig with Pilot detecting degradation
- [ ] 30-second viral video published (10K+ views target)
- [ ] 5-10 minute YouTube demo (1K+ views target)
- [ ] Dashboard showing three phases (normal, warning, fault)

### Phase 6 (Agent Factory Integration): Complete
- [ ] MachineHealthAtom schema deployed
- [ ] PilotDataIngestionAgent functional
- [ ] PilotWatchdogAgent detecting anomalies
- [ ] Agents registered in orchestrator

### Phase 7 (First Customer): Complete
- [ ] 1+ paying customer secured
- [ ] Case study published
- [ ] Testimonial captured
- [ ] Product improvements identified

### Year 1: Validated
- [ ] 10 paying customers
- [ ] $9K ARR
- [ ] 3 published case studies
- [ ] Product-market fit confirmed

---

## Next Steps (Prioritized)

### Immediate (Week 1)
1. **Order hardware** - Click PLC, pneumatics kit, sensors ($300-500)
2. **Create project directory** - `plc/pilot/` with subdirectories
3. **Write PLC program** - Base state machine with data logging
4. **Assemble rig** - Mount components, wire 24V

### Short-term (Week 2-4)
5. **Add Pilot logic to PLC** - Baseline learning, drift detection
6. **Create Python logger** - Modbus reader, SQLite buffer
7. **Build dashboard** - Flask + Chart.js visualization
8. **Capture demo video** - 30-second and long-form versions

### Medium-term (Week 5-8)
9. **Design Agent Factory integration** - MachineHealthAtom schema
10. **Create Pilot agents** - Data ingestion + watchdog agents
11. **Deploy to Supabase** - Schema extension, initial deployment
12. **Test end-to-end** - Demo rig → Agents → Dashboard

### Long-term (Week 9-12)
13. **Identify first customer** - Local manufacturer outreach
14. **Deploy on-site** - Install, baseline capture, monitoring
15. **Capture case study** - Document results, ROI calculation
16. **Publish content** - Case study, testimonial, LinkedIn posts

---

## Supporting Documentation

### To Be Created
- [ ] `plc/pilot/PILOT_WATCHDOG_MVP.md` - Hardware blueprint (detailed BOM, wiring)
- [ ] `plc/pilot/PLC_CODE.md` - PLC program documentation (state machine, Pilot logic)
- [ ] `plc/pilot/PYTHON_LOGGER.md` - Logger implementation guide
- [ ] `plc/pilot/DASHBOARD.md` - Dashboard setup and customization
- [ ] `plc/pilot/AGENT_SPECS.md` - Agent specifications and interfaces
- [ ] `plc/pilot/CUSTOMER_PITCH.md` - Sales deck for first customers
- [ ] `plc/pilot/CASE_STUDY_TEMPLATE.md` - Template for documenting wins

### Referenced Documents
- `claude.md` - Agent Factory execution rules and patterns
- `plc/README.md` - PLC Tutor vertical overview
- `docs/architecture/TRIUNE_STRATEGY.md` - Multi-vertical strategy
- `docs/architecture/AGENT_ORGANIZATION.md` - 18-agent system specs
- `docs/architecture/ATOM_SPEC_UNIVERSAL.md` - Universal Knowledge Atom schema

---

## Conclusion

Pilot Watchdog represents a **strategically critical third vertical** for Agent Factory. It:

1. **Validates the platform** - Proves Knowledge Atom Standard works across domains
2. **Demonstrates technical depth** - Physical hardware + PLC code + AI agents
3. **Creates viral content** - Compelling demo drives brand awareness
4. **Enables robot licensing** - Machine health data becomes training data (Year 5+)
5. **De-risks the business** - Not dependent on RIVET or PLC Tutor alone

**The 12-week timeline is aggressive but achievable:**
- Weeks 1-4: Demo rig and viral video
- Weeks 5-8: Agent Factory integration
- Weeks 9-12: First paying customer

**If successful, Year 3 revenue potential is $3.8M ARR**, contributing to **$8.8M combined ARR** across all three verticals.

**The data moat is the key:** Once you have baseline patterns from hundreds of machines across dozens of customers, competitors can't replicate that knowledge base. The machine health atoms become as valuable as RIVET maintenance atoms and PLC Tutor programming atoms.

---

**Go build it.**
