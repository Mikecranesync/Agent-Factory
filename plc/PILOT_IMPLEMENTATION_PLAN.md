# Pilot Watchdog Implementation Plan
## Agent Factory Integration Strategy

---

## Overview

This document outlines the implementation plan for integrating the Pilot Watchdog MVP into the Agent Factory ecosystem. The Pilot Watchdog is a predictive maintenance system for PLCs that learns normal machine cycles and detects degradation before faults occur.

**Reference Document**: See `plc/PILOT_WATCHDOG_MVP.md` for the complete hardware and demo rig specifications.

---

## Strategic Alignment

### How Pilot Fits into Agent Factory

The Pilot Watchdog represents a **third vertical** alongside RIVET (Industrial Maintenance) and PLC Tutor (PLC Programming Education):

```
Agent Factory (Core Platform)
    ↓
Knowledge Atom Standard
    ├── Industrial Maintenance Atoms (RIVET)
    ├── PLC Programming Atoms (PLC Tutor)
    └── Machine Health Atoms (Pilot Watchdog) ← NEW
    ↓
Multi-Vertical Products
    ├── RIVET ($2.5M ARR target)
    ├── PLC Tutor ($2.5M ARR target)
    └── Pilot Watchdog ($1-3M ARR target) ← NEW
```

### Value Proposition

1. **Validates Multi-Vertical Platform**: Proves Agent Factory works across industrial automation domains
2. **Faster ROI**: Hardware + software = immediate B2B sales opportunity
3. **Data Moat**: Real-world machine data from customer installations
4. **Cross-Selling**: Pilot customers need PLC programming (PLC Tutor) and maintenance help (RIVET)
5. **Agent Training Data**: Machine behavior patterns train autonomous industrial agents

---

## Phase 1: Knowledge Atom Schema Design (Week 1)

### Objective
Define the "Machine Health Atom" schema for storing PLC cycle data, baseline patterns, and anomaly detections.

### Tasks

#### 1.1 Create Pydantic Models
**Location**: `core/models.py`

Add new atom types:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CycleRecord(BaseModel):
    """Individual machine cycle data"""
    cycle_id: int
    timestamp: datetime
    extend_time_ms: int
    retract_time_ms: int
    sensor_states: dict  # {sensor_name: bool}
    analog_values: Optional[dict] = None  # {tag_name: float}
    machine_fault: bool = False
    pilot_warning: bool = False

class MachineHealthAtom(BaseModel):
    """Knowledge atom for machine health patterns"""
    atom_id: str = Field(..., pattern=r'^pilot:[a-z0-9\-]+$')
    type: str = "machine_health"
    machine_id: str
    plc_type: str  # "siemens", "allen_bradley", "click", etc.
    baseline_extend_ms: int
    baseline_retract_ms: int
    tolerance_ms: int
    confidence_level: int = Field(..., ge=0, le=100)
    cycles_observed: int
    anomalies_detected: int
    last_updated: datetime
    metadata: Optional[dict] = None

class AnomalyAtom(BaseModel):
    """Knowledge atom for detected anomalies"""
    atom_id: str = Field(..., pattern=r'^pilot:anomaly:[a-z0-9\-]+$')
    type: str = "anomaly"
    machine_id: str
    detected_at: datetime
    anomaly_type: str  # "slow_extend", "slow_retract", "sensor_drift", etc.
    severity: str  # "warning", "critical"
    baseline_value: float
    observed_value: float
    deviation_percent: float
    cycles_before_fault: Optional[int] = None
    resolution: Optional[str] = None
```

#### 1.2 Database Schema
**Location**: `docs/database/supabase_complete_schema.sql`

Add tables:

```sql
-- Machine health atoms
CREATE TABLE IF NOT EXISTS machine_health_atoms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    atom_id TEXT UNIQUE NOT NULL,
    machine_id TEXT NOT NULL,
    plc_type TEXT NOT NULL,
    baseline_extend_ms INTEGER NOT NULL,
    baseline_retract_ms INTEGER NOT NULL,
    tolerance_ms INTEGER NOT NULL,
    confidence_level INTEGER CHECK (confidence_level >= 0 AND confidence_level <= 100),
    cycles_observed INTEGER DEFAULT 0,
    anomalies_detected INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cycle records (time-series data)
CREATE TABLE IF NOT EXISTS cycle_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    machine_id TEXT NOT NULL,
    cycle_id INTEGER NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    extend_time_ms INTEGER NOT NULL,
    retract_time_ms INTEGER NOT NULL,
    sensor_states JSONB NOT NULL,
    analog_values JSONB,
    machine_fault BOOLEAN DEFAULT FALSE,
    pilot_warning BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Anomaly records
CREATE TABLE IF NOT EXISTS anomaly_atoms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    atom_id TEXT UNIQUE NOT NULL,
    machine_id TEXT NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL,
    anomaly_type TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('warning', 'critical')),
    baseline_value FLOAT NOT NULL,
    observed_value FLOAT NOT NULL,
    deviation_percent FLOAT NOT NULL,
    cycles_before_fault INTEGER,
    resolution TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_cycle_records_machine_id ON cycle_records(machine_id);
CREATE INDEX idx_cycle_records_timestamp ON cycle_records(timestamp DESC);
CREATE INDEX idx_anomaly_atoms_machine_id ON anomaly_atoms(machine_id);
CREATE INDEX idx_anomaly_atoms_detected_at ON anomaly_atoms(detected_at DESC);
```

#### 1.3 Validation
Run validation commands:

```bash
# Verify models import
poetry run python -c "from core.models import MachineHealthAtom, AnomalyAtom, CycleRecord; print('Models OK')"

# Deploy schema to Neon
poetry run python deploy_schema_to_neon.py
```

**Deliverable**: Pydantic models and database schema committed to main branch.

---

## Phase 2: PLC Data Ingestion Agent (Week 1-2)

### Objective
Build an agent that reads PLC data over Ethernet and stores it as Knowledge Atoms.

### Tasks

#### 2.1 Create PLCDataIngestionAgent
**Location**: `plc/agents/plc_data_ingestion_agent.py`

```python
from typing import Dict, Any
import time
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from agent_factory.core.agent_factory import AgentFactory
from core.models import CycleRecord, MachineHealthAtom

class PLCDataIngestionAgent:
    """Reads PLC data and stores as Knowledge Atoms"""

    def __init__(self, machine_id: str, plc_ip: str, plc_type: str):
        self.machine_id = machine_id
        self.plc_ip = plc_ip
        self.plc_type = plc_type
        self.factory = AgentFactory()
        self.modbus_client = ModbusTcpClient(plc_ip)

    def read_plc_tags(self) -> Dict[str, Any]:
        """Read cycle data from PLC"""
        # Implement Modbus/Ethernet IP reading based on PLC type
        # This is PLC-specific; adjust for your hardware
        tags = {
            'cycle_count': self.read_tag(0),  # Modbus address 0
            'extend_time': self.read_tag(1),
            'retract_time': self.read_tag(2),
            'machine_fault': self.read_tag(3),
            'sensor_extended': self.read_tag(4),
            'sensor_retracted': self.read_tag(5),
        }
        return tags

    def read_tag(self, address: int) -> Any:
        """Read single Modbus register"""
        result = self.modbus_client.read_holding_registers(address, 1)
        return result.registers[0] if not result.isError() else None

    def store_cycle_record(self, tags: Dict[str, Any]):
        """Store cycle data as Knowledge Atom"""
        record = CycleRecord(
            cycle_id=tags['cycle_count'],
            timestamp=datetime.now(),
            extend_time_ms=tags['extend_time'],
            retract_time_ms=tags['retract_time'],
            sensor_states={
                'extended': bool(tags['sensor_extended']),
                'retracted': bool(tags['sensor_retracted']),
            },
            machine_fault=bool(tags['machine_fault']),
            pilot_warning=False,  # Will be set by watchdog agent
        )

        # Store to database via Agent Factory memory system
        self.factory.memory.store_atom(record.dict(), atom_type='cycle_record')

    def run_continuous(self, interval_seconds: int = 1):
        """Continuously poll PLC and store data"""
        last_cycle_id = -1

        while True:
            try:
                tags = self.read_plc_tags()

                # Only log new cycles
                if tags['cycle_count'] > last_cycle_id:
                    self.store_cycle_record(tags)
                    last_cycle_id = tags['cycle_count']
                    print(f"Logged cycle {last_cycle_id}")

                time.sleep(interval_seconds)

            except Exception as e:
                print(f"Error reading PLC: {e}")
                time.sleep(5)  # Back off on error
```

#### 2.2 Configuration File
**Location**: `plc/config/pilot_config.yaml`

```yaml
machines:
  - machine_id: "demo_rig_01"
    plc_ip: "192.168.1.100"
    plc_type: "click"
    poll_interval_sec: 1

  - machine_id: "customer_line_03"
    plc_ip: "10.0.50.23"
    plc_type: "siemens_s7_1200"
    poll_interval_sec: 2

pilot_settings:
  learning_cycles: 20  # Number of cycles to establish baseline
  tolerance_percent: 20  # % deviation before warning
  confidence_threshold: 80  # Minimum confidence before alerting
```

#### 2.3 Run Script
**Location**: `plc/run_pilot_ingestion.py`

```python
import yaml
from plc.agents.plc_data_ingestion_agent import PLCDataIngestionAgent

def main():
    with open('plc/config/pilot_config.yaml') as f:
        config = yaml.safe_load(f)

    # Start ingestion for all configured machines
    for machine in config['machines']:
        agent = PLCDataIngestionAgent(
            machine_id=machine['machine_id'],
            plc_ip=machine['plc_ip'],
            plc_type=machine['plc_type']
        )

        print(f"Starting ingestion for {machine['machine_id']}")
        agent.run_continuous(interval_seconds=machine['poll_interval_sec'])

if __name__ == '__main__':
    main()
```

**Deliverable**: Working PLC data ingestion agent storing cycle records to database.

---

## Phase 3: Pilot Watchdog Agent (Week 2-3)

### Objective
Build an agent that analyzes cycle patterns, learns baselines, and detects anomalies.

### Tasks

#### 3.1 Create PilotWatchdogAgent
**Location**: `plc/agents/pilot_watchdog_agent.py`

```python
from typing import List, Optional
from datetime import datetime, timedelta
from core.models import CycleRecord, MachineHealthAtom, AnomalyAtom
from agent_factory.core.agent_factory import AgentFactory

class PilotWatchdogAgent:
    """Learns machine baselines and detects anomalies"""

    def __init__(self, machine_id: str, config: dict):
        self.machine_id = machine_id
        self.config = config
        self.factory = AgentFactory()
        self.baseline: Optional[MachineHealthAtom] = None

    def load_baseline(self) -> Optional[MachineHealthAtom]:
        """Load existing baseline from database"""
        result = self.factory.memory.query_atoms(
            atom_type='machine_health',
            filters={'machine_id': self.machine_id}
        )
        return result[0] if result else None

    def calculate_baseline(self, cycles: List[CycleRecord]) -> MachineHealthAtom:
        """Calculate baseline from clean cycles"""
        # Filter out faulted cycles
        clean_cycles = [c for c in cycles if not c.machine_fault]

        if len(clean_cycles) < self.config['learning_cycles']:
            raise ValueError(f"Need {self.config['learning_cycles']} clean cycles")

        # Calculate moving average
        avg_extend = sum(c.extend_time_ms for c in clean_cycles) / len(clean_cycles)
        avg_retract = sum(c.retract_time_ms for c in clean_cycles) / len(clean_cycles)

        # Tolerance as percentage of baseline
        tolerance = int(avg_extend * (self.config['tolerance_percent'] / 100))

        baseline = MachineHealthAtom(
            atom_id=f"pilot:{self.machine_id}:baseline",
            machine_id=self.machine_id,
            plc_type="click",  # Get from config
            baseline_extend_ms=int(avg_extend),
            baseline_retract_ms=int(avg_retract),
            tolerance_ms=tolerance,
            confidence_level=100,
            cycles_observed=len(clean_cycles),
            anomalies_detected=0,
            last_updated=datetime.now()
        )

        # Store to database
        self.factory.memory.store_atom(baseline.dict(), atom_type='machine_health')
        return baseline

    def detect_anomaly(self, cycle: CycleRecord) -> Optional[AnomalyAtom]:
        """Check if cycle deviates from baseline"""
        if not self.baseline:
            return None

        # Check extend time
        if cycle.extend_time_ms > (self.baseline.baseline_extend_ms + self.baseline.tolerance_ms):
            deviation = ((cycle.extend_time_ms - self.baseline.baseline_extend_ms) /
                        self.baseline.baseline_extend_ms * 100)

            anomaly = AnomalyAtom(
                atom_id=f"pilot:anomaly:{self.machine_id}:{cycle.cycle_id}",
                machine_id=self.machine_id,
                detected_at=cycle.timestamp,
                anomaly_type="slow_extend",
                severity="warning" if deviation < 50 else "critical",
                baseline_value=float(self.baseline.baseline_extend_ms),
                observed_value=float(cycle.extend_time_ms),
                deviation_percent=deviation
            )

            # Store anomaly
            self.factory.memory.store_atom(anomaly.dict(), atom_type='anomaly')
            print(f"⚠️  ANOMALY DETECTED: {anomaly.anomaly_type} on {self.machine_id}")
            return anomaly

        # Check retract time (similar logic)
        # ...

        return None

    def run_continuous(self, interval_seconds: int = 5):
        """Continuously analyze new cycles"""
        # Load or create baseline
        self.baseline = self.load_baseline()

        if not self.baseline:
            print(f"Learning baseline for {self.machine_id}...")
            # Get last N cycles from database
            recent_cycles = self.factory.memory.query_atoms(
                atom_type='cycle_record',
                filters={'machine_id': self.machine_id},
                limit=self.config['learning_cycles']
            )
            self.baseline = self.calculate_baseline(recent_cycles)
            print(f"✓ Baseline established: {self.baseline.baseline_extend_ms}ms extend")

        # Monitor new cycles
        while True:
            new_cycles = self.get_new_cycles(since=datetime.now() - timedelta(seconds=interval_seconds))

            for cycle in new_cycles:
                self.detect_anomaly(cycle)

            time.sleep(interval_seconds)
```

**Deliverable**: Working anomaly detection agent with configurable baselines.

---

## Phase 4: Visualization Dashboard (Week 3-4)

### Objective
Build a web dashboard showing real-time machine health and anomaly alerts.

### Tasks

#### 4.1 Flask Dashboard
**Location**: `plc/dashboard/pilot_dashboard.py`

```python
from flask import Flask, render_template, jsonify
from agent_factory.core.agent_factory import AgentFactory

app = Flask(__name__)
factory = AgentFactory()

@app.route('/api/machines')
def get_machines():
    """Get all monitored machines"""
    machines = factory.memory.query_atoms(atom_type='machine_health')
    return jsonify([m.dict() for m in machines])

@app.route('/api/machine/<machine_id>/cycles')
def get_cycles(machine_id):
    """Get recent cycles for a machine"""
    cycles = factory.memory.query_atoms(
        atom_type='cycle_record',
        filters={'machine_id': machine_id},
        limit=100
    )
    return jsonify([c.dict() for c in cycles])

@app.route('/api/machine/<machine_id>/anomalies')
def get_anomalies(machine_id):
    """Get anomalies for a machine"""
    anomalies = factory.memory.query_atoms(
        atom_type='anomaly',
        filters={'machine_id': machine_id},
        limit=50
    )
    return jsonify([a.dict() for a in anomalies])

@app.route('/')
def index():
    return render_template('pilot_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

#### 4.2 Frontend Template
**Location**: `plc/dashboard/templates/pilot_dashboard.html`

- Real-time chart showing cycle times (extend/retract)
- Baseline overlay with tolerance bands
- Anomaly alerts with severity indicators
- Machine status indicators (green/yellow/red)

**Deliverable**: Live dashboard accessible at http://localhost:5000

---

## Phase 5: Agent Factory Integration (Week 4)

### Objective
Integrate Pilot agents into the main Agent Factory orchestration system.

### Tasks

#### 5.1 Register Pilot Agents
**Location**: `orchestrator.py`

Add Pilot agents to orchestrator:

```python
# Register Pilot Watchdog agents
for machine in pilot_config['machines']:
    ingestion_agent = PLCDataIngestionAgent(
        machine_id=machine['machine_id'],
        plc_ip=machine['plc_ip'],
        plc_type=machine['plc_type']
    )

    watchdog_agent = PilotWatchdogAgent(
        machine_id=machine['machine_id'],
        config=pilot_config['pilot_settings']
    )

    orchestrator.register(
        f"pilot_ingestion_{machine['machine_id']}",
        ingestion_agent,
        keywords=['plc', 'ingestion', machine['machine_id']]
    )

    orchestrator.register(
        f"pilot_watchdog_{machine['machine_id']}",
        watchdog_agent,
        keywords=['anomaly', 'detection', machine['machine_id']]
    )
```

#### 5.2 Cross-Agent Communication
Enable Pilot to trigger RIVET maintenance alerts:

```python
# When critical anomaly detected
if anomaly.severity == 'critical':
    # Route to RIVET maintenance agent
    orchestrator.route(
        f"Critical anomaly on {machine_id}: {anomaly.anomaly_type}. "
        f"Deviation: {anomaly.deviation_percent:.1f}%. Investigate immediately."
    )
```

**Deliverable**: Pilot agents integrated into main orchestrator, cross-vertical communication working.

---

## Phase 6: Demo Rig & Content Creation (Week 5-8)

### Objective
Build physical demo rig and create marketing content (see `PILOT_WATCHDOG_MVP.md` for details).

### Tasks

1. **Hardware Assembly** (Week 5)
   - Purchase BOM ($300-500)
   - Assemble pneumatic rig
   - Wire PLC and sensors
   - Test basic IO

2. **PLC Programming** (Week 5-6)
   - Implement state machine
   - Add Pilot logic to PLC
   - Test data logging

3. **Video Production** (Week 6-7)
   - Baseline run footage
   - Induced failure demo
   - Dashboard screen recording
   - Edit 30-second short + 5-minute long-form

4. **Content Distribution** (Week 7-8)
   - YouTube upload
   - LinkedIn post
   - TikTok/Instagram clips
   - Sales one-pager PDF

**Deliverable**: YouTube demo video + sales collateral.

---

## Phase 7: First Customer Pilot (Week 9-12)

### Objective
Install Pilot on a real customer machine and document results.

### Tasks

1. **Customer Acquisition**
   - Reach out to local plants
   - Offer free 2-week trial
   - Get access to one production line

2. **Installation**
   - Configure PLC data ingestion
   - Establish baseline over 2-3 days
   - Run in shadow mode (monitoring only)

3. **Documentation**
   - Log all anomalies detected
   - Track if any progressed to faults
   - Calculate "early warning" time (hours/days before fault)

4. **Case Study**
   - Write up results
   - Get customer testimonial
   - Use for future sales

**Deliverable**: Customer case study proving Pilot value in production environment.

---

## Success Metrics

### Technical Metrics
- [ ] Baseline established within 20 cycles
- [ ] Anomaly detection accuracy >90% (true positives)
- [ ] False positive rate <5%
- [ ] Average early warning time: 2+ hours before PLC fault

### Business Metrics
- [ ] Demo video: 10K+ views in first month
- [ ] 3+ customer pilot inquiries
- [ ] 1 paying customer by Month 4
- [ ] $500-1000 MRR by Month 6

### Integration Metrics
- [ ] Pilot agents registered in orchestrator
- [ ] Cross-vertical communication (Pilot → RIVET) working
- [ ] Dashboard accessible and real-time
- [ ] Knowledge atoms stored in unified schema

---

## Risk Mitigation

### Technical Risks

**Risk**: PLC communication protocols vary widely
**Mitigation**: Start with Click PLC (simple Ethernet), document adapter pattern for other brands

**Risk**: Baseline learning may not work for all machine types
**Mitigation**: Start with simple cyclical machines (pneumatics, conveyors), expand later

**Risk**: False positives annoy customers
**Mitigation**: Tune tolerance thresholds per machine, add "snooze" feature

### Business Risks

**Risk**: Hard to access customer PLCs (network security)
**Mitigation**: Offer on-premise deployment option, emphasize no cloud dependency

**Risk**: Customers don't trust AI predictions
**Mitigation**: Run in shadow mode first, show historical data proving predictions

**Risk**: Market too small (PLC predictive maintenance is niche)
**Mitigation**: Pilot is part of broader RIVET ecosystem, not standalone product

---

## Next Steps (After Phase 7)

1. **Multi-Machine Support**: Dashboard shows fleet view (compare machines)
2. **Mobile App**: iOS/Android app for maintenance alerts
3. **Autonomous Remediation**: Auto-adjust PLC parameters when drift detected
4. **OEM Partnerships**: License Pilot to Siemens, AB, Beckhoff
5. **Robot Training Data**: Feed Pilot data into autonomous robot learning pipelines

---

## Conclusion

The Pilot Watchdog MVP validates the Agent Factory platform's ability to handle real-world industrial automation. By integrating PLC data ingestion, anomaly detection, and cross-vertical communication, we demonstrate a complete end-to-end AI system that creates tangible business value.

**Timeline**: 12 weeks from start to first paying customer
**Investment**: $300-500 hardware + ~80 hours engineering time
**Expected ROI**: $500-1000 MRR within 6 months, scales to $1-3M ARR within 3 years

**Status**: Ready to build. Let's go.
