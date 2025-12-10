# Content Roadmap: A-to-Z PLC & Industrial Automation Curriculum

## Overview

This document outlines **100+ video topics** sequenced from absolute basics (voltage, current) through advanced PLC programming and AI-augmented automation.

**Philosophy:** Linear learning paths with spiral curriculum (revisit concepts with increasing complexity).

**Target Audience:**
- Complete beginners (no electrical background)
- Electricians transitioning to PLCs
- Technicians upskilling
- Engineering students

**Content Format:**
- 5-12 minute videos (YouTube long-form)
- 30-60 second clips (TikTok, Instagram, LinkedIn)
- Structured as modules → courses → playlists

---

## Track A: Electrical Fundamentals (Videos 1-20)

### Module 1: Electricity Basics (Videos 1-5)
*Foundation for everyone. No prerequisites.*

**Video 1: What is Electricity? (Industrial Skills Hub #1)**
- **Atom:** `plc:generic:electricity-intro`
- **Topics:** Atoms, electrons, flow of charge
- **Duration:** 5-7 min
- **Keywords:** what is electricity, electricity basics, electrical fundamentals
- **Hook:** "Everything you touch runs on electricity. Let's understand how."
- **Example:** Water analogy (pressure = voltage, flow = current)
- **Quiz:** "What moves when electricity flows?" (Answer: electrons)

**Video 2: Voltage, Current, and Resistance Explained (#2)**
- **Atoms:** `plc:generic:voltage`, `plc:generic:current`, `plc:generic:resistance`
- **Topics:** Definitions, units (V, A, Ω), relationships
- **Duration:** 7-9 min
- **Keywords:** voltage current resistance, electrical terms, volts amps ohms
- **Hook:** "These 3 concepts explain every circuit you'll ever see."
- **Example:** Garden hose analogy (pressure, flow, restriction)
- **Quiz:** "If resistance increases, what happens to current?" (Answer: decreases)

**Video 3: Ohm's Law - The Foundation of Electrical Engineering (#3)**
- **Atom:** `plc:generic:ohms-law`
- **Topics:** V=I×R, calculations, applications
- **Duration:** 8-10 min
- **Keywords:** ohms law, V=IR, electrical calculations, ohms law tutorial
- **Hook:** "This one equation solves 90% of electrical problems."
- **Example:** Calculate voltage drop across a resistor (12V, 2A → R=6Ω)
- **Quiz:** "A 24V circuit with 4Ω resistance. What's the current?" (Answer: 6A)

**Video 4: Electrical Power - Watts, Work, and Energy (#4)**
- **Atom:** `plc:generic:power`
- **Topics:** P=V×I, watts, kilowatts, energy vs power
- **Duration:** 7-9 min
- **Keywords:** electrical power, watts, power calculation, energy vs power
- **Hook:** "Why does your electric bill measure kilowatt-hours?"
- **Example:** Calculate power for a motor (480V, 10A → P=4800W=4.8kW)
- **Quiz:** "Which uses more power: 120V 5A or 240V 2A?" (Answer: Same, 600W each)

**Video 5: AC vs DC - Understanding Alternating and Direct Current (#5)**
- **Atoms:** `plc:generic:ac-current`, `plc:generic:dc-current`
- **Topics:** AC waveform, frequency, DC steady-state, applications
- **Duration:** 9-11 min
- **Keywords:** AC vs DC, alternating current, direct current, AC DC difference
- **Hook:** "Why does your wall outlet use AC, but your phone uses DC?"
- **Example:** 60 Hz AC oscillates 60 times per second (show sine wave)
- **Quiz:** "What's the frequency of US residential AC power?" (Answer: 60 Hz)

---

### Module 2: Electrical Safety & Components (Videos 6-10)
*Practical safety + common industrial components.*

**Video 6: Electrical Safety Fundamentals - Stay Alive on the Job (#6)**
- **Atom:** `plc:generic:electrical-safety`
- **Topics:** Lockout/tagout, PPE, arc flash, grounding
- **Duration:** 10-12 min
- **Keywords:** electrical safety, LOTO, arc flash, electrical hazards
- **Hook:** "[cautionary] This could save your life. Watch carefully."
- **Example:** Proper lockout/tagout procedure (6 steps)
- **Quiz:** "What's the first step in LOTO?" (Answer: Notify affected employees)
- **Safety Level:** DANGER

**Video 7: Sensors - How Machines See the World (#7)**
- **Atom:** `plc:generic:sensors-intro`
- **Topics:** Proximity sensors, photoelectric, limit switches, pressure/temp
- **Duration:** 8-10 min
- **Keywords:** industrial sensors, proximity sensors, photoelectric sensors
- **Hook:** "Without sensors, machines are blind. Here's how they work."
- **Example:** Photoelectric sensor detecting box on conveyor
- **Quiz:** "Which sensor detects metal without contact?" (Answer: Inductive proximity)

**Video 8: Actuators - How Machines Move (#8)**
- **Atom:** `plc:generic:actuators-intro`
- **Topics:** Solenoids, relays, contactors, motor starters
- **Duration:** 8-10 min
- **Keywords:** industrial actuators, solenoids, relays, contactors
- **Hook:** "Sensors detect. Actuators act. Here's how."
- **Example:** Solenoid valve controlling pneumatic cylinder
- **Quiz:** "What device switches high-power circuits?" (Answer: Contactor)

**Video 9: Electric Motors - The Heart of Automation (#9)**
- **Atom:** `plc:generic:motors-intro`
- **Topics:** AC motors, DC motors, VFDs, motor control basics
- **Duration:** 10-12 min
- **Keywords:** electric motors, AC motors, DC motors, VFDs
- **Hook:** "Motors convert electricity into motion. Let's see how."
- **Example:** 3-phase AC induction motor (most common in industry)
- **Quiz:** "What controls motor speed in AC motors?" (Answer: VFD / Variable Frequency Drive)

**Video 10: Relays and Contactors - The Building Blocks of Control (#10)**
- **Atom:** `plc:generic:relays-contactors`
- **Topics:** Relay operation, normally open/closed contacts, contactor sizing
- **Duration:** 9-11 min
- **Keywords:** relays, contactors, relay operation, NO NC contacts
- **Hook:** "Before PLCs, everything ran on relays. Here's why they still matter."
- **Example:** Control relay switching 24VDC signal to activate motor contactor
- **Quiz:** "What's the difference between NO and NC contacts?" (Answer: NO open by default, NC closed)

---

### Module 3: Electrical Circuits & Troubleshooting (Videos 11-15)

**Video 11: Series vs Parallel Circuits - The Two Ways to Connect (#11)**
- **Atoms:** `plc:generic:series-circuits`, `plc:generic:parallel-circuits`
- **Topics:** Series (same current), parallel (same voltage), calculations
- **Duration:** 9-11 min
- **Keywords:** series circuits, parallel circuits, series vs parallel
- **Hook:** "These two patterns explain every circuit you'll ever see."
- **Example:** Christmas lights (series) vs home outlets (parallel)
- **Quiz:** "In a series circuit, what's the same everywhere?" (Answer: Current)

**Video 12: Reading Electrical Schematics - The Language of Circuits (#12)**
- **Atom:** `plc:generic:schematics-reading`
- **Topics:** Symbol library, reading conventions, tracing current paths
- **Duration:** 10-12 min
- **Keywords:** electrical schematics, reading schematics, circuit diagrams
- **Hook:** "Can't read schematics? You're guessing. Let's fix that."
- **Example:** Trace current path in simple motor control circuit
- **Quiz:** "What symbol represents a normally open contact?" (Answer: Two parallel lines, gap)

**Video 13: Multimeter Basics - Your Most Important Tool (#13)**
- **Atom:** `plc:generic:multimeter-basics`
- **Topics:** Measuring voltage, current, resistance, continuity
- **Duration:** 8-10 min
- **Keywords:** multimeter, how to use multimeter, voltage measurement
- **Hook:** "This $20 tool will save you hours of troubleshooting."
- **Example:** Measure voltage across motor terminals (expect 480V, read 0V → blown fuse)
- **Quiz:** "To measure current, how do you connect a multimeter?" (Answer: In series)

**Video 14: Troubleshooting Electrical Circuits - The Systematic Approach (#14)**
- **Atom:** `plc:generic:troubleshooting-circuits`
- **Topics:** Half-split method, voltage tracing, common failures
- **Duration:** 11-13 min
- **Keywords:** troubleshooting electrical circuits, electrical troubleshooting
- **Hook:** "Stop guessing. Here's how pros troubleshoot."
- **Example:** Motor won't start → trace voltage from panel → find blown fuse
- **Quiz:** "What's the fastest way to isolate a fault?" (Answer: Half-split / divide and conquer)

**Video 15: Grounding and Bonding - Why It Matters (#15)**
- **Atom:** `plc:generic:grounding-bonding`
- **Topics:** Safety grounding, equipment grounding, NEC requirements
- **Duration:** 9-11 min
- **Keywords:** electrical grounding, grounding vs bonding, NEC grounding
- **Hook:** "[cautionary] Bad grounding kills. Here's how to do it right."
- **Example:** Proper equipment grounding for motor control panel
- **Quiz:** "What's the purpose of grounding?" (Answer: Safety, fault current path)
- **Safety Level:** WARNING

---

### Module 4: Three-Phase Power & Industrial Systems (Videos 16-20)

**Video 16: Three-Phase Power - Why Industry Uses It (#16)**
- **Atom:** `plc:generic:three-phase-power`
- **Topics:** 3-phase vs single-phase, wye/delta, power calculations
- **Duration:** 11-13 min
- **Keywords:** three phase power, 3 phase, wye delta, industrial power
- **Hook:** "Single-phase is for homes. Three-phase is for industry. Here's why."
- **Example:** 480V 3-phase motor (calculate power: √3 × V × I × PF)
- **Quiz:** "What's the advantage of 3-phase over single-phase?" (Answer: More power, smoother, smaller conductors)

**Video 17: Transformers - Changing Voltage Levels (#17)**
- **Atom:** `plc:generic:transformers`
- **Topics:** Step-up/step-down, turns ratio, control transformers
- **Duration:** 9-11 min
- **Keywords:** transformers, step up transformer, step down transformer
- **Hook:** "How does 480V become 24V for your PLC? Transformers."
- **Example:** 480V to 120V control transformer (4:1 turns ratio)
- **Quiz:** "If primary is 480V and secondary is 120V, what's the turns ratio?" (Answer: 4:1)

**Video 18: Motor Starters - Protecting Your Motors (#18)**
- **Atom:** `plc:generic:motor-starters`
- **Topics:** DOL starters, soft starters, VFDs, overload protection
- **Duration:** 10-12 min
- **Keywords:** motor starters, DOL starter, soft starter, VFD
- **Hook:** "Starting a motor wrong can destroy it. Here's how to do it right."
- **Example:** DOL (Direct-On-Line) starter with thermal overload
- **Quiz:** "What protects motors from overcurrent?" (Answer: Overload relay)

**Video 19: Control Circuits vs Power Circuits - The Two Sides (#19)**
- **Atoms:** `plc:generic:control-circuits`, `plc:generic:power-circuits`
- **Topics:** Low-voltage control (24V), high-voltage power (480V), isolation
- **Duration:** 9-11 min
- **Keywords:** control circuits, power circuits, control vs power
- **Hook:** "Why do we use 24V to control 480V motors? Safety."
- **Example:** 24VDC control circuit energizes 480VAC contactor coil
- **Quiz:** "What's typical control circuit voltage?" (Answer: 24VDC or 120VAC)

**Video 20: Industrial Panel Design - Putting It All Together (#20)**
- **Atom:** `plc:generic:panel-design`
- **Topics:** Panel layout, wire routing, labeling, safety
- **Duration:** 12-15 min
- **Keywords:** electrical panel design, control panel layout, industrial panels
- **Hook:** "A well-designed panel is easy to troubleshoot. A bad one is a nightmare."
- **Example:** Walkthrough of typical motor control panel (disconnect, fuses, contactors, PLC)
- **Quiz:** "Where should disconnect switches be located?" (Answer: Top of panel, easily accessible)

---

## Track B: PLC Fundamentals (Videos 21-40)

### Module 5: PLC Hardware & Basics (Videos 21-25)

**Video 21: What is a PLC? (Programmable Logic Controller Explained) (#21)**
- **Atom:** `plc:generic:what-is-plc`
- **Topics:** PLC history, purpose, vs microcontrollers, applications
- **Duration:** 8-10 min
- **Keywords:** what is a PLC, programmable logic controller, PLC explained
- **Hook:** "Before PLCs, factories used miles of relay wiring. Here's what changed."
- **Example:** PLC controlling conveyor system (inputs: sensors, outputs: motors)
- **Quiz:** "What replaced relay panels in modern factories?" (Answer: PLCs)

**Video 22: PLC Scan Cycle - How PLCs Think (#22)**
- **Atom:** `plc:generic:scan-cycle`
- **Topics:** Input scan, program scan, output scan, cycle time
- **Duration:** 9-11 min
- **Keywords:** PLC scan cycle, scan time, how PLCs work
- **Hook:** "PLCs don't run instantly. They scan. Here's why that matters."
- **Example:** 10ms scan cycle = 100 scans per second
- **Quiz:** "What happens if program execution exceeds scan time?" (Answer: Watchdog fault)

**Video 23: PLC Hardware - CPU, I/O, and Racks (#23)**
- **Atom:** `plc:generic:plc-hardware`
- **Topics:** CPU modules, I/O modules, racks, power supplies, backplanes
- **Duration:** 10-12 min
- **Keywords:** PLC hardware, PLC CPU, PLC I/O modules, PLC racks
- **Hook:** "What's inside a PLC? Let's take it apart."
- **Example:** Allen-Bradley ControlLogix rack (CPU, digital I/O, analog I/O)
- **Quiz:** "What module runs the PLC program?" (Answer: CPU)

**Video 24: Digital I/O - The Foundation of PLC Control (#24)**
- **Atom:** `plc:generic:digital-io`
- **Topics:** Digital inputs (sensors), digital outputs (actuators), sinking/sourcing
- **Duration:** 9-11 min
- **Keywords:** PLC digital IO, digital inputs outputs, sinking sourcing
- **Hook:** "Everything starts here: on/off signals."
- **Example:** Digital input from proximity sensor, digital output to solenoid valve
- **Quiz:** "What type of signal does a digital input handle?" (Answer: On/off, binary, 0 or 1)

**Video 25: Analog I/O - Measuring Real-World Values (#25)**
- **Atom:** `plc:generic:analog-io`
- **Topics:** 4-20mA, 0-10V, scaling, resolution
- **Duration:** 10-12 min
- **Keywords:** PLC analog IO, 4-20mA, analog signals, scaling
- **Hook:** "Temperature, pressure, speed—here's how PLCs measure them."
- **Example:** 4-20mA pressure sensor (4mA=0psi, 20mA=100psi), scale in PLC
- **Quiz:** "What current represents 0% in a 4-20mA signal?" (Answer: 4mA)

---

### Module 6: Ladder Logic Fundamentals (Videos 26-30)

**Video 26: Ladder Logic Basics - Your First Rung (#26)**
- **Atom:** `plc:generic:ladder-fundamentals`
- **Topics:** Rungs, rails, left-to-right execution, contacts, coils
- **Duration:** 9-11 min
- **Keywords:** ladder logic, ladder logic tutorial, PLC programming basics
- **Hook:** "This is the language of PLCs. Let's learn it."
- **Example:** Simple rung: button (contact) → light (coil)
- **Quiz:** "Ladder logic executes in which direction?" (Answer: Left to right, top to bottom)

**Video 27: Contacts and Coils - The Building Blocks (#27)**
- **Atom:** `plc:generic:contacts-coils`
- **Topics:** Normally open (NO), normally closed (NC), output coils, internal bits
- **Duration:** 8-10 min
- **Keywords:** ladder logic contacts, coils, NO NC contacts, PLC coils
- **Hook:** "Everything in ladder logic is made of these two things."
- **Example:** NO contact (start button), NC contact (stop button), coil (motor contactor)
- **Quiz:** "What happens when an NO contact is energized?" (Answer: Closes, allows current flow)

**Video 28: Seal-In Circuits - How to Latch (#28)**
- **Atom:** `plc:generic:seal-in-circuit`
- **Topics:** 3-wire control, start/stop/seal, maintained contact
- **Duration:** 9-11 min
- **Keywords:** seal in circuit, 3 wire control, PLC latch, motor control
- **Hook:** "Press start, release, motor stays running. Here's the trick."
- **Example:** Start button → Motor coil energizes → Motor auxiliary contact seals in
- **Quiz:** "What keeps the motor running after releasing start?" (Answer: Seal-in contact / auxiliary contact)

**Video 29: Interlocks - Preventing Dangerous Conditions (#29)**
- **Atom:** `plc:generic:interlocks`
- **Topics:** Safety interlocks, permissive logic, AND/OR conditions
- **Duration:** 10-12 min
- **Keywords:** interlocks, safety interlocks, permissive logic, PLC safety
- **Hook:** "[cautionary] Without interlocks, machines can kill. Here's how to prevent it."
- **Example:** Conveyor only runs if guard closed AND e-stop not pressed
- **Quiz:** "What logic requires ALL conditions true?" (Answer: AND logic / series contacts)
- **Safety Level:** WARNING

**Video 30: Your First PLC Program - Start/Stop Motor Control (#30)**
- **Atom:** `plc:generic:first-plc-program`
- **Topics:** Complete program, I/O assignment, testing, troubleshooting
- **Duration:** 12-15 min (milestone video)
- **Keywords:** first PLC program, PLC programming tutorial, motor control ladder logic
- **Hook:** "[enthusiastic] This is it! Your first real PLC program."
- **Example:** 3-wire motor control (start, stop, seal-in, motor output)
- **Quiz:** "What's the first step in writing a PLC program?" (Answer: Define I/O assignments)

---

### Module 7: Timers and Counters (Videos 31-35)

**Video 31: Timer On-Delay (TON) - The Most Common Timer (#31)**
- **Atom:** `plc:ab:timer-on-delay`
- **Topics:** TON operation, preset, accumulated, done bit
- **Duration:** 9-11 min
- **Keywords:** TON timer, timer on delay, PLC timers, Allen Bradley timers
- **Hook:** "Need a delay? This is your timer."
- **Example:** Press button → wait 5 seconds → light turns on
- **Quiz:** "When does the TON done bit turn on?" (Answer: When accumulated = preset)

**Video 32: Timer Off-Delay (TOF) - The Opposite Timer (#32)**
- **Atom:** `plc:ab:timer-off-delay`
- **Topics:** TOF operation, use cases (cooling delays, ramp-down)
- **Duration:** 8-10 min
- **Keywords:** TOF timer, timer off delay, PLC timers
- **Hook:** "TON delays turning on. TOF delays turning off."
- **Example:** Motor stops → wait 10 seconds → cooling fan turns off
- **Quiz:** "When does the TOF done bit turn off?" (Answer: After delay expires when input goes false)

**Video 33: Retentive Timer (RTO) - The Timer That Remembers (#33)**
- **Atom:** `plc:ab:timer-retentive`
- **Topics:** RTO operation, accumulated value retention, reset
- **Duration:** 9-11 min
- **Keywords:** RTO timer, retentive timer, PLC timers
- **Hook:** "Need to accumulate time across cycles? Use RTO."
- **Example:** Track total machine run time (accumulates across power cycles)
- **Quiz:** "What makes RTO different from TON?" (Answer: Retains accumulated value when input goes false)

**Video 34: Counters (CTU/CTD) - Counting Events (#34)**
- **Atoms:** `plc:ab:counter-up`, `plc:ab:counter-down`
- **Topics:** CTU (count up), CTD (count down), done bit, reset
- **Duration:** 10-12 min
- **Keywords:** PLC counters, CTU counter, CTD counter, counting in PLC
- **Hook:** "Count parts, cycles, faults—here's how."
- **Example:** Count bottles on conveyor (CTU increments on photoelectric sensor)
- **Quiz:** "When does the CTU done bit turn on?" (Answer: When accumulated ≥ preset)

**Video 35: Timer/Counter Applications - Real-World Examples (#35)**
- **Atom:** `plc:generic:timer-counter-applications`
- **Topics:** Multi-step sequences, batch counting, alarm delays
- **Duration:** 11-13 min
- **Keywords:** PLC timer applications, PLC counter applications, sequencing
- **Hook:** "Let's combine timers and counters to solve real problems."
- **Example:** Traffic light sequence (timers), production batch counter (stop at 100 units)
- **Quiz:** "How do you create a 2-step sequence?" (Answer: Timer 1 done bit triggers Timer 2)

---

### Module 8: Advanced Ladder Logic (Videos 36-40)

**Video 36: Comparison Instructions - Greater Than, Less Than, Equal (#36)**
- **Atom:** `plc:generic:comparison-instructions`
- **Topics:** EQU, NEQ, GRT, GEQ, LES, LEQ
- **Duration:** 9-11 min
- **Keywords:** comparison instructions, PLC comparisons, EQU GRT LES
- **Hook:** "Need to make decisions based on values? Use comparisons."
- **Example:** If temperature > 150°F, activate cooling fan
- **Quiz:** "Which instruction checks if two values are equal?" (Answer: EQU)

**Video 37: Math Instructions - Add, Subtract, Multiply, Divide (#37)**
- **Atom:** `plc:generic:math-instructions`
- **Topics:** ADD, SUB, MUL, DIV, overflow handling
- **Duration:** 10-12 min
- **Keywords:** PLC math, ADD SUB MUL DIV, math instructions
- **Hook:** "PLCs aren't just on/off. They can calculate."
- **Example:** Convert 4-20mA signal to engineering units (scale 0-100 psi)
- **Quiz:** "What happens if you divide by zero?" (Answer: Math overflow fault)

**Video 38: Move and Copy Instructions - Data Handling (#38)**
- **Atom:** `plc:generic:move-copy-instructions`
- **Topics:** MOV, COP, file manipulation
- **Duration:** 9-11 min
- **Keywords:** MOV instruction, COP instruction, PLC data handling
- **Hook:** "Need to move data around? Here's how."
- **Example:** Copy setpoint value from HMI to timer preset
- **Quiz:** "What's the difference between MOV and COP?" (Answer: MOV moves single value, COP copies arrays)

**Video 39: Sequencers - Automating Patterns (#39)**
- **Atom:** `plc:ab:sequencer`
- **Topics:** SQO (sequencer output), step-by-step control
- **Duration:** 10-12 min
- **Keywords:** PLC sequencer, SQO instruction, step control
- **Hook:** "Repeating patterns? Let the sequencer handle it."
- **Example:** Traffic light (step 1: green, step 2: yellow, step 3: red, repeat)
- **Quiz:** "What triggers the sequencer to advance?" (Answer: Step enable going true)

**Video 40: Program Organization - Routines, Subroutines, and JSRs (#40)**
- **Atom:** `plc:ab:program-organization`
- **Topics:** Main routine, subroutines, JSR/SBR/RET, program structure
- **Duration:** 11-13 min
- **Keywords:** PLC program organization, subroutines, JSR SBR, program structure
- **Hook:** "Big programs get messy. Here's how pros organize them."
- **Example:** Main calls motor_control subroutine, conveyor_control subroutine
- **Quiz:** "What instruction calls a subroutine?" (Answer: JSR / Jump to Subroutine)

---

## Track C: Structured Text & Advanced (Videos 41-60)

### Module 9: Structured Text Basics (Videos 41-45)

**Video 41: Introduction to Structured Text (ST) - Why Learn It? (#41)**
- **Atom:** `plc:generic:structured-text-intro`
- **Topics:** ST vs ladder, when to use ST, advantages
- **Duration:** 8-10 min
- **Keywords:** structured text, ST programming, ladder vs ST
- **Hook:** "Ladder logic is great, but some things are easier in text."
- **Example:** Complex math (calculate PID output) is cleaner in ST
- **Quiz:** "When should you use ST over ladder?" (Answer: Complex math, algorithms, data manipulation)

**Video 42: ST Variables and Data Types - Declaring Your Data (#42)**
- **Atom:** `plc:generic:st-variables`
- **Topics:** INT, REAL, BOOL, DINT, arrays, strings
- **Duration:** 9-11 min
- **Keywords:** ST variables, data types, INT REAL BOOL
- **Hook:** "Before you code, you declare. Here's how."
- **Example:** VAR Motor_Speed : REAL; END_VAR
- **Quiz:** "What data type holds decimals?" (Answer: REAL)

**Video 43: ST Expressions and Operators - Math and Logic (#43)**
- **Atom:** `plc:generic:st-expressions`
- **Topics:** Arithmetic (+, -, *, /), comparison (=, <>, >, <), logical (AND, OR, NOT)
- **Duration:** 10-12 min
- **Keywords:** ST operators, ST expressions, math in ST
- **Hook:** "ST reads like algebra. Let's write some equations."
- **Example:** Output := (Setpoint - Process_Value) * Gain;
- **Quiz:** "What operator checks inequality?" (Answer: <> or !=)

**Video 44: ST Control Structures - IF, FOR, WHILE (#44)**
- **Atoms:** `plc:generic:st-if-else`, `plc:generic:st-for-loop`, `plc:generic:st-while-loop`
- **Topics:** IF/THEN/ELSE, FOR loops, WHILE loops, CASE statements
- **Duration:** 11-13 min
- **Keywords:** ST control structures, IF THEN ELSE, FOR loop, WHILE loop
- **Hook:** "Control flow in ST is powerful. Here's how it works."
- **Example:** IF Temp > 150 THEN Cooling_Fan := TRUE; END_IF
- **Quiz:** "Which loop runs a set number of times?" (Answer: FOR loop)

**Video 45: Ladder vs Structured Text - Converting Programs (#45)**
- **Atom:** `plc:generic:ladder-to-st-conversion`
- **Topics:** Equivalent constructs, when to convert, best practices
- **Duration:** 10-12 min
- **Keywords:** ladder to ST, convert ladder to structured text
- **Hook:** "Same logic, different language. Let's translate."
- **Example:** 3-wire motor control (ladder) → equivalent ST code
- **Quiz:** "What's the ST equivalent of an NO contact?" (Answer: Boolean variable / IF condition)

---

### Module 10: HMI & Data Handling (Videos 46-50)

**Video 46: Introduction to HMIs - Human-Machine Interfaces (#46)**
- **Atom:** `plc:generic:hmi-intro`
- **Topics:** HMI purpose, types (panels, PC-based), communication
- **Duration:** 9-11 min
- **Keywords:** HMI, human machine interface, SCADA, HMI tutorial
- **Hook:** "PLCs run the machine. HMIs let you control it."
- **Example:** HMI showing tank level, start/stop buttons, alarms
- **Quiz:** "What protocol commonly connects HMIs to PLCs?" (Answer: Ethernet/IP, Modbus, Profinet)

**Video 47: Data Tables and Tags - Organizing Your Data (#47)**
- **Atom:** `plc:ab:data-tables`
- **Topics:** Controller tags, program tags, I/O tags, UDTs
- **Duration:** 10-12 min
- **Keywords:** PLC tags, data tables, UDT, Allen Bradley tags
- **Hook:** "Messy data = messy programs. Here's how to organize."
- **Example:** Create UDT for motor (Motor.Running, Motor.Fault, Motor.Speed)
- **Quiz:** "What's a UDT?" (Answer: User-Defined Type, custom data structure)

**Video 48: Alarms and Faults - Handling Errors Gracefully (#48)**
- **Atom:** `plc:generic:alarms-faults`
- **Topics:** Alarm logic, fault detection, HMI alarm displays, logging
- **Duration:** 11-13 min
- **Keywords:** PLC alarms, fault handling, alarm logic
- **Hook:** "Machines fail. Your program should handle it."
- **Example:** Detect overtemp fault, trigger alarm, log to HMI
- **Quiz:** "What should a critical alarm do?" (Answer: Stop machine, alert operator, log event)

**Video 49: Recipe Management - Storing Setpoints (#49)**
- **Atom:** `plc:generic:recipe-management`
- **Topics:** Recipe data structures, loading/saving, HMI integration
- **Duration:** 10-12 min
- **Keywords:** PLC recipes, recipe management, setpoint storage
- **Hook:** "Different products need different settings. Here's how to manage them."
- **Example:** Pizza oven (Recipe 1: 450°F 10min, Recipe 2: 500°F 8min)
- **Quiz:** "Where are recipes typically stored?" (Answer: PLC memory, HMI, or external database)

**Video 50: Data Logging and Trending - Tracking Performance (#50)**
- **Atom:** `plc:generic:data-logging`
- **Topics:** Historical data, trend charts, CSV export, databases
- **Duration:** 10-12 min
- **Keywords:** data logging, trending, PLC data logging
- **Hook:** "Can't improve what you don't measure. Let's log it."
- **Example:** Log tank level every 1 second, export to CSV for analysis
- **Quiz:** "Why log data?" (Answer: Troubleshooting, optimization, compliance)

---

### Module 11: Communications & Networking (Videos 51-55)

**Video 51: Industrial Networks - Ethernet/IP, Modbus, Profinet (#51)**
- **Atoms:** `plc:generic:ethernet-ip`, `plc:generic:modbus`, `plc:generic:profinet`
- **Topics:** Network protocols, OSI model, vendor ecosystems
- **Duration:** 11-13 min
- **Keywords:** industrial networks, Ethernet IP, Modbus, Profinet
- **Hook:** "PLCs don't work alone. They talk. Here's how."
- **Example:** Allen-Bradley uses Ethernet/IP, Siemens uses Profinet
- **Quiz:** "Which protocol is vendor-neutral?" (Answer: Modbus)

**Video 52: Remote I/O - Expanding Your System (#52)**
- **Atom:** `plc:generic:remote-io`
- **Topics:** Distributed I/O, fieldbus, advantages (reduce wiring)
- **Duration:** 9-11 min
- **Keywords:** remote IO, distributed IO, fieldbus, PLC networking
- **Hook:** "Why run 500 feet of wire when you can run one network cable?"
- **Example:** Main PLC in control room, remote I/O rack on factory floor
- **Quiz:** "What's the main advantage of remote I/O?" (Answer: Reduced wiring, flexible placement)

**Video 53: PLC-to-PLC Communication - Multiple Controllers (#53)**
- **Atom:** `plc:generic:plc-to-plc-comm`
- **Topics:** MSG instruction, CIP messaging, peer-to-peer
- **Duration:** 10-12 min
- **Keywords:** PLC to PLC communication, MSG instruction, CIP
- **Hook:** "Big systems need multiple PLCs. Here's how they talk."
- **Example:** PLC 1 (conveyor) sends count to PLC 2 (palletizer)
- **Quiz:** "What instruction sends data between PLCs?" (Answer: MSG / Message)

**Video 54: Connecting PLCs to Databases - SQL and OPC (#54)**
- **Atoms:** `plc:generic:opc`, `plc:generic:sql-integration`
- **Topics:** OPC UA, SQL databases, data collection
- **Duration:** 11-13 min
- **Keywords:** OPC, OPC UA, PLC to database, SQL
- **Hook:** "Want your PLC data in Excel or Power BI? Here's the bridge."
- **Example:** OPC server reads PLC tags, writes to SQL database
- **Quiz:** "What's OPC stand for?" (Answer: OLE for Process Control / Open Platform Communications)

**Video 55: Troubleshooting Network Issues - Connectivity and Faults (#55)**
- **Atom:** `plc:generic:network-troubleshooting`
- **Topics:** Ping tests, MAC addresses, switch configuration, cable issues
- **Duration:** 10-12 min
- **Keywords:** network troubleshooting, PLC network issues, Ethernet troubleshooting
- **Hook:** "Network down? Production stops. Here's how to fix it fast."
- **Example:** PLC offline → check cable, ping test, verify IP address
- **Quiz:** "What tool tests network connectivity?" (Answer: Ping)

---

### Module 12: Motion Control & Advanced Topics (Videos 56-60)

**Video 56: Motion Control Basics - Positioning and Velocity (#56)**
- **Atom:** `plc:generic:motion-control-intro`
- **Topics:** Servo motors, stepper motors, positioning modes
- **Duration:** 11-13 min
- **Keywords:** motion control, servo motors, stepper motors, positioning
- **Hook:** "Need precise positioning? Motion control is the answer."
- **Example:** Servo motor moves to position 1000 encoder counts
- **Quiz:** "What's the difference between servo and stepper?" (Answer: Servo has feedback, stepper is open-loop)

**Video 57: PID Control - The Universal Controller (#57)**
- **Atom:** `plc:generic:pid-control`
- **Topics:** Proportional, Integral, Derivative, tuning, applications
- **Duration:** 12-15 min
- **Keywords:** PID control, PID tuning, proportional integral derivative
- **Hook:** "Temperature, pressure, level—PID controls it all."
- **Example:** PID controlling oven temperature (setpoint 450°F)
- **Quiz:** "What does the Integral term do?" (Answer: Eliminates steady-state error)

**Video 58: Safety PLCs - Safety-Rated Control (#58)**
- **Atom:** `plc:generic:safety-plc`
- **Topics:** Safety integrity levels (SIL), safety I/O, dual-channel logic
- **Duration:** 11-13 min
- **Keywords:** safety PLC, SIL, functional safety, safety rated control
- **Hook:** "[cautionary] Standard PLCs can fail. Safety PLCs can't."
- **Example:** Emergency stop circuit (dual-channel, monitored)
- **Quiz:** "What does SIL stand for?" (Answer: Safety Integrity Level)
- **Safety Level:** DANGER

**Video 59: Cloud Connectivity - IIoT and Industry 4.0 (#59)**
- **Atoms:** `plc:generic:iiot`, `plc:generic:cloud-connectivity`
- **Topics:** MQTT, cloud platforms (AWS, Azure), edge gateways
- **Duration:** 11-13 min
- **Keywords:** IIoT, Industry 4.0, PLC cloud, MQTT
- **Hook:** "The future of manufacturing is connected. Here's how."
- **Example:** PLC sends production data to AWS via MQTT
- **Quiz:** "What protocol is common for IIoT?" (Answer: MQTT)

**Video 60: Best Practices - Writing Professional PLC Code (#60)**
- **Atom:** `plc:generic:best-practices`
- **Topics:** Commenting, naming conventions, documentation, version control
- **Duration:** 12-15 min (milestone video)
- **Keywords:** PLC best practices, PLC programming standards, documentation
- **Hook:** "Write code like a pro. Your future self will thank you."
- **Example:** Compare bad code (no comments, generic names) vs good code
- **Quiz:** "Why comment your code?" (Answer: Maintainability, troubleshooting, teamwork)

---

## Track D: Vendor-Specific Deep Dives (Videos 61-80)

### Module 13: Allen-Bradley / Rockwell (Videos 61-70)

**Video 61: Allen-Bradley Platform Overview - ControlLogix, CompactLogix (#61)**
- **Video 62: Studio 5000 Basics - Navigating the Software (#62)**
- **Video 63: RSLogix 500 - Programming SLC/MicroLogix (#63)**
- **Video 64: Allen-Bradley Safety PLCs - GuardLogix (#64)**
- **Video 65: PowerFlex Drives - Configuring VFDs (#65)**
- **Video 66: FactoryTalk View - Building HMIs (#66)**
- **Video 67: Ethernet/IP Configuration - Network Setup (#67)**
- **Video 68: Allen-Bradley Motion Control - Kinetix Servos (#68)**
- **Video 69: Troubleshooting Allen-Bradley Systems (#69)**
- **Video 70: Allen-Bradley vs Siemens - The Great Debate (#70)**

---

### Module 14: Siemens (Videos 71-80)

**Video 71: Siemens Platform Overview - S7-1200, S7-1500 (#71)**
- **Video 72: TIA Portal Basics - Navigating the Software (#72)**
- **Video 73: Siemens Safety PLCs - Fail-Safe Programming (#73)**
- **Video 74: Sinamics Drives - Configuring VFDs (#74)**
- **Video 75: WinCC HMI - Building Operator Interfaces (#75)**
- **Video 76: Profinet Configuration - Network Setup (#76)**
- **Video 77: Siemens Motion Control - Simotion (#77)**
- **Video 78: Structured Control Language (SCL) - Siemens ST (#78)**
- **Video 79: Troubleshooting Siemens Systems (#79)**
- **Video 80: Siemens Best Practices - TIA Portal Tips (#80)**

---

## Track E: AI & Automation (Videos 81-100)

### Module 15: AI-Augmented PLC Programming (Videos 81-90)

**Video 81: AI for PLC Programming - The Future is Here (#81)**
- **Atom:** `plc:generic:ai-plc-intro`
- **Topics:** AI code generation, verification, optimization
- **Duration:** 10-12 min
- **Keywords:** AI PLC programming, AI automation, LLM PLC
- **Hook:** "What if AI could write your PLC code? It can."
- **Example:** Spec → AI generates ladder logic → human reviews
- **Quiz:** "What's the human's role in AI-generated code?" (Answer: Review, verify, approve)

**Video 82: Generating Ladder Logic with AI - Spec to Code (#82)**
- **Video 83: AI-Powered Troubleshooting - Fault Diagnosis (#83)**
- **Video 84: Optimizing PLC Code with AI - Performance Tuning (#84)**
- **Video 85: AI-Generated Documentation - Auto-Commenting (#85)**
- **Video 86: Testing AI-Generated Code - Verification Loops (#86)**
- **Video 87: AI for HMI Design - Screen Generation (#87)**
- **Video 88: Predictive Maintenance with AI - Detecting Failures Early (#88)**
- **Video 89: AI + Computer Use - Driving Studio 5000/TIA Portal (#89)**
- **Video 90: The Future of Automation - Agents All the Way Down (#90)**

---

### Module 16: Capstone & Real-World Projects (Videos 91-100)

**Video 91: Project 1 - Conveyor System with Sensors (#91)**
- **Video 92: Project 2 - Batch Process Control (Mixing Tank) (#92)**
- **Video 93: Project 3 - Traffic Light Sequencer (#93)**
- **Video 94: Project 4 - Automated Parking Gate (#94)**
- **Video 95: Project 5 - Temperature Control System (PID) (#95)**
- **Video 96: Project 6 - Multi-Motor Coordinated Control (#96)**
- **Video 97: Project 7 - Pick-and-Place Robot Arm (#97)**
- **Video 98: Project 8 - Warehouse Automation (Full System) (#98)**
- **Video 99: Project 9 - AI-Generated PLC Program (End-to-End) (#99)**
- **Video 100: Congratulations! Where to Go Next (#100)**
  - Recap of journey (electricity → AI)
  - Career paths (technician, engineer, integrator)
  - Resources for continued learning
  - Premium courses, certifications
  - "You've completed the A-to-Z curriculum. Now go build something amazing."

---

## Content Production Notes

### Pacing Strategy
- **Weeks 1-4:** Videos 1-10 (Electrical Fundamentals) - Foundation
- **Weeks 5-8:** Videos 11-20 (Advanced Electrical + Safety) - Build depth
- **Weeks 9-12:** Videos 21-30 (PLC Basics + First Program) - Milestone
- **Month 4-6:** Videos 31-60 (Timers, ST, HMI, Networking) - Expand
- **Month 7-12:** Videos 61-100 (Vendor-specific, AI, Projects) - Advanced

### Anchor Videos (Heavily Promoted)
- **Video 1:** "What is Electricity?" - Foundation for everyone
- **Video 10:** "Relays and Contactors" - Bridge to PLCs
- **Video 21:** "What is a PLC?" - PLC introduction
- **Video 30:** "Your First PLC Program" - Major milestone
- **Video 50:** "Data Logging and Trending" - HMI milestone
- **Video 81:** "AI for PLC Programming" - Future vision
- **Video 100:** "Congratulations!" - Completion celebration

### SEO Focus Areas
- **High-Volume Keywords:** "PLC programming tutorial", "ladder logic", "Allen Bradley", "Siemens"
- **Low-Competition Keywords:** "structured text tutorial", "PLC timer examples", "AI PLC programming"
- **Local Keywords:** "industrial automation training [city]", "PLC courses near me"

### Community Engagement
- Pin comment on each video: "What should I cover next?"
- Respond to technical questions with atom-backed answers
- Create "You Asked, I Answered" series (videos 101+) based on comments

---

## Success Metrics

### Video Performance Targets
- **CTR:** > 4% (higher for anchor videos)
- **AVD:** > 50% (viewers watch half the video)
- **Engagement:** > 2% (likes + comments / views)
- **Traffic Sources:** 40% search, 30% suggested, 20% browse, 10% external

### Playlist Performance
- **View-Through Rate:** > 40% (viewers watch next video in playlist)
- **Completion Rate:** > 60% (viewers finish playlist)

### Channel Growth
- **Month 3:** 1,000 subscribers
- **Month 6:** 5,000 subscribers
- **Month 12:** 20,000 subscribers
- **Year 2:** 100,000 subscribers

---

## Next Steps

1. ✅ Read this roadmap (you're here)
2. Use this as guide for Master Curriculum Agent (Week 5)
3. Content Strategy Agent pulls topics from this roadmap
4. Scriptwriter Agent references this for video structure
5. Analytics Agent tracks performance vs targets
6. Update roadmap quarterly based on analytics + community feedback

**The roadmap is your content bible. Follow it, iterate on it, grow with it.**
