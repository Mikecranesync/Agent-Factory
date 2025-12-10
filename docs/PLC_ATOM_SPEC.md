# PLC Knowledge Atom Standard (v0.1)
## First-Principles Design Document
### December 9, 2025

---

## Executive Summary

This document extends the **Industrial Maintenance Knowledge Atom Standard v1.0** for the PLC programming education domain. It combines:

1. **Knowledge Atom Standard v1.0** – Base schema for industrial knowledge (proven with RIVET)
2. **IEC 61131-3** – International standard for PLC programming languages
3. **IEC 62061** – Safety of machinery - Functional safety
4. **LLM4PLC Research Pattern** – Spec → Code → Verify loop (UC Irvine, 2024)
5. **Cole Medin Computer-Use Pattern** – Agentic coding with visual verification

This is **NOT** a new standard—it's an extension of proven industrial knowledge standards to the PLC programming vertical.

---

## Part 1: Why PLC Atoms Are Different From Maintenance Atoms

### Maintenance Atoms (RIVET)
- **Focus:** Troubleshooting existing systems
- **User:** Field technicians fixing broken equipment
- **Content:** Error codes, procedures, fault diagnosis
- **Outcome:** Equipment back online

### PLC Atoms (PLC Tutor)
- **Focus:** Teaching programming patterns and generating code
- **User:** PLC programmers learning or automating code generation
- **Content:** Programming patterns, logic structures, code examples
- **Outcome:** Working PLC programs

### Key Differences

| Dimension | Maintenance Atoms | PLC Atoms |
|-----------|-------------------|-----------|
| **Primary Content** | Text + images | Ladder logic + structured text |
| **Validation** | Community corroboration | Executable code verification |
| **Safety** | Informational warnings | Critical safety interlocks |
| **Structure** | Free-form description | Structured I/O + logic + steps |
| **Sources** | Manuals, forums, Reddit | Vendor docs, textbooks, standards |
| **User Interaction** | Read-only knowledge | Code generation input |

---

## Part 2: The 4 PLC Atom Types

### Type 1: Concept Atoms
**Purpose:** Fundamental PLC programming concepts
**Examples:** "What is scan cycle", "How does latch/unlatch work", "Timer vs Counter"

**Structure:**
```json
{
  "atom_type": "concept",
  "plc:conceptCategory": "fundamentals|timing|logic|data_handling|motion|safety",
  "plc:difficulty": "beginner|intermediate|advanced|expert",
  "plc:prerequisiteAtoms": ["atom-id-1", "atom-id-2"],
  "plc:learningObjectives": [
    "Understand PLC scan cycle execution order",
    "Identify when to use edge-triggered vs level-triggered logic"
  ],
  "plc:commonMistakes": [
    {
      "mistake": "Not accounting for scan time in timing logic",
      "consequence": "Unpredictable timer behavior",
      "correction": "Use hardware timers or add scan time compensation"
    }
  ]
}
```

### Type 2: Pattern Atoms
**Purpose:** Reusable programming patterns (like design patterns in software)
**Examples:** "3-wire motor control", "Debounce filter", "State machine template"

**Structure:**
```json
{
  "atom_type": "pattern",
  "plc:patternCategory": "motor_control|safety|sequencing|analog|communication",
  "plc:inputs": [
    {
      "tag": "Start_PB",
      "type": "BOOL",
      "io_type": "DI",
      "description": "Normally-open start pushbutton",
      "address": "I:0/0",
      "required": true
    }
  ],
  "plc:outputs": [
    {
      "tag": "Motor_Contactor",
      "type": "BOOL",
      "io_type": "DO",
      "description": "Motor contactor coil",
      "address": "O:0/0"
    }
  ],
  "plc:internalTags": [
    {
      "tag": "Motor_Running",
      "type": "BOOL",
      "description": "Motor running status bit"
    }
  ],
  "plc:logicDescription": "Parallel seal-in with series stop button (fail-safe NC)",
  "plc:ladderLogicSteps": [
    "Rung 1: Start_PB (NO) parallel Motor_Running (NO) in series with Stop_PB (NC) → Motor_Contactor (coil)",
    "Rung 2: Motor_Contactor (NO) → Motor_Running (coil) [seal-in logic]"
  ],
  "plc:structuredTextEquivalent": "Motor_Contactor := (Start_PB OR Motor_Running) AND Stop_PB;\nMotor_Running := Motor_Contactor;",
  "plc:safetyRequirements": [
    "Stop button must be NC (normally-closed) for fail-safe operation",
    "Overload relay required (not shown in logic)",
    "Emergency stop must break power to contactor directly"
  ]
}
```

### Type 3: Fault Atoms
**Purpose:** Common PLC errors and how to diagnose/fix them
**Examples:** "I/O module not responding", "Watchdog timer fault", "Network timeout"

**Structure:**
```json
{
  "atom_type": "fault",
  "plc:faultCode": "E0032",
  "plc:faultCategory": "hardware|communication|program|safety|configuration",
  "plc:symptoms": [
    "Red fault LED on CPU",
    "HMI shows 'PLC offline'",
    "I/O not updating"
  ],
  "plc:probableCauses": [
    {
      "cause": "Watchdog timer expired",
      "likelihood": "high",
      "diagnostic": "Check PLC scan time in diagnostics tab"
    }
  ],
  "plc:resolutionSteps": [
    "1. Check PLC mode (RUN/STOP/FAULT)",
    "2. Access fault log via HMI or programming software",
    "3. Note exact fault code and timestamp",
    "4. Check for infinite loops or blocking instructions",
    "5. Optimize scan time or increase watchdog threshold"
  ],
  "plc:preventionMeasures": [
    "Avoid blocking instructions in main program",
    "Use periodic tasks for slow operations",
    "Monitor scan time during commissioning"
  ]
}
```

### Type 4: Procedure Atoms
**Purpose:** Step-by-step procedures (commissioning, testing, backup/restore)
**Examples:** "Initial PLC startup procedure", "Network configuration checklist", "Safety validation"

**Structure:**
```json
{
  "atom_type": "procedure",
  "plc:procedureCategory": "commissioning|testing|maintenance|troubleshooting|documentation",
  "plc:estimatedTime": "30 minutes",
  "plc:requiredTools": [
    "Programming cable (USB-A to RS232)",
    "Programming software (Studio 5000 v33+)",
    "Multimeter (for I/O verification)",
    "Lockout/tagout kit"
  ],
  "plc:prerequisites": [
    "Power supply verified (24VDC, 2A minimum)",
    "All I/O modules installed and seated",
    "Network cables connected and tested",
    "Safety checklist completed"
  ],
  "plc:steps": [
    {
      "stepNumber": 1,
      "action": "Apply power to PLC and verify green RUN LED",
      "expectedResult": "Green RUN LED solid, no fault codes",
      "troubleshooting": "If red FAULT LED: check power supply voltage and fuses"
    }
  ],
  "plc:safetyWarnings": [
    {
      "severity": "DANGER",
      "warning": "Apply lockout/tagout before touching any I/O wiring",
      "consequence": "Risk of electric shock or equipment damage"
    }
  ],
  "plc:verificationChecklist": [
    "All I/O points tested and documented",
    "Network communication verified",
    "Program uploaded and backed up",
    "Safety interlocks tested"
  ]
}
```

---

## Part 3: JSON Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://plctutor.schema.org/schema/plc-atom-v0.1.json",
  "title": "PLC Programming Knowledge Atom",
  "description": "Standard schema for PLC programming knowledge units (extends Knowledge Atom v1.0)",
  "type": "object",

  "required": [
    "@context",
    "@id",
    "@type",
    "atom_type",
    "schema:name",
    "schema:description",
    "plc:vendor",
    "plc:platform",
    "plc:status"
  ],

  "properties": {
    "@context": {
      "type": "string",
      "enum": ["https://plctutor.schema.org/context/v0.1"],
      "description": "JSON-LD context for PLC domain"
    },

    "@id": {
      "type": "string",
      "pattern": "^plc:[a-z_]+:[a-z0-9-]+$",
      "description": "Unique identifier (format: plc:vendor:slug)",
      "examples": ["plc:ab:motor-start-stop", "plc:siemens:timer-on-delay"]
    },

    "@type": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 2,
      "description": "Always includes 'schema:Thing' and 'plctutor:PLCAtom'"
    },

    "atom_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$",
      "description": "Schema version (current: '0.1')"
    },

    "atom_type": {
      "type": "string",
      "enum": ["concept", "pattern", "fault", "procedure"],
      "description": "Type of PLC knowledge unit"
    },

    "schema:name": {
      "type": "string",
      "minLength": 5,
      "maxLength": 100,
      "description": "Human-readable title",
      "examples": ["3-Wire Motor Start/Stop/Seal-In", "Timer On-Delay (TON) Basics"]
    },

    "schema:description": {
      "type": "string",
      "minLength": 20,
      "maxLength": 2000,
      "description": "Detailed explanation of concept/pattern/fault/procedure"
    },

    "plc:vendor": {
      "type": "string",
      "enum": [
        "allen_bradley",
        "siemens",
        "schneider",
        "mitsubishi",
        "omron",
        "codesys",
        "generic"
      ],
      "description": "PLC vendor (use 'generic' for vendor-agnostic atoms)"
    },

    "plc:platform": {
      "type": "string",
      "description": "Specific PLC platform",
      "examples": ["s7-1200", "s7-1500", "control_logix", "compact_logix", "micro800"]
    },

    "plc:programmingLanguage": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "ladder_logic",
          "structured_text",
          "function_block_diagram",
          "sequential_function_chart",
          "instruction_list"
        ]
      },
      "description": "IEC 61131-3 languages used in this atom"
    },

    "plc:difficulty": {
      "type": "string",
      "enum": ["beginner", "intermediate", "advanced", "expert"],
      "description": "Required skill level"
    },

    "plc:prerequisiteAtoms": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Atom IDs that should be learned first",
      "examples": [["plc:generic:io-basics", "plc:generic:ladder-fundamentals"]]
    },

    "plc:inputs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["tag", "type", "description"],
        "properties": {
          "tag": {
            "type": "string",
            "description": "Variable tag name",
            "examples": ["Start_PB", "Temp_Sensor_AI"]
          },
          "type": {
            "type": "string",
            "enum": ["BOOL", "INT", "DINT", "REAL", "STRING", "TIMER", "COUNTER"],
            "description": "Data type"
          },
          "io_type": {
            "type": "string",
            "enum": ["DI", "AI", "internal"],
            "description": "Input type (DI=Digital Input, AI=Analog Input)"
          },
          "address": {
            "type": "string",
            "description": "Physical I/O address",
            "examples": ["I:0/0", "%I0.0", "Local:1:I.Data.0"]
          },
          "description": {
            "type": "string",
            "description": "Human-readable description"
          },
          "required": {
            "type": "boolean",
            "default": true,
            "description": "Is this input required for the pattern to work?"
          }
        }
      },
      "description": "Input tags for pattern atoms"
    },

    "plc:outputs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["tag", "type", "description"],
        "properties": {
          "tag": { "type": "string" },
          "type": {
            "type": "string",
            "enum": ["BOOL", "INT", "DINT", "REAL", "STRING"]
          },
          "io_type": {
            "type": "string",
            "enum": ["DO", "AO", "internal"]
          },
          "address": { "type": "string" },
          "description": { "type": "string" }
        }
      },
      "description": "Output tags for pattern atoms"
    },

    "plc:internalTags": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["tag", "type", "description"],
        "properties": {
          "tag": { "type": "string" },
          "type": { "type": "string" },
          "description": { "type": "string" }
        }
      },
      "description": "Internal variables (not mapped to I/O)"
    },

    "plc:logicDescription": {
      "type": "string",
      "description": "Plain-English description of the logic flow"
    },

    "plc:ladderLogicSteps": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Step-by-step ladder logic rungs in text format"
    },

    "plc:structuredTextEquivalent": {
      "type": "string",
      "description": "Structured text (ST) code equivalent"
    },

    "plc:functionBlockDiagram": {
      "type": "string",
      "description": "Function block diagram in text or URL to image"
    },

    "plc:safetyRequirements": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Safety constraints and requirements"
    },

    "plc:safetyLevel": {
      "type": "string",
      "enum": ["info", "caution", "warning", "danger", "sil_rated"],
      "description": "Safety criticality level"
    },

    "plc:faultCode": {
      "type": "string",
      "description": "Error/fault code (for fault atoms)",
      "examples": ["E0032", "SF_0001", "C000001E"]
    },

    "plc:faultCategory": {
      "type": "string",
      "enum": ["hardware", "communication", "program", "safety", "configuration"],
      "description": "Category of fault"
    },

    "plc:symptoms": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Observable symptoms of the fault"
    },

    "plc:probableCauses": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "cause": { "type": "string" },
          "likelihood": {
            "type": "string",
            "enum": ["high", "medium", "low"]
          },
          "diagnostic": { "type": "string" }
        }
      },
      "description": "Likely root causes with diagnostic steps"
    },

    "plc:resolutionSteps": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Step-by-step resolution procedure"
    },

    "plc:preventionMeasures": {
      "type": "array",
      "items": { "type": "string" },
      "description": "How to prevent this fault from occurring"
    },

    "plc:procedureCategory": {
      "type": "string",
      "enum": ["commissioning", "testing", "maintenance", "troubleshooting", "documentation"],
      "description": "Type of procedure"
    },

    "plc:estimatedTime": {
      "type": "string",
      "description": "Estimated time to complete",
      "examples": ["30 minutes", "2-4 hours", "1 day"]
    },

    "plc:requiredTools": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Tools and equipment needed"
    },

    "plc:prerequisites": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Prerequisites before starting procedure"
    },

    "plc:steps": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["stepNumber", "action"],
        "properties": {
          "stepNumber": { "type": "integer" },
          "action": { "type": "string" },
          "expectedResult": { "type": "string" },
          "troubleshooting": { "type": "string" }
        }
      },
      "description": "Step-by-step procedure"
    },

    "plc:safetyWarnings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "severity": {
            "type": "string",
            "enum": ["NOTICE", "CAUTION", "WARNING", "DANGER"]
          },
          "warning": { "type": "string" },
          "consequence": { "type": "string" }
        }
      },
      "description": "Safety warnings (ANSI Z535 format)"
    },

    "plc:verificationChecklist": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Checklist to verify procedure completion"
    },

    "plc:conceptCategory": {
      "type": "string",
      "enum": ["fundamentals", "timing", "logic", "data_handling", "motion", "safety", "communication"],
      "description": "Category for concept atoms"
    },

    "plc:learningObjectives": {
      "type": "array",
      "items": { "type": "string" },
      "description": "What the learner will understand after this concept"
    },

    "plc:commonMistakes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "mistake": { "type": "string" },
          "consequence": { "type": "string" },
          "correction": { "type": "string" }
        }
      },
      "description": "Common mistakes learners make"
    },

    "plc:patternCategory": {
      "type": "string",
      "enum": ["motor_control", "safety", "sequencing", "analog", "communication", "timing", "counting"],
      "description": "Category for pattern atoms"
    },

    "plc:codeExample": {
      "type": "object",
      "properties": {
        "language": {
          "type": "string",
          "enum": ["ladder_logic", "structured_text", "function_block_diagram"]
        },
        "code": { "type": "string" },
        "tested": { "type": "boolean" },
        "testPlatform": { "type": "string" }
      },
      "description": "Executable code example"
    },

    "plc:status": {
      "type": "string",
      "enum": ["draft", "validated", "tested_on_hardware", "certified"],
      "description": "Validation status of this atom"
    },

    "schema:provider": {
      "type": "object",
      "required": ["plc:sourceTier", "schema:url"],
      "properties": {
        "@type": { "const": "plctutor:KnowledgeSource" },
        "plc:sourceTier": {
          "type": "string",
          "enum": [
            "vendor_manual",
            "textbook",
            "iec_standard",
            "university_course",
            "community_validated",
            "user_contributed"
          ]
        },
        "schema:url": { "type": "string", "format": "uri" },
        "schema:author": { "type": "string" },
        "schema:datePublished": { "type": "string", "format": "date-time" }
      }
    },

    "schema:dateCreated": { "type": "string", "format": "date-time" },
    "schema:dateModified": { "type": "string", "format": "date-time" }
  },

  "additionalProperties": false
}
```

---

## Part 4: Example PLC Atoms

### Example 1: Pattern Atom (3-Wire Motor Control)

```json
{
  "@context": "https://plctutor.schema.org/context/v0.1",
  "@id": "plc:ab:motor-start-stop-seal",
  "@type": ["schema:Thing", "plctutor:PLCAtom"],
  "atom_version": "0.1",
  "atom_type": "pattern",

  "schema:name": "3-Wire Motor Start/Stop/Seal-In Control",
  "schema:description": "Basic motor control circuit using maintained contact seal-in logic. This is the foundational pattern for motor control in industrial automation. The circuit uses a normally-open start button, normally-closed stop button, and an auxiliary contact from the motor contactor to create a 'seal-in' or 'latch' that keeps the motor running after the start button is released.",

  "plc:vendor": "allen_bradley",
  "plc:platform": "control_logix",
  "plc:programmingLanguage": ["ladder_logic", "structured_text"],
  "plc:difficulty": "beginner",
  "plc:prerequisiteAtoms": [
    "plc:generic:io-basics",
    "plc:generic:ladder-fundamentals",
    "plc:generic:seal-in-concept"
  ],

  "plc:patternCategory": "motor_control",

  "plc:inputs": [
    {
      "tag": "Start_PB",
      "type": "BOOL",
      "io_type": "DI",
      "description": "Normally-open start pushbutton",
      "address": "Local:1:I.Data.0",
      "required": true
    },
    {
      "tag": "Stop_PB",
      "type": "BOOL",
      "io_type": "DI",
      "description": "Normally-closed stop pushbutton",
      "address": "Local:1:I.Data.1",
      "required": true
    },
    {
      "tag": "OL_Contact",
      "type": "BOOL",
      "io_type": "DI",
      "description": "Overload relay auxiliary contact (NC)",
      "address": "Local:1:I.Data.2",
      "required": false
    }
  ],

  "plc:outputs": [
    {
      "tag": "Motor_Contactor",
      "type": "BOOL",
      "io_type": "DO",
      "description": "Motor contactor coil",
      "address": "Local:2:O.Data.0"
    }
  ],

  "plc:internalTags": [
    {
      "tag": "Motor_Running",
      "type": "BOOL",
      "description": "Motor running status bit (mirrors contactor state)"
    }
  ],

  "plc:logicDescription": "Start button and seal-in contact in parallel, all in series with stop button. When start button is pressed, contactor energizes. Contactor's auxiliary contact seals in, allowing start button to be released. Pressing stop button breaks the circuit.",

  "plc:ladderLogicSteps": [
    "Rung 0: Start_PB (XIC) parallel Motor_Running (XIC), in series with Stop_PB (XIC) and OL_Contact (XIC) → Motor_Contactor (OTE)",
    "Rung 1: Motor_Contactor (XIC) → Motor_Running (OTE)"
  ],

  "plc:structuredTextEquivalent": "Motor_Contactor := (Start_PB OR Motor_Running) AND Stop_PB AND OL_Contact;\nMotor_Running := Motor_Contactor;",

  "plc:safetyRequirements": [
    "Stop button MUST be normally-closed (NC) for fail-safe operation",
    "Overload relay contact MUST break circuit on overload condition",
    "Emergency stop circuit MUST break power to contactor directly (not shown)",
    "Seal-in contact must be properly sized for coil current draw",
    "Lockout/tagout required before servicing"
  ],

  "plc:safetyLevel": "caution",

  "plc:codeExample": {
    "language": "ladder_logic",
    "code": "[Rung 0]\n|--] [--+--] [--+--] [--+--] [--+--(  )--|\n| Start_PB   | Motor_Running | Stop_PB | OL_Contact | Motor_Contactor |\n\n[Rung 1]\n|--] [--+--(  )--|\n| Motor_Contactor | Motor_Running |",
    "tested": true,
    "testPlatform": "Studio 5000 Emulate, CompactLogix 5380"
  },

  "plc:status": "tested_on_hardware",

  "schema:provider": {
    "@type": "plctutor:KnowledgeSource",
    "plc:sourceTier": "textbook",
    "schema:url": "https://literature.rockwellautomation.com/idc/groups/literature/documents/rm/1756-rm003_-en-p.pdf",
    "schema:author": "Rockwell Automation",
    "schema:datePublished": "2023-01-15T00:00:00Z"
  },

  "schema:dateCreated": "2025-12-09T00:00:00Z",
  "schema:dateModified": "2025-12-09T00:00:00Z"
}
```

### Example 2: Concept Atom (Scan Cycle)

```json
{
  "@context": "https://plctutor.schema.org/context/v0.1",
  "@id": "plc:generic:scan-cycle-concept",
  "@type": ["schema:Thing", "plctutor:PLCAtom"],
  "atom_version": "0.1",
  "atom_type": "concept",

  "schema:name": "PLC Scan Cycle Fundamentals",
  "schema:description": "Understanding how PLCs execute programs in a continuous scan cycle: Input scan → Program scan → Output scan → Housekeeping. This is fundamental to understanding PLC behavior, timing, and troubleshooting logic issues.",

  "plc:vendor": "generic",
  "plc:platform": "all",
  "plc:programmingLanguage": ["ladder_logic", "structured_text", "function_block_diagram"],
  "plc:difficulty": "beginner",
  "plc:prerequisiteAtoms": [],

  "plc:conceptCategory": "fundamentals",

  "plc:learningObjectives": [
    "Understand the four phases of a PLC scan cycle",
    "Explain why output changes don't occur until the end of the scan",
    "Identify timing issues related to scan time",
    "Calculate worst-case input-to-output delay"
  ],

  "plc:commonMistakes": [
    {
      "mistake": "Expecting immediate output response within the same scan",
      "consequence": "Logic doesn't behave as expected, one-scan delays occur",
      "correction": "Account for scan cycle in timing-critical logic, use immediate I/O instructions if needed"
    },
    {
      "mistake": "Not monitoring scan time during commissioning",
      "consequence": "Watchdog faults, unpredictable timing",
      "correction": "Always check max scan time in diagnostics, optimize code if needed"
    }
  ],

  "plc:status": "validated",

  "schema:provider": {
    "@type": "plctutor:KnowledgeSource",
    "plc:sourceTier": "textbook",
    "schema:url": "https://www.plcacademy.com/plc-scan-cycle/",
    "schema:author": "PLC Academy",
    "schema:datePublished": "2024-03-10T00:00:00Z"
  },

  "schema:dateCreated": "2025-12-09T00:00:00Z",
  "schema:dateModified": "2025-12-09T00:00:00Z"
}
```

### Example 3: Fault Atom (Watchdog Timeout)

```json
{
  "@context": "https://plctutor.schema.org/context/v0.1",
  "@id": "plc:siemens:watchdog-timeout-fault",
  "@type": ["schema:Thing", "plctutor:PLCAtom"],
  "atom_version": "0.1",
  "atom_type": "fault",

  "schema:name": "Watchdog Timer Timeout Fault (Siemens S7-1200)",
  "schema:description": "The PLC enters STOP mode because the program scan time exceeded the configured watchdog timeout value. This is a safety mechanism to prevent runaway programs.",

  "plc:vendor": "siemens",
  "plc:platform": "s7-1200",
  "plc:difficulty": "intermediate",

  "plc:faultCode": "SF_0001",
  "plc:faultCategory": "program",

  "plc:symptoms": [
    "PLC enters STOP mode unexpectedly",
    "Red SF (System Fault) LED illuminated on CPU",
    "HMI shows 'CPU in STOP mode'",
    "Diagnostic buffer shows 'Cycle time exceeded'"
  ],

  "plc:probableCauses": [
    {
      "cause": "Infinite loop in program logic",
      "likelihood": "high",
      "diagnostic": "Review FOR loops, WHILE loops, and recursive function blocks"
    },
    {
      "cause": "Excessive program scan time",
      "likelihood": "high",
      "diagnostic": "Check OB1 cycle time in TIA Portal diagnostics"
    },
    {
      "cause": "Blocking communication instruction",
      "likelihood": "medium",
      "diagnostic": "Check for TRCV/TSEND blocks without timeout"
    }
  ],

  "plc:resolutionSteps": [
    "1. Switch CPU to STOP mode if not already",
    "2. Open TIA Portal and go online with PLC",
    "3. Open Diagnostic Buffer (Tools → Diagnostic Buffer)",
    "4. Note the exact timestamp and fault details",
    "5. Check 'Cycle time monitoring' in CPU properties",
    "6. Review program for infinite loops or blocking instructions",
    "7. Increase watchdog timeout if scan time is legitimately long",
    "8. Optimize program logic or split into periodic tasks",
    "9. Clear fault and switch back to RUN mode",
    "10. Monitor scan time for 24 hours to verify fix"
  ],

  "plc:preventionMeasures": [
    "Always set max_loop_iterations limit on FOR/WHILE loops",
    "Use periodic tasks for slow operations (file access, complex calcs)",
    "Monitor scan time during commissioning and load testing",
    "Implement watchdog reset logic in critical sections (use carefully)",
    "Avoid blocking instructions in OB1 main cycle"
  ],

  "plc:safetyWarnings": [
    {
      "severity": "WARNING",
      "warning": "Increasing watchdog timeout can mask serious program issues",
      "consequence": "May allow runaway programs to continue operating unsafely"
    }
  ],

  "plc:safetyLevel": "warning",
  "plc:status": "validated",

  "schema:provider": {
    "@type": "plctutor:KnowledgeSource",
    "plc:sourceTier": "vendor_manual",
    "schema:url": "https://support.industry.siemens.com/cs/document/109746530",
    "schema:author": "Siemens AG",
    "schema:datePublished": "2024-06-01T00:00:00Z"
  },

  "schema:dateCreated": "2025-12-09T00:00:00Z",
  "schema:dateModified": "2025-12-09T00:00:00Z"
}
```

### Example 4: Procedure Atom (S7-1200 Initial Startup)

```json
{
  "@context": "https://plctutor.schema.org/context/v0.1",
  "@id": "plc:siemens:s7-1200-startup-procedure",
  "@type": ["schema:Thing", "plctutor:PLCAtom"],
  "atom_version": "0.1",
  "atom_type": "procedure",

  "schema:name": "Siemens S7-1200 Initial Startup and Commissioning",
  "schema:description": "Complete procedure for commissioning a new Siemens S7-1200 PLC from unboxing to first program download. Includes hardware installation, power-up, network configuration, and verification.",

  "plc:vendor": "siemens",
  "plc:platform": "s7-1200",
  "plc:difficulty": "beginner",

  "plc:procedureCategory": "commissioning",
  "plc:estimatedTime": "45-60 minutes",

  "plc:requiredTools": [
    "24VDC power supply (minimum 2A for CPU 1212C)",
    "Ethernet cable (Cat5e or better)",
    "Computer with TIA Portal v17 or later installed",
    "Small flathead screwdriver (for terminal blocks)",
    "Multimeter (for voltage verification)",
    "Lockout/tagout equipment"
  ],

  "plc:prerequisites": [
    "TIA Portal software installed and licensed",
    "Network subnet planned (default: 192.168.0.1/24)",
    "Power supply capacity verified (check CPU datasheet)",
    "DIN rail mounted and grounded"
  ],

  "plc:safetyWarnings": [
    {
      "severity": "DANGER",
      "warning": "Apply lockout/tagout to power source before wiring",
      "consequence": "Risk of electric shock or short circuit"
    },
    {
      "severity": "CAUTION",
      "warning": "Verify 24VDC polarity before applying power",
      "consequence": "Reverse polarity will damage PLC (not protected)"
    }
  ],

  "plc:steps": [
    {
      "stepNumber": 1,
      "action": "Mount S7-1200 CPU on DIN rail and verify secure click",
      "expectedResult": "CPU firmly mounted, no movement when pulled",
      "troubleshooting": "If loose, check DIN rail profile (35mm standard)"
    },
    {
      "stepNumber": 2,
      "action": "Connect 24VDC power: L+ to terminal 20, M to terminal 21",
      "expectedResult": "No power yet (still locked out)",
      "troubleshooting": "Double-check polarity with multimeter before connecting"
    },
    {
      "stepNumber": 3,
      "action": "Connect Ethernet cable to X1 port on CPU",
      "expectedResult": "Cable clicks into RJ45 jack securely",
      "troubleshooting": "Ensure Cat5e or better, max length 100m to switch"
    },
    {
      "stepNumber": 4,
      "action": "Remove lockout/tagout and apply 24VDC power",
      "expectedResult": "RUN LED blinks green, MAINT LED solid yellow (factory state)",
      "troubleshooting": "If no LEDs: check power supply voltage (should be 24VDC ±10%)"
    },
    {
      "stepNumber": 5,
      "action": "Open TIA Portal, create new project, add S7-1200 CPU",
      "expectedResult": "Project created, CPU added to hardware configuration",
      "troubleshooting": "Select exact CPU model (e.g., CPU 1212C DC/DC/DC)"
    },
    {
      "stepNumber": 6,
      "action": "Assign IP address in TIA Portal (e.g., 192.168.0.10)",
      "expectedResult": "IP configuration saved in project",
      "troubleshooting": "Ensure IP is in same subnet as programming computer"
    },
    {
      "stepNumber": 7,
      "action": "Go online and download IP address to PLC",
      "expectedResult": "TIA Portal finds PLC, downloads IP successfully",
      "troubleshooting": "If not found, use 'Accessible devices' scan in TIA Portal"
    },
    {
      "stepNumber": 8,
      "action": "Download empty project to PLC",
      "expectedResult": "Download completes, PLC switches to RUN mode (green LED solid)",
      "troubleshooting": "If STOP mode: check for hardware config mismatch"
    },
    {
      "stepNumber": 9,
      "action": "Verify diagnostics: CPU Properties → Diagnostics → General",
      "expectedResult": "No faults, cycle time <5ms, all status green",
      "troubleshooting": "Clear diagnostic buffer if any historical faults present"
    },
    {
      "stepNumber": 10,
      "action": "Test I/O: Connect test switch to DI0, monitor in TIA Portal",
      "expectedResult": "DI0 changes state when switch toggled",
      "troubleshooting": "Check wiring polarity (1L+ input needs sourcing signal)"
    }
  ],

  "plc:verificationChecklist": [
    "Power supply voltage measured: 24VDC ±10%",
    "All LEDs in expected state (RUN=green, MAINT=off)",
    "IP address pingable from programming PC",
    "TIA Portal shows 'Connected' status",
    "Scan time <10ms with empty program",
    "At least one DI and one DO tested and working",
    "Project saved and backed up",
    "CPU firmware version documented"
  ],

  "plc:status": "tested_on_hardware",

  "schema:provider": {
    "@type": "plctutor:KnowledgeSource",
    "plc:sourceTier": "vendor_manual",
    "schema:url": "https://support.industry.siemens.com/cs/document/109742700",
    "schema:author": "Siemens AG",
    "schema:datePublished": "2024-09-01T00:00:00Z"
  },

  "schema:dateCreated": "2025-12-09T00:00:00Z",
  "schema:dateModified": "2025-12-09T00:00:00Z"
}
```

---

## Part 5: Vector Database Schema (Supabase + pgvector)

### Table Structure

```sql
-- PLC atoms table (extends knowledge atoms pattern)
CREATE TABLE plc_atoms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  atom_id TEXT UNIQUE NOT NULL,  -- e.g., "plc:ab:motor-start-stop"
  atom_type TEXT NOT NULL CHECK (atom_type IN ('concept', 'pattern', 'fault', 'procedure')),

  -- Core content
  name TEXT NOT NULL,
  description TEXT NOT NULL,

  -- Vendor/platform
  vendor TEXT NOT NULL,
  platform TEXT,
  programming_languages TEXT[],
  difficulty TEXT CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')),

  -- Pattern-specific fields (nullable for non-pattern atoms)
  pattern_category TEXT,
  inputs JSONB,  -- Array of input tag definitions
  outputs JSONB,  -- Array of output tag definitions
  internal_tags JSONB,
  logic_description TEXT,
  ladder_logic_steps TEXT[],
  structured_text_code TEXT,

  -- Fault-specific fields
  fault_code TEXT,
  fault_category TEXT,
  symptoms TEXT[],
  probable_causes JSONB,
  resolution_steps TEXT[],
  prevention_measures TEXT[],

  -- Procedure-specific fields
  procedure_category TEXT,
  estimated_time TEXT,
  required_tools TEXT[],
  prerequisites TEXT[],
  steps JSONB,  -- Array of step objects
  verification_checklist TEXT[],

  -- Concept-specific fields
  concept_category TEXT,
  learning_objectives TEXT[],
  common_mistakes JSONB,

  -- Safety
  safety_requirements TEXT[],
  safety_level TEXT,
  safety_warnings JSONB,

  -- Quality & validation
  status TEXT NOT NULL CHECK (status IN ('draft', 'validated', 'tested_on_hardware', 'certified')),
  prerequisite_atoms TEXT[],

  -- Source
  source_tier TEXT,
  source_url TEXT,
  source_author TEXT,

  -- Vector embedding
  embedding vector(3072),  -- text-embedding-3-large

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Full JSON for export
  full_json JSONB NOT NULL
);

-- Indexes for fast querying
CREATE INDEX idx_plc_atoms_atom_type ON plc_atoms(atom_type);
CREATE INDEX idx_plc_atoms_vendor ON plc_atoms(vendor);
CREATE INDEX idx_plc_atoms_platform ON plc_atoms(platform);
CREATE INDEX idx_plc_atoms_difficulty ON plc_atoms(difficulty);
CREATE INDEX idx_plc_atoms_status ON plc_atoms(status);
CREATE INDEX idx_plc_atoms_pattern_category ON plc_atoms(pattern_category);
CREATE INDEX idx_plc_atoms_fault_code ON plc_atoms(fault_code);

-- HNSW index for vector similarity search
CREATE INDEX idx_plc_atoms_embedding ON plc_atoms
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Text search index
CREATE INDEX idx_plc_atoms_name_description ON plc_atoms
USING GIN (to_tsvector('english', name || ' ' || description));
```

### Query Examples

```sql
-- Find motor control patterns for Allen-Bradley
SELECT atom_id, name, difficulty
FROM plc_atoms
WHERE atom_type = 'pattern'
  AND pattern_category = 'motor_control'
  AND vendor = 'allen_bradley'
  AND status IN ('validated', 'tested_on_hardware', 'certified')
ORDER BY difficulty;

-- Semantic search for "timer on delay" (using vector similarity)
SELECT atom_id, name, 1 - (embedding <=> query_embedding) AS similarity
FROM plc_atoms
WHERE atom_type = 'concept'
  AND vendor IN ('generic', 'siemens')
ORDER BY embedding <=> query_embedding
LIMIT 10;

-- Find all faults related to communication issues
SELECT fault_code, name, resolution_steps
FROM plc_atoms
WHERE atom_type = 'fault'
  AND fault_category = 'communication'
  AND vendor = 'siemens'
  AND platform LIKE 's7-%';

-- Get learning path (all prerequisite atoms for a pattern)
WITH RECURSIVE prereq_chain AS (
  -- Base case: start with target atom
  SELECT atom_id, name, prerequisite_atoms, 1 AS depth
  FROM plc_atoms
  WHERE atom_id = 'plc:ab:motor-start-stop-seal'

  UNION ALL

  -- Recursive case: find prerequisites
  SELECT p.atom_id, p.name, p.prerequisite_atoms, pc.depth + 1
  FROM plc_atoms p
  JOIN prereq_chain pc ON p.atom_id = ANY(pc.prerequisite_atoms)
  WHERE pc.depth < 5  -- Prevent infinite loops
)
SELECT DISTINCT atom_id, name, depth
FROM prereq_chain
ORDER BY depth, name;
```

---

## Part 6: LLM4PLC Integration (Autonomous Code Generation)

### Research Foundation

Based on UC Irvine's LLM4PLC research (2024):
- **Spec → Code → Verify** loop
- Use LLMs to generate ladder logic from natural language
- Use computer-use to verify in actual PLC software

### Atom-Driven Code Generation

```python
# Agent 7: PLC Code Generator Agent
# Uses pattern atoms as templates for code generation

def generate_plc_code(user_spec: str, vendor: str, platform: str):
    """
    Generate PLC code from natural language specification.

    Process:
    1. Parse user spec into requirements
    2. Find relevant pattern atoms (vector search)
    3. Combine patterns into solution
    4. Generate vendor-specific code
    5. Verify in PLC software (computer-use)
    """

    # Step 1: Semantic search for relevant patterns
    query_embedding = embed_text(user_spec)
    relevant_atoms = vector_search(
        query_embedding,
        filters={
            "atom_type": "pattern",
            "vendor": [vendor, "generic"],
            "status": ["validated", "tested_on_hardware"]
        },
        top_k=5
    )

    # Step 2: Extract I/O requirements from spec
    required_inputs = extract_inputs_from_spec(user_spec)
    required_outputs = extract_outputs_from_spec(user_spec)

    # Step 3: Compose solution from patterns
    solution = compose_patterns(
        patterns=relevant_atoms,
        required_inputs=required_inputs,
        required_outputs=required_outputs
    )

    # Step 4: Generate vendor-specific code
    if vendor == "allen_bradley":
        code = generate_ab_ladder_logic(solution)
    elif vendor == "siemens":
        code = generate_siemens_ladder_logic(solution)

    # Step 5: Verify using computer-use (Cole Medin pattern)
    verification = verify_code_in_plc_software(
        code=code,
        vendor=vendor,
        platform=platform,
        test_cases=extract_test_cases(user_spec)
    )

    return {
        "code": code,
        "patterns_used": [a["atom_id"] for a in relevant_atoms],
        "verification": verification,
        "confidence": calculate_confidence(relevant_atoms, verification)
    }
```

---

## Part 7: Validation Pipeline (PLC-Specific)

```python
# 6-stage validation pipeline for PLC atoms

def validate_plc_atom(atom: dict) -> ValidationResult:
    """
    Validate PLC atom before insertion into database.
    """

    # Stage 1: JSON Schema validation
    validate_against_schema(atom, PLC_ATOM_SCHEMA)

    # Stage 2: Vendor/platform validation
    if atom["plc:vendor"] not in APPROVED_VENDORS:
        raise InvalidVendorError(f"Unknown vendor: {atom['plc:vendor']}")

    # Stage 3: Safety validation
    if atom.get("plc:safetyLevel") in ["danger", "sil_rated"]:
        if not atom.get("plc:safetyRequirements"):
            raise MissingSafetyRequirementsError("High safety atoms must have requirements")

    # Stage 4: Code validation (for pattern atoms)
    if atom["atom_type"] == "pattern":
        if not atom.get("plc:logicDescription"):
            raise MissingLogicDescriptionError("Patterns must have logic description")

        # Validate I/O definitions
        validate_io_tags(atom.get("plc:inputs", []))
        validate_io_tags(atom.get("plc:outputs", []))

    # Stage 5: Prerequisite chain validation
    if atom.get("plc:prerequisiteAtoms"):
        for prereq_id in atom["plc:prerequisiteAtoms"]:
            if not atom_exists(prereq_id):
                raise PrerequisiteNotFoundError(f"Prerequisite not found: {prereq_id}")

    # Stage 6: Hardware testing requirement
    if atom["plc:status"] == "tested_on_hardware":
        if not atom.get("plc:codeExample", {}).get("testPlatform"):
            raise MissingTestPlatformError("Hardware-tested atoms must document test platform")

    return ValidationResult(valid=True, atom_id=atom["@id"])
```

---

## Part 8: Implementation Roadmap

### Week 1: Foundation (Current Week)
- [x] Create PLC_ATOM_SPEC.md (this document)
- [ ] Create plc/ directory structure
- [ ] Create 15 PLC agent skeleton classes
- [ ] Create docs/PLC_BUSINESS_MODEL.md
- [ ] Create 10 example atoms (3 patterns, 3 concepts, 2 faults, 2 procedures)

### Week 2: Validation & Testing
- [ ] Implement validation pipeline
- [ ] Test atoms on Siemens S7-1200 hardware
- [ ] Create validation test suite
- [ ] Document testing procedures

### Week 3: Agent Implementation (Product & Engineering)
- [ ] Agent 1: PLC Textbook Scraper
- [ ] Agent 2: Vendor Manual Scraper
- [ ] Agent 3: Atom Validator
- [ ] Agent 4: Atom Publisher
- [ ] Agent 5: Duplicate Detector

### Week 4: Agent Implementation (Content)
- [ ] Agent 6: Tutorial Writer
- [ ] Agent 7: Code Generator (LLM4PLC)
- [ ] Agent 8: Video Producer
- [ ] Agent 9: Social Media Manager

---

## Part 9: Success Metrics

### Data Quality Metrics
- **Atom Coverage:** 1,000+ atoms by Month 3 (500 patterns, 300 concepts, 100 faults, 100 procedures)
- **Vendor Coverage:** 3+ vendors (Allen-Bradley, Siemens, CODESYS)
- **Validation Rate:** 80%+ of atoms validated against actual hardware
- **Safety Compliance:** 100% of high-safety atoms have documented requirements

### User Engagement Metrics
- **Free Users:** 500 by Month 3 (YouTube funnel)
- **Paying Subscribers:** 50 by Month 3 (10% conversion)
- **Code Generation Success Rate:** 70%+ of generated code compiles without errors
- **User Satisfaction:** 4.5+ stars average rating

### Business Metrics
- **MRR:** $1,450 by Month 3
- **CAC:** <$50 (organic + YouTube)
- **LTV:** $500+ (12-month retention target)
- **Autonomous Code Usage:** 10+ customers by Month 6

---

## Conclusion

This PLC Atom Specification v0.1 extends the proven Knowledge Atom Standard v1.0 to the PLC programming education domain.

**Built on:**
- Industrial Maintenance Knowledge Atom Standard v1.0
- IEC 61131-3 (PLC programming languages)
- IEC 62061 (Functional safety)
- LLM4PLC research (UC Irvine)
- Cole Medin computer-use patterns

**Enables:**
- Structured PLC knowledge capture
- Autonomous PLC code generation
- Learning path construction
- Multi-vendor support
- Safety-critical validation

**Next Steps:**
1. Create plc/ repository structure
2. Implement 15 agent skeletons
3. Create 10 example atoms
4. Test on S7-1200 hardware
5. Launch PLC Tutor Beta (Week 4)

---

**Status:** v0.1 (Draft)
**Last Updated:** 2025-12-09
**Next Review:** 2025-12-16 (after Week 1 implementation)
