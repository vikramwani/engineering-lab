# Human-in-the-Loop (HITL) Escalation Contract

## Overview

The Agent Alignment Framework provides a formalized, deterministic contract for Human-in-the-Loop (HITL) escalation when automated multi-agent evaluation requires human review. This contract is designed to be domain-agnostic, serializable, and integration-ready without making assumptions about UI, persistence, or workflow systems.

## Key Principles

- **Pure, Deterministic Logic**: Same inputs always produce identical outputs with no side effects
- **Schema-Driven Models**: Structured, typed data models for reliable integration
- **Domain Agnostic**: No business logic or domain-specific assumptions
- **Integration Ready**: Fully serializable for any downstream review system
- **Backward Compatible**: Works seamlessly with existing evaluation pipeline

## Escalation Contract

### When Escalation Occurs

The HITL escalation contract is triggered **only** when:

1. `EvaluationResult.requires_human_review == True`
2. The alignment state indicates `HARD_DISAGREEMENT`

As defined in Task 2, only `HARD_DISAGREEMENT` triggers human review escalation. Other alignment states (`FULL_ALIGNMENT`, `SOFT_DISAGREEMENT`, `INSUFFICIENT_SIGNAL`) do not trigger escalation.

### Escalation Reasons

```python
class HITLEscalationReason(str, Enum):
    HARD_DISAGREEMENT = "hard_disagreement"      # Agents disagree on primary decision
    LOW_CONFIDENCE = "low_confidence"            # Insufficient confidence levels
    INCONSISTENT_EVIDENCE = "inconsistent_evidence"  # Evidence quality issues
    CUSTOM_RULE = "custom_rule"                  # User-defined escalation rules
```

**Current Implementation**: Only `HARD_DISAGREEMENT` is actively triggered by the alignment engine.

### HITL Request Structure

```python
class HITLRequest(BaseModel):
    request_id: str                              # Unique escalation identifier
    task_id: str                                 # Original evaluation task ID
    alignment_state: str                         # Alignment state that triggered escalation
    alignment_score: float                       # Deterministic alignment score [0.0, 1.0]
    escalation_reason: HITLEscalationReason     # Primary escalation reason
    summary: str                                 # Human-readable escalation explanation
    
    # Complete agent context
    agent_decisions: List[AgentDecision]         # All agent decisions (not duplicated)
    dissenting_agents: List[str]                 # Names of dissenting agents
    
    # Temporal metadata
    created_at: datetime                         # UTC timestamp of escalation
    
    # Rich metadata for downstream systems
    metadata: Dict[str, Any]                     # Structured escalation metadata
```

## Usage

### Basic Escalation Check

```python
from agent_alignment.core.hitl import build_hitl_request

# After multi-agent evaluation
evaluation_result = evaluator.evaluate(task)

# Check if HITL escalation is needed
hitl_request = build_hitl_request(evaluation_result, evaluation_result.alignment_summary)

if hitl_request is not None:
    # Human review required - send to your review system
    send_to_review_system(hitl_request)
else:
    # No human review needed - proceed with automated decision
    process_automated_decision(evaluation_result)
```

### Integration with MultiAgentEvaluator

```python
# The evaluator provides a convenience method
evaluator = MultiAgentEvaluator(agents=agents, enable_hitl=True)
evaluation_result = evaluator.evaluate(task)

# Create HITL request if needed
hitl_request = evaluator.create_hitl_request(evaluation_result)
```

## Escalation Semantics

### Information Included

The HITL request includes complete context for human reviewers:

- **Alignment Analysis**: State, score, confidence metrics, disagreement areas
- **Agent Decisions**: All agent decisions with rationale and evidence
- **Dissenting Agents**: Specific agents with minority positions
- **Temporal Context**: When escalation occurred
- **Rich Metadata**: Processing time, confidence distribution, consensus strength

### Information Intentionally Excluded

The contract excludes workflow and UI concerns:

- UI preferences or layout instructions
- Workflow state or routing information
- Reviewer assignments or notifications
- Persistence or storage details
- Async callbacks or completion handlers

### Deterministic Behavior

The escalation contract guarantees deterministic behavior:

```python
# Same inputs always produce identical outputs
result1 = build_hitl_request(evaluation_result, alignment_summary)
result2 = build_hitl_request(evaluation_result, alignment_summary)

assert result1.request_id == result2.request_id  # Deterministic ID generation
assert result1.summary == result2.summary        # Deterministic summary
assert result1.escalation_reason == result2.escalation_reason  # Deterministic reason
```

## Integration Patterns

### Queue-Based Systems

```python
import json
from your_queue_system import send_message

hitl_request = build_hitl_request(evaluation_result, alignment_summary)
if hitl_request:
    message = {
        "type": "hitl_escalation",
        "payload": json.loads(hitl_request.model_dump_json()),
        "routing_key": f"review.{hitl_request.escalation_reason.value}"
    }
    send_message("hitl-queue", message)
```

### REST API Integration

```python
import requests

hitl_request = build_hitl_request(evaluation_result, alignment_summary)
if hitl_request:
    response = requests.post(
        "https://review-system.com/api/escalations",
        json=hitl_request.model_dump(),
        headers={"Content-Type": "application/json"}
    )
```

### Database Storage

```python
from your_orm import HITLEscalation

hitl_request = build_hitl_request(evaluation_result, alignment_summary)
if hitl_request:
    escalation = HITLEscalation(
        request_id=hitl_request.request_id,
        task_id=hitl_request.task_id,
        escalation_data=hitl_request.model_dump(),
        status="pending",
        created_at=hitl_request.created_at
    )
    escalation.save()
```

### Webhook Integration

```python
import requests

def send_webhook(hitl_request: HITLRequest):
    webhook_payload = {
        "event": "hitl_escalation_required",
        "escalation": hitl_request.model_dump(),
        "timestamp": hitl_request.created_at.isoformat()
    }
    
    requests.post(
        "https://your-system.com/webhooks/hitl",
        json=webhook_payload,
        headers={"X-Event-Type": "hitl_escalation"}
    )
```

## Validation and Testing

### Contract Validation

```python
from agent_alignment.core.hitl import validate_hitl_request

# Validate HITL request structure
is_valid = validate_hitl_request(hitl_request)
assert is_valid, "HITL request must be valid"
```

### Escalation Semantics

```python
from agent_alignment.core.hitl import get_escalation_semantics

# Get machine-readable contract semantics
semantics = get_escalation_semantics()
print(f"Contract version: {semantics['contract_version']}")
print(f"Deterministic: {semantics['deterministic']}")
print(f"Side effects: {semantics['side_effects']}")
```

### Testing Escalation Logic

```python
# Test that only HARD_DISAGREEMENT triggers escalation
from agent_alignment.core.models import AlignmentState

test_cases = [
    (AlignmentState.FULL_ALIGNMENT, False),      # Should not escalate
    (AlignmentState.SOFT_DISAGREEMENT, False),   # Should not escalate  
    (AlignmentState.INSUFFICIENT_SIGNAL, False), # Should not escalate
    (AlignmentState.HARD_DISAGREEMENT, True),    # Should escalate
]

for state, should_escalate in test_cases:
    # Create test evaluation result with given state
    evaluation_result = create_test_result(alignment_state=state)
    hitl_request = build_hitl_request(evaluation_result, evaluation_result.alignment_summary)
    
    if should_escalate:
        assert hitl_request is not None, f"Expected escalation for {state}"
    else:
        assert hitl_request is None, f"Unexpected escalation for {state}"
```

## Best Practices

### 1. Always Check for Escalation

```python
# Always check after evaluation
evaluation_result = evaluator.evaluate(task)
hitl_request = build_hitl_request(evaluation_result, evaluation_result.alignment_summary)

if hitl_request:
    handle_human_review(hitl_request)
else:
    handle_automated_decision(evaluation_result)
```

### 2. Preserve Complete Context

```python
# The HITL request contains complete agent context
for agent_decision in hitl_request.agent_decisions:
    print(f"Agent: {agent_decision.agent_name}")
    print(f"Decision: {agent_decision.decision_value}")
    print(f"Confidence: {agent_decision.confidence}")
    print(f"Rationale: {agent_decision.rationale}")
    print(f"Evidence: {agent_decision.evidence}")
```

### 3. Use Structured Metadata

```python
# Rich metadata is available for downstream processing
metadata = hitl_request.metadata
processing_time = metadata["processing_time_ms"]
confidence_spread = metadata["confidence_spread"]
disagreement_areas = metadata["disagreement_areas"]

# Route based on escalation characteristics
if "primary_decision" in disagreement_areas:
    route_to_senior_reviewer(hitl_request)
elif confidence_spread > 0.3:
    route_to_confidence_specialist(hitl_request)
```

### 4. Handle Serialization Properly

```python
import json
from datetime import datetime

# Serialize for storage/transmission
json_data = hitl_request.model_dump_json()

# Deserialize from storage/transmission  
loaded_data = json.loads(json_data)
restored_request = HITLRequest(**loaded_data)

# Datetime fields are properly handled
assert isinstance(restored_request.created_at, datetime)
```

## Extensibility

### Custom Escalation Reasons

While the current implementation only triggers `HARD_DISAGREEMENT`, the contract supports extension:

```python
# Future extension example (not currently implemented)
def custom_escalation_check(evaluation_result: EvaluationResult) -> bool:
    # Custom business logic for escalation
    if evaluation_result.confidence < 0.3:
        return True
    if "high_risk" in evaluation_result.metadata:
        return True
    return False

# This would require extending the build_hitl_request function
```

### Additional Metadata

```python
# Extend metadata for domain-specific needs
hitl_request.metadata.update({
    "business_impact": "high",
    "regulatory_requirements": ["SOX", "PCI-DSS"],
    "stakeholder_groups": ["security", "compliance", "operations"]
})
```

## Troubleshooting

### Common Issues

1. **No Escalation When Expected**
   - Verify `evaluation_result.requires_human_review == True`
   - Check that alignment state is `HARD_DISAGREEMENT`
   - Ensure agents actually disagree on `decision_value`

2. **Unexpected Escalation**
   - Review alignment thresholds in `AlignmentThresholds`
   - Check agent decision agreement logic
   - Verify confidence spread calculations

3. **Serialization Errors**
   - Ensure all custom data in `metadata` is JSON-serializable
   - Check datetime handling for `created_at` field
   - Validate agent decision data types

### Debugging

```python
# Enable debug logging
import logging
logging.getLogger("agent_alignment.core.hitl").setLevel(logging.DEBUG)

# Check escalation logic step by step
print(f"Requires review: {evaluation_result.requires_human_review}")
print(f"Alignment state: {evaluation_result.alignment_summary.state}")
print(f"Decision agreement: {evaluation_result.alignment_summary.decision_agreement}")

hitl_request = build_hitl_request(evaluation_result, evaluation_result.alignment_summary)
print(f"HITL request created: {hitl_request is not None}")
```

## Migration and Compatibility

The HITL escalation contract is designed for backward compatibility:

- Existing evaluation pipelines continue to work unchanged
- HITL functionality is opt-in via `enable_hitl=True`
- Legacy `HumanReviewRequest` models are still supported (deprecated)
- No breaking changes to public APIs

## Summary

The HITL escalation contract provides a robust, deterministic foundation for human review integration. It focuses purely on escalation signal generation while remaining agnostic to downstream review systems, UI implementations, and workflow management. This design enables flexible integration with any review system while maintaining the framework's core principles of determinism, domain-agnosticism, and extensibility.