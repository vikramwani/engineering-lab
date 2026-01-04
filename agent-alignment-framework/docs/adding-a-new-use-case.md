# Adding a New Use Case to the Agent Alignment Framework

This guide walks you through creating a new evaluation use case using the Agent Alignment Framework. We'll use a **Risk Assessment** example to demonstrate the process.

## Overview

Adding a new use case involves:
1. Defining the evaluation domain and decision types
2. Creating specialized agents for the domain
3. Writing domain-specific prompts
4. Implementing a domain-specific evaluator
5. Testing and validation

## Step 1: Define Your Evaluation Domain

### 1.1 Identify the Decision Type

First, determine what type of decision your use case requires:

```python
from agent_alignment import BooleanDecision, CategoricalDecision, ScalarDecision

# Risk Assessment Example - Categorical decision
risk_levels = ["low", "medium", "high", "critical"]
decision_type = CategoricalDecision(categories=risk_levels)

# Alternative: Scalar risk score
# decision_type = ScalarDecision(min_value=0.0, max_value=10.0)
```

### 1.2 Define Input Schema

Determine what information your agents need to make decisions:

```python
# Risk Assessment inputs
risk_inputs = {
    "scenario": {
        "description": "System deployment to production",
        "context": "First deployment of new authentication system",
        "timeline": "Next Friday during business hours"
    },
    "factors": {
        "technical_complexity": "high",
        "user_impact": "all users affected",
        "rollback_capability": "available within 30 minutes"
    },
    "constraints": {
        "budget": 50000,
        "timeline_flexibility": "none",
        "resource_availability": "limited"
    }
}
```

## Step 2: Create Domain-Specific Agents

### 2.1 Implement Specialized Agent Class

```python
# examples/risk_assessment/agents.py
from agent_alignment.core.agent import LLMAgent
from agent_alignment.core.models import AgentOutput, EvaluationTask
from agent_alignment.utils.validation import extract_json_from_text, normalize_confidence

class RiskAssessmentAgent(LLMAgent):
    """Agent specialized for risk assessment evaluation."""
    
    def _build_prompt(self, task: EvaluationTask) -> str:
        """Build risk assessment prompt."""
        template = self._load_prompt_template()
        
        scenario = task.inputs.get("scenario", {})
        factors = task.inputs.get("factors", {})
        constraints = task.inputs.get("constraints", {})
        
        # Format scenario information
        scenario_info = self._format_scenario_info(scenario)
        factors_info = self._format_factors_info(factors)
        constraints_info = self._format_constraints_info(constraints)
        
        return template.format(
            agent_role=self.role.instruction,
            evaluation_criteria=task.evaluation_criteria,
            scenario_info=scenario_info,
            factors_info=factors_info,
            constraints_info=constraints_info,
            risk_levels=", ".join(task.context.get("risk_levels", [])),
        )
    
    def _parse_response(self, task: EvaluationTask, response: str, request_id: str) -> AgentOutput:
        """Parse risk assessment response."""
        json_data = extract_json_from_text(response)
        
        if json_data is None:
            return self._parse_fallback_response(task, response, request_id)
        
        # Extract and validate risk assessment fields
        risk_level = json_data.get("risk_level") or json_data.get("decision")
        confidence = normalize_confidence(json_data.get("confidence", 0.5))
        reasoning = json_data.get("reasoning", "")
        risk_factors = json_data.get("risk_factors", [])
        mitigation_strategies = json_data.get("mitigation_strategies", [])
        
        # Combine evidence
        evidence = risk_factors + mitigation_strategies
        
        return AgentOutput(
            agent_name=self.role.name,
            role_type=self.role.role_type,
            decision=risk_level,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence,
            metadata={
                "request_id": request_id,
                "domain": "risk_assessment",
                "risk_factors": risk_factors,
                "mitigation_strategies": mitigation_strategies,
            }
        )
    
    def _format_scenario_info(self, scenario: dict) -> str:
        """Format scenario information for prompts."""
        if not scenario:
            return "No scenario information provided"
        
        lines = ["Scenario:"]
        for key, value in scenario.items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(lines)
    
    # Similar methods for _format_factors_info and _format_constraints_info
```

### 2.2 Define Agent Roles

```python
# examples/risk_assessment/evaluator.py
def _create_agent_roles(self) -> List[AgentRole]:
    """Create agent roles for risk assessment."""
    return [
        AgentRole(
            name="risk_analyst",
            role_type="advocate", 
            instruction=(
                "Analyze the scenario and identify potential risks. "
                "Focus on technical, operational, and business risks that could impact success."
            ),
            prompt_template="examples/risk_assessment/prompts/risk_analyst.txt",
        ),
        AgentRole(
            name="optimist_agent",
            role_type="skeptic",
            instruction=(
                "Challenge risk assessments and look for positive factors. "
                "Identify strengths, safeguards, and reasons for optimism."
            ),
            prompt_template="examples/risk_assessment/prompts/optimist.txt",
        ),
        AgentRole(
            name="risk_manager",
            role_type="judge",
            instruction=(
                "Synthesize risk analysis and make final risk level determination. "
                "Balance identified risks against mitigating factors."
            ),
            prompt_template="examples/risk_assessment/prompts/risk_manager.txt",
        ),
    ]
```

## Step 3: Create Domain-Specific Prompts

### 3.1 Risk Analyst Prompt

```text
# examples/risk_assessment/prompts/risk_analyst.txt
You are an expert risk analyst evaluating potential risks in a business scenario.

Your role: {agent_role}

Task: {evaluation_criteria}

{scenario_info}

{factors_info}

{constraints_info}

Available risk levels: {risk_levels}

As a risk analyst, focus on:
1. Technical risks (system failures, integration issues, performance problems)
2. Operational risks (process failures, resource constraints, timeline issues)
3. Business risks (financial impact, reputation damage, competitive disadvantage)
4. External risks (market conditions, regulatory changes, dependencies)

Provide your assessment in JSON format:

```json
{
  "risk_level": "medium",
  "confidence": 0.85,
  "reasoning": "Detailed analysis of identified risks and their potential impact",
  "risk_factors": [
    "Specific risk factor 1",
    "Specific risk factor 2",
    "Specific risk factor 3"
  ],
  "mitigation_strategies": [
    "Potential mitigation approach 1",
    "Potential mitigation approach 2"
  ]
}
```

Be thorough in identifying risks while remaining objective and evidence-based.
```

### 3.2 Create Additional Prompts

Create similar prompts for the optimist agent and risk manager, each tailored to their specific perspective and role in the evaluation process.

## Step 4: Implement Domain Evaluator

### 4.1 Create Specialized Evaluator

```python
# examples/risk_assessment/evaluator.py
from typing import Any, Dict, Optional
from agent_alignment import MultiAgentEvaluator, EvaluationTask, CategoricalDecision
from .agents import RiskAssessmentAgent

class RiskAssessmentEvaluator:
    """Specialized evaluator for risk assessment."""
    
    RISK_LEVELS = ["low", "medium", "high", "critical"]
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
        # Create agent roles
        agent_roles = self._create_agent_roles()
        
        # Create multi-agent evaluator
        self.evaluator = MultiAgentEvaluator.from_roles(
            roles=agent_roles,
            llm_client=llm_client,
            agent_class=RiskAssessmentAgent,
        )
    
    def assess_risk(
        self,
        scenario: Dict[str, Any],
        factors: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assess risk level for a given scenario."""
        
        # Create evaluation task
        task = EvaluationTask(
            task_id=task_id or f"risk_{hash(str(scenario))}"[:8],
            task_type="risk_assessment",
            decision_type=CategoricalDecision(categories=self.RISK_LEVELS),
            inputs={
                "scenario": scenario,
                "factors": factors,
                "constraints": constraints or {},
            },
            evaluation_criteria=(
                "Assess the overall risk level for this scenario considering "
                "technical, operational, business, and external risk factors."
            ),
            context={
                "domain": "risk_assessment",
                "risk_levels": self.RISK_LEVELS,
            }
        )
        
        # Run evaluation
        result = self.evaluator.evaluate(task)
        
        # Convert to risk-specific format
        return {
            "risk_level": result.decision,
            "confidence": result.confidence,
            "assessment": result.reasoning,
            "risk_factors": self._extract_risk_factors(result.agent_outputs),
            "mitigation_strategies": self._extract_mitigation_strategies(result.agent_outputs),
            "agent_assessments": [
                {
                    "agent": output.agent_name,
                    "role": output.role_type,
                    "risk_level": output.decision,
                    "confidence": output.confidence,
                    "reasoning": output.reasoning,
                }
                for output in result.agent_outputs
            ],
            "alignment_summary": {
                "state": result.alignment_summary.state.value,
                "agreement": result.alignment_summary.decision_agreement,
                "confidence_spread": result.alignment_summary.confidence_spread,
            },
            "needs_review": result.needs_human_review,
            "request_id": result.request_id,
        }
    
    def _extract_risk_factors(self, agent_outputs) -> List[str]:
        """Extract risk factors from agent outputs."""
        risk_factors = []
        for output in agent_outputs:
            if "risk_factors" in output.metadata:
                risk_factors.extend(output.metadata["risk_factors"])
        return list(set(risk_factors))  # Remove duplicates
    
    def _extract_mitigation_strategies(self, agent_outputs) -> List[str]:
        """Extract mitigation strategies from agent outputs."""
        strategies = []
        for output in agent_outputs:
            if "mitigation_strategies" in output.metadata:
                strategies.extend(output.metadata["mitigation_strategies"])
        return list(set(strategies))
```

## Step 5: Usage Example

### 5.1 Basic Usage

```python
from agent_alignment.llm.client import LLMClient
from agent_alignment.llm.providers import OpenAIProvider
from examples.risk_assessment import RiskAssessmentEvaluator

# Setup
provider = OpenAIProvider(model="gpt-4o-mini")
llm_client = LLMClient(provider)
evaluator = RiskAssessmentEvaluator(llm_client)

# Define scenario
scenario = {
    "description": "Deploy new payment processing system",
    "context": "Black Friday weekend deployment",
    "timeline": "48 hours before peak traffic"
}

factors = {
    "technical_complexity": "high",
    "testing_coverage": "80%",
    "team_experience": "moderate",
    "rollback_plan": "available"
}

# Assess risk
result = evaluator.assess_risk(scenario, factors)

print(f"Risk Level: {result['risk_level']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Assessment: {result['assessment']}")
```

### 5.2 Integration with HITL

```python
from agent_alignment.core.hitl import HITLManager, MockHITLProvider

# Setup HITL for high-risk scenarios
hitl_provider = MockHITLProvider(auto_approve=False)
hitl_manager = HITLManager(hitl_provider)

# Assess risk
result = evaluator.assess_risk(scenario, factors)

# Check if human review is needed
if result['needs_review']:
    # Create HITL request (would integrate with your review system)
    review_request = hitl_manager.create_review_request(
        evaluation_result,  # Full EvaluationResult object
        priority="high" if result['risk_level'] == "critical" else "medium"
    )
    
    review_id = hitl_manager.submit_review_request(review_request)
    print(f"Human review requested: {review_id}")
```

## Step 6: Testing and Validation

### 6.1 Unit Tests

```python
# tests/test_risk_assessment.py
import pytest
from examples.risk_assessment import RiskAssessmentEvaluator

def test_risk_assessment_basic():
    """Test basic risk assessment functionality."""
    evaluator = RiskAssessmentEvaluator(mock_llm_client)
    
    scenario = {"description": "Low-risk maintenance update"}
    factors = {"complexity": "low", "testing": "complete"}
    
    result = evaluator.assess_risk(scenario, factors)
    
    assert result["risk_level"] in RiskAssessmentEvaluator.RISK_LEVELS
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["assessment"]) > 0

def test_high_risk_scenario():
    """Test that high-risk scenarios are properly identified."""
    evaluator = RiskAssessmentEvaluator(mock_llm_client)
    
    scenario = {"description": "Untested system during peak traffic"}
    factors = {"complexity": "high", "testing": "minimal"}
    
    result = evaluator.assess_risk(scenario, factors)
    
    # Should identify as high risk
    assert result["risk_level"] in ["high", "critical"]
```

### 6.2 Integration Tests

```python
def test_agent_alignment():
    """Test that agents produce consistent outputs."""
    evaluator = RiskAssessmentEvaluator(real_llm_client)
    
    # Test with clear low-risk scenario
    low_risk_scenario = {
        "description": "Minor documentation update",
        "context": "Non-production environment"
    }
    
    result = evaluator.assess_risk(low_risk_scenario, {})
    
    # All agents should agree on low risk
    agent_decisions = [a["risk_level"] for a in result["agent_assessments"]]
    assert all(level in ["low", "medium"] for level in agent_decisions)
```

## Step 7: Documentation

### 7.1 Create Use Case Documentation

```markdown
# Risk Assessment Use Case

## Overview
The Risk Assessment use case evaluates business scenarios to determine risk levels
and identify mitigation strategies using multi-agent analysis.

## Agents
- **Risk Analyst**: Identifies potential risks and their impact
- **Optimist Agent**: Challenges risk assessments and finds positive factors  
- **Risk Manager**: Synthesizes analysis and determines final risk level

## Usage
[Include usage examples and API documentation]

## Configuration
[Document configuration options and customization points]
```

## Best Practices

### 1. Domain Modeling
- Clearly define your decision space and valid outcomes
- Consider edge cases and ambiguous scenarios
- Design for extensibility as requirements evolve

### 2. Agent Design
- Give each agent a clear, distinct perspective
- Ensure agents have complementary viewpoints
- Balance thoroughness with efficiency

### 3. Prompt Engineering
- Use specific, actionable instructions
- Include relevant examples and context
- Test prompts with various scenarios

### 4. Validation
- Test with known scenarios to validate behavior
- Monitor agent agreement patterns
- Collect feedback on real-world usage

### 5. Integration
- Design clean APIs for your specific domain
- Provide clear error messages and validation
- Consider performance requirements for your use case

By following this guide, you can create robust, domain-specific evaluators that leverage the full power of the Agent Alignment Framework while maintaining clean separation of concerns and extensibility.