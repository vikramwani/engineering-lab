# Evaluation History Storage and Management

## Overview

The Agent Alignment UI stores evaluation history to allow users to review past multi-agent evaluations, analyze patterns, and track system performance over time.

## Storage Location

**Current Implementation**: In-memory storage (for demo purposes)
- **Backend**: `evaluations_store` dictionary in `backend/main.py`
- **HITL Requests**: `hitl_requests_store` dictionary in the same file

**Production Recommendation**: Replace with persistent database storage (PostgreSQL, MongoDB, etc.)

## Data Structure

Each evaluation is stored with the following structure:

```json
{
  "task_id": "unique-task-identifier",
  "task_type": "product_compatibility",
  "synthesized_decision": "final_decision_value",
  "confidence": 0.85,
  "reasoning": "explanation_of_decision",
  "evidence": ["supporting_evidence_1", "supporting_evidence_2"],
  "agent_decisions": [
    {
      "agent_name": "advocate_agent",
      "role_type": "advocate",
      "decision_value": "compatible",
      "confidence": 0.95,
      "rationale": "detailed_reasoning",
      "evidence": ["evidence_items"],
      "metadata": {}
    }
  ],
  "alignment_summary": {
    "state": "hard_disagreement",
    "alignment_score": 0.3,
    "decision_agreement": false,
    "confidence_spread": 0.4,
    "avg_confidence": 0.8,
    "dissenting_agents": ["skeptic_agent"],
    "disagreement_areas": ["primary_decision", "confidence_levels"]
  },
  "requires_human_review": true,
  "review_reason": "Agents have fundamental disagreements",
  "request_id": "unique-request-id",
  "processing_time_ms": 15000,
  "created_at": "2026-01-12T02:30:39.936979"
}
```

## API Endpoints

### Viewing History

- **GET `/api/evaluations`** - List all evaluations
- **GET `/api/evaluations/{task_id}`** - Get specific evaluation

### Clearing History

- **DELETE `/api/evaluations`** - Clear all evaluations
- **DELETE `/api/evaluations/{task_id}`** - Delete specific evaluation

### HITL Requests

- **GET `/api/hitl/requests`** - List all HITL requests
- **DELETE `/api/hitl/requests`** - Clear all HITL requests
- **DELETE `/api/hitl/requests/{request_id}`** - Delete specific HITL request

## Frontend Interface

### History Page (`/history`)

The History page provides a comprehensive interface for managing evaluation history:

**Features:**
- **View Evaluations**: Browse all past evaluations with filtering and pagination
- **Search & Filter**: Filter by task type, alignment state, or search terms
- **Individual Actions**: View details, export JSON, or delete specific evaluations
- **Bulk Actions**: Clear all evaluation history with confirmation dialog

**Clear History Button:**
- Located in the top-right corner of the History page
- Shows confirmation dialog before clearing
- Disabled when no evaluations exist
- Shows loading state during operation

**Individual Delete Buttons:**
- Available on each evaluation card
- Immediately removes the evaluation
- Updates the list in real-time

## Data Persistence Notes

**Current Limitations:**
- Data is lost when backend restarts
- No backup or recovery mechanism
- Limited to available memory

**Production Recommendations:**
1. **Database Integration**: Use PostgreSQL or MongoDB for persistent storage
2. **Data Retention Policies**: Implement automatic cleanup of old evaluations
3. **Backup Strategy**: Regular backups of evaluation history
4. **Archiving**: Move old evaluations to archive storage
5. **User Permissions**: Add user-based access control for deletion operations

## Security Considerations

- **Confirmation Required**: Clear operations require user confirmation
- **Audit Logging**: Consider logging deletion operations for audit trails
- **Access Control**: In production, restrict deletion permissions to authorized users
- **Backup Before Clear**: Recommend exporting important data before clearing