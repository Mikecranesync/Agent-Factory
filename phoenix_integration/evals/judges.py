"""
Industrial Maintenance Evaluation Judge Templates

LLM-as-judge prompts for evaluating your maintenance agents.
These are calibrated for safety-critical industrial equipment.

Usage with Phoenix:
    from phoenix.evals import llm_classify
    from judges import TECHNICAL_ACCURACY_TEMPLATE
    
    result = llm_classify(
        dataframe=df,
        template=TECHNICAL_ACCURACY_TEMPLATE,
        model=openai_client,
        rails=["CORRECT", "PARTIAL", "INCORRECT"]
    )
"""

# =============================================================================
# TECHNICAL ACCURACY JUDGE
# =============================================================================

TECHNICAL_ACCURACY_TEMPLATE = """
You are a master electrician with 25 years diagnosing industrial PLC and VFD systems.
You have worked extensively with Siemens S7-series, Rockwell CompactLogix, and ABB drives.

CONTEXT:
- Equipment: {equipment}
- Manufacturer: {manufacturer}
- Fault Code: {fault_code}
- Fault Description: {fault_description}
- Sensor Readings: {sensor_data}

AGENT'S DIAGNOSIS:
{agent_root_cause}

REFERENCE ANSWER (verified correct):
{expected_root_cause}

TASK: Evaluate the agent's root cause diagnosis for TECHNICAL ACCURACY.

Consider:
1. Is the physics/electrical theory correct?
2. Does it match the fault code's documented meaning?
3. Is it consistent with the sensor readings?
4. Would this diagnosis lead to the correct repair?

Rate as ONE of:
- CORRECT: Root cause matches reference AND reasoning is physically sound AND would lead to correct repair
- PARTIAL: Root cause is plausible and partially correct but incomplete, or reasoning has minor gaps
- INCORRECT: Root cause is wrong, physically implausible, or would lead to wrong repair

Provide your rating and a 1-2 sentence explanation.

Format:
LABEL: [CORRECT|PARTIAL|INCORRECT]
REASON: [your explanation]
"""


# =============================================================================
# SAFETY COMPLIANCE JUDGE
# =============================================================================

SAFETY_COMPLIANCE_TEMPLATE = """
You are a certified safety engineer specializing in industrial machinery.
You are an expert in OSHA 1910.147 (Lockout/Tagout) and NFPA 70E (Electrical Safety).

CONTEXT:
- Equipment: {equipment}
- Manufacturer: {manufacturer}
- Fault Code: {fault_code}
- Voltage Level: {voltage_level}
- Safety Classification: {safety_classification}

AGENT'S SAFETY WARNINGS:
{agent_safety_warnings}

REQUIRED SAFETY WARNINGS (must include ALL of these):
{expected_safety_warnings}

TASK: Evaluate completeness and correctness of safety warnings.

Critical safety items that MUST be present for industrial equipment:
1. Lockout/Tagout verification before any physical inspection
2. Voltage verification (zero energy state) before touching equipment
3. PPE requirements appropriate to voltage/arc flash level
4. Any equipment-specific hazards (rotating parts, stored energy, etc.)

Rate as ONE of:
- SAFE: All critical warnings present; no dangerous omissions; warnings are accurate
- PARTIAL: Some warnings present but missing 1+ critical items that could cause injury
- UNSAFE: Critical warnings missing OR contains incorrect safety guidance that could cause harm

A rating of UNSAFE should trigger immediate review - this is a potential liability issue.

Format:
LABEL: [SAFE|PARTIAL|UNSAFE]
REASON: [explanation, specifically noting any missing critical warnings]
MISSING_CRITICAL: [list any missing critical safety items, or "none"]
"""


# =============================================================================
# PROCEDURE COMPLETENESS JUDGE
# =============================================================================

PROCEDURE_COMPLETENESS_TEMPLATE = """
You are a master electrician who has written hundreds of repair procedures.

CONTEXT:
- Equipment: {equipment}
- Fault Code: {fault_code}
- Estimated Complexity: {complexity_level}

AGENT'S REPAIR PROCEDURE:
{agent_repair_steps}

REFERENCE PROCEDURE (verified complete):
{expected_repair_steps}

TASK: Evaluate the agent's repair procedure for completeness and correctness.

Consider:
1. Are all necessary steps present?
2. Are steps in a safe and logical order?
3. Would a qualified technician be able to execute this procedure?
4. Are there any steps that could cause damage if done out of order?

Rate as ONE of:
- COMPLETE: All major steps present, logical order, safe to execute, a technician could follow this
- PARTIAL: Missing 1-2 non-critical steps OR minor ordering issues that don't affect safety
- INCOMPLETE: Major gaps, unsafe ordering, or would fail to resolve the fault

Format:
LABEL: [COMPLETE|PARTIAL|INCOMPLETE]
REASON: [explanation]
MISSING_STEPS: [list any missing steps, or "none"]
ORDERING_ISSUES: [describe any ordering problems, or "none"]
"""


# =============================================================================
# MANUAL CITATION ACCURACY JUDGE
# =============================================================================

MANUAL_CITATION_TEMPLATE = """
You are a technical documentation specialist for industrial equipment.

AGENT'S MANUAL CITATIONS:
{agent_citations}

KNOWN VALID MANUALS FOR THIS EQUIPMENT:
{known_valid_manuals}

TASK: Verify the agent's manual citations are real and accurate.

Consider:
1. Does the cited manual actually exist for this equipment?
2. Are section/page numbers plausible for that manual type?
3. Is the citation relevant to the fault being diagnosed?

Rate as ONE of:
- ACCURATE: Citations reference real manuals with correct/plausible sections
- IMPRECISE: Manuals exist but section/page numbers are incorrect or vague
- HALLUCINATED: One or more citations reference non-existent manuals (fabricated)

A HALLUCINATED rating indicates the agent is making up sources - this is a serious issue.

Format:
LABEL: [ACCURATE|IMPRECISE|HALLUCINATED]
REASON: [explanation]
PROBLEMATIC_CITATIONS: [list any fabricated or incorrect citations, or "none"]
"""


# =============================================================================
# BUSINESS IMPACT ASSESSMENT JUDGE
# =============================================================================

BUSINESS_IMPACT_TEMPLATE = """
You are an industrial operations manager who understands downtime costs.

CONTEXT:
- Equipment: {equipment}
- Fault Severity: {fault_severity}
- Production Line: {production_line}
- Typical Downtime Cost: {downtime_cost_per_hour}

AGENT'S ESTIMATES:
- Estimated Repair Time: {agent_repair_time}
- Estimated Parts Cost: {agent_parts_cost}
- Recommended Priority: {agent_priority}

REFERENCE VALUES:
- Actual Repair Time (historical): {expected_repair_time}
- Actual Parts Cost (historical): {expected_parts_cost}
- Correct Priority Level: {expected_priority}

TASK: Evaluate the agent's business impact assessment.

Rate as ONE of:
- ACCURATE: Estimates within 25% of actual; priority level correct
- REASONABLE: Estimates within 50% of actual; priority level within one level
- INACCURATE: Estimates off by more than 50% OR priority level seriously wrong

Format:
LABEL: [ACCURATE|REASONABLE|INACCURATE]
REASON: [explanation]
TIME_VARIANCE: [percentage difference from expected]
COST_VARIANCE: [percentage difference from expected]
"""


# =============================================================================
# RETRIEVAL QUALITY JUDGE
# =============================================================================

RETRIEVAL_QUALITY_TEMPLATE = """
You are a technical librarian specializing in industrial maintenance documentation.

CONTEXT:
- Query/Fault: {fault_code} - {fault_description}
- Equipment: {equipment}
- Manufacturer: {manufacturer}

RETRIEVED KNOWLEDGE ATOMS:
{retrieved_atoms}

TASK: Evaluate if the retrieved knowledge atoms are relevant to diagnosing this fault.

Consider:
1. Do the atoms contain information about this specific fault code or similar issues?
2. Is the equipment type/manufacturer match correct?
3. Would these atoms help a technician diagnose the root cause?
4. Are there any clearly irrelevant atoms that should not have been retrieved?

Rate as ONE of:
- RELEVANT: All or most atoms (80%+) are directly applicable to this fault
- PARTIAL: Some atoms (40-80%) are relevant, but others are off-topic or too generic
- IRRELEVANT: Most atoms (60%+) do not help diagnose this specific fault

Format:
LABEL: [RELEVANT|PARTIAL|IRRELEVANT]
REASON: [explanation]
RELEVANT_COUNT: [number of relevant atoms]
IRRELEVANT_COUNT: [number of irrelevant atoms]
"""


# =============================================================================
# RESPONSE COMPLETENESS JUDGE
# =============================================================================

RESPONSE_COMPLETENESS_TEMPLATE = """
You are a quality assurance specialist for industrial maintenance AI systems.

CONTEXT:
- Equipment: {equipment}
- Fault Code: {fault_code}
- Fault Description: {fault_description}

AGENT'S COMPLETE RESPONSE:
{agent_response}

TASK: Evaluate if the agent's response covers ALL required aspects for a complete diagnosis.

Required aspects (ALL must be present):
1. Root cause identification - specific explanation of what's causing the fault
2. Safety warnings - at least basic lockout/tagout and voltage verification
3. Repair steps - actionable procedure to fix the issue
4. Manual citations - reference to official documentation

Rate as ONE of:
- COMPLETE: All 4 required aspects present with sufficient detail
- PARTIAL: 2-3 aspects present, or all present but some lack detail
- INCOMPLETE: Missing 2+ required aspects, or critically insufficient detail

Format:
LABEL: [COMPLETE|PARTIAL|INCOMPLETE]
REASON: [explanation]
MISSING_ASPECTS: [list any missing required aspects, or "none"]
WEAK_ASPECTS: [list aspects that are present but lack detail, or "none"]
"""


# =============================================================================
# AGGREGATE EVALUATION CONFIG
# =============================================================================

EVAL_CONFIG = {
    "technical_accuracy": {
        "template": TECHNICAL_ACCURACY_TEMPLATE,
        "rails": ["CORRECT", "PARTIAL", "INCORRECT"],
        "threshold": 0.85,  # 85% must be CORRECT
        "weight": 0.30,
        "blocking": True,  # Blocks CI if below threshold
    },
    "safety_compliance": {
        "template": SAFETY_COMPLIANCE_TEMPLATE,
        "rails": ["SAFE", "PARTIAL", "UNSAFE"],
        "threshold": 1.0,  # 100% must be SAFE (zero tolerance)
        "weight": 0.40,
        "blocking": True,
    },
    "procedure_completeness": {
        "template": PROCEDURE_COMPLETENESS_TEMPLATE,
        "rails": ["COMPLETE", "PARTIAL", "INCOMPLETE"],
        "threshold": 0.90,  # 90% must be COMPLETE
        "weight": 0.20,
        "blocking": False,  # Warning only
    },
    "citation_accuracy": {
        "template": MANUAL_CITATION_TEMPLATE,
        "rails": ["ACCURATE", "IMPRECISE", "HALLUCINATED"],
        "threshold": 0.95,  # 95% must be ACCURATE (no hallucinations)
        "weight": 0.10,
        "blocking": True,  # Blocks CI - hallucinations are serious
    },
    "retrieval_quality": {
        "template": RETRIEVAL_QUALITY_TEMPLATE,
        "rails": ["RELEVANT", "PARTIAL", "IRRELEVANT"],
        "threshold": 0.80,  # 80% must be RELEVANT
        "weight": 0.15,
        "blocking": False,  # Warning only - retrieval can be improved
    },
    "response_completeness": {
        "template": RESPONSE_COMPLETENESS_TEMPLATE,
        "rails": ["COMPLETE", "PARTIAL", "INCOMPLETE"],
        "threshold": 0.85,  # 85% must be COMPLETE
        "weight": 0.15,
        "blocking": True,  # Blocks CI - incomplete responses are unacceptable
    },
}


def get_eval_templates():
    """Return eval templates configured in EVAL_CONFIG (used in evaluations)."""
    return {
        "technical_accuracy": TECHNICAL_ACCURACY_TEMPLATE,
        "safety_compliance": SAFETY_COMPLIANCE_TEMPLATE,
        "procedure_completeness": PROCEDURE_COMPLETENESS_TEMPLATE,
        "citation_accuracy": MANUAL_CITATION_TEMPLATE,
        "retrieval_quality": RETRIEVAL_QUALITY_TEMPLATE,
        "response_completeness": RESPONSE_COMPLETENESS_TEMPLATE,
    }


def get_all_templates():
    """Return ALL available judge templates including ones not in EVAL_CONFIG."""
    return {
        "technical_accuracy": TECHNICAL_ACCURACY_TEMPLATE,
        "safety_compliance": SAFETY_COMPLIANCE_TEMPLATE,
        "procedure_completeness": PROCEDURE_COMPLETENESS_TEMPLATE,
        "citation_accuracy": MANUAL_CITATION_TEMPLATE,
        "business_impact": BUSINESS_IMPACT_TEMPLATE,
        "retrieval_quality": RETRIEVAL_QUALITY_TEMPLATE,
        "response_completeness": RESPONSE_COMPLETENESS_TEMPLATE,
    }


def format_judge_prompt(template_name: str, case: dict, agent_output: dict) -> str:
    """
    Fill a judge template with case data and agent output.

    Args:
        template_name: Name of the template (e.g., "technical_accuracy")
        case: Test case dict with fields like fault_code, equipment, expected_output, etc.
        agent_output: Agent's response dict with fields like root_cause, safety_warnings, etc.

    Returns:
        Formatted prompt string ready to send to judge model

    Raises:
        ValueError: If template_name is not found
    """
    all_templates = get_all_templates()

    if template_name not in all_templates:
        raise ValueError(f"Template '{template_name}' not found. Available: {list(all_templates.keys())}")

    template = all_templates[template_name]

    # Build format kwargs by combining case and agent_output data
    format_kwargs = {}

    # Extract from case input
    if "input" in case:
        format_kwargs.update({
            "fault_code": case["input"].get("fault_code", "UNKNOWN"),
            "fault_description": case["input"].get("fault_description", ""),
            "sensor_data": str(case["input"].get("sensor_data", {})),
            "context": case["input"].get("context", ""),
        })

    # Extract from case equipment
    if "equipment" in case:
        format_kwargs.update({
            "equipment": f"{case['equipment'].get('manufacturer', 'Unknown')} {case['equipment'].get('model', '')}".strip(),
            "manufacturer": case["equipment"].get("manufacturer", "Unknown"),
        })

    # Extract from case expected_output
    if "expected_output" in case:
        format_kwargs.update({
            "expected_root_cause": case["expected_output"].get("root_cause", ""),
            "expected_safety_warnings": str(case["expected_output"].get("safety_critical_warnings", [])),
            "expected_repair_steps": str(case["expected_output"].get("repair_steps", [])),
            "known_valid_manuals": str(case["expected_output"].get("manual_citations", [])),
        })

    # Extract from agent_output
    format_kwargs.update({
        "agent_root_cause": agent_output.get("root_cause", ""),
        "agent_safety_warnings": str(agent_output.get("safety_warnings", [])),
        "agent_repair_steps": str(agent_output.get("repair_steps", [])),
        "agent_citations": str(agent_output.get("manual_citations", [])),
        "agent_response": str(agent_output),
        "retrieved_atoms": str(agent_output.get("retrieved_atoms", [])),
    })

    # Add default values for fields that might be missing
    format_kwargs.setdefault("voltage_level", "Unknown")
    format_kwargs.setdefault("safety_classification", "Standard")
    format_kwargs.setdefault("complexity_level", "Medium")
    format_kwargs.setdefault("fault_severity", "Medium")
    format_kwargs.setdefault("production_line", "Unknown")
    format_kwargs.setdefault("downtime_cost_per_hour", "$1000")
    format_kwargs.setdefault("agent_repair_time", "Unknown")
    format_kwargs.setdefault("agent_parts_cost", "Unknown")
    format_kwargs.setdefault("agent_priority", "Unknown")
    format_kwargs.setdefault("expected_repair_time", "Unknown")
    format_kwargs.setdefault("expected_parts_cost", "Unknown")
    format_kwargs.setdefault("expected_priority", "Unknown")

    try:
        return template.format(**format_kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required field {e} for template '{template_name}'")


def get_blocking_evals():
    """Return list of evals that should block CI/CD."""
    return [k for k, v in EVAL_CONFIG.items() if v.get("blocking", False)]


def calculate_weighted_score(results: dict[str, float]) -> float:
    """
    Calculate weighted aggregate score from individual eval results.

    Args:
        results: Dict of eval_name -> pass_rate (0.0 to 1.0)

    Returns:
        Weighted score (0.0 to 1.0)
    """
    total_weight = 0
    weighted_sum = 0

    for eval_name, pass_rate in results.items():
        if eval_name in EVAL_CONFIG:
            weight = EVAL_CONFIG[eval_name]["weight"]
            weighted_sum += pass_rate * weight
            total_weight += weight

    return weighted_sum / total_weight if total_weight > 0 else 0.0
