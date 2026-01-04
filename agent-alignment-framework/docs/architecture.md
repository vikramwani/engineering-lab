# Agent Alignment Framework Architecture

## Overview

The Agent Alignment Framework is designed around the principle of **multi-perspective evaluation** where different AI agents analyze problems from distinct viewpoints, enabling more robust and reliable decision-making through disagreement detection and consensus building.

The framework enforces strict **separation of concerns** with pure core logic, isolated infrastructure concerns, and stable public APIs.

## Architectural Boundaries

### Core vs Infrastructure Separation

```
┌─────────────────────────────────────────────────────────────────┐
│                        CORE DOMAIN                              │
│                   (Pure, Deterministic)                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Models    │  │ Resolution  │  │    HITL     │            │
│  │             │  │   Engine    │  │  Contract   │            │
│  │ • Pure data │  │ • Pure      │  │ • Pure      │            │
│  │ • No I/O    │  │   functions │  │   functions │            │
│  │ • No logs   │  │ • No I/O    │  │ • No I/O    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                    Event Callbacks (Pure Interface)
                                │
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Evaluator  │  │   Logging   │  │     LLM     │            │
│  │             │  │             │  │  Providers  │            │
│  │ • Orchestr. │  │ • Structured│  │ • External  │            │
│  │ • Logging   │  │ • JSON      │  │   APIs      │            │
│  │ • I/O       │  │ • Files     │  │ • Network   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Core Principles:**
- **Core modules** (`core/*`) contain NO logging, I/O, or external dependencies
- **Infrastructure modules** handle logging, LLM providers, configuration loading
- **Event callbacks** provide pure interface between core and infrastructure
- **Configuration injection** eliminates hardcoded values in core logic

### HITL as Contract, Not Workflow

The HITL system is designed as a **pure escalation contract** rather than a workflow system:

```
┌─────────────────────────────────────────────────────────────────┐
│                    HITL ESCALATION CONTRACT                     │
│                      (Pure, Deterministic)                     │
│                                                                 │
│  Input: EvaluationResult + AlignmentSummary                    │
│  Output: Optional[HITLRequest] (structured, serializable)      │
│                                                                 │
│  ✅ Deterministic escalation logic                             │
│  ✅ Complete context preservation                              │
│  ✅ Machine-readable reasons                                   │
│  ✅ Zero workflow assumptions                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                    Pluggable Integration
                                │
┌─────────────────────────────────────────────────────────────────┐
│                  DOWNSTREAM REVIEW SYSTEMS                     │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Queues    │  │  REST APIs  │  │  Webhooks   │            │
│  │             │  │             │  │             │            │
│  │ • RabbitMQ  │  │ • HTTP      │  │ • Events    │            │
│  │ • Kafka     │  │ • JSON      │  │ • Callbacks │            │
│  │ • Redis     │  │ • GraphQL   │  │ • Async     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Architecture

### 1. Multi-Agent Orchestration Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    MultiAgentEvaluator                          │
│                  (Orchestration Engine)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────────────────────┐
        ▼             ▼             ▼                             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐         ┌─────────────┐
│ Agent A     │ │ Agent B     │ │ Judge       │         │ Alignment   │
│ (Advocate)  │ │ (Skeptic)   │ │ Agent       │         │ Engine      │
│             │ │             │ │             │         │             │
│ Structured  │ │ Structured  │ │ Synthesis   │         │ Disagreement│
│ Output      │ │ Output      │ │ & Decision  │         │ Detection   │
└─────────────┘ └─────────────┘ └─────────────┘         └─────────────┘
```

**Key Components:**

- **MultiAgentEvaluator**: Central orchestrator that manages agent execution, collects outputs, and coordinates the evaluation process
- **BaseAgent/LLMAgent**: Abstract base classes for implementing domain-specific agents
- **AlignmentEngine**: Analyzes agent outputs to detect disagreements and synthesize final decisions
- **EvaluationTask**: Standardized input format that defines what needs to be evaluated

### 2. Agent Architecture

Each agent follows a consistent interface while allowing for specialized implementations:

```python
class BaseAgent(ABC):
    def evaluate(self, task: EvaluationTask) -> AgentOutput:
        # Core evaluation method that all agents must implement
        pass
```

**Agent Types:**
- **Advocate**: Argues FOR a particular outcome, finds supporting evidence
- **Skeptic**: Argues AGAINST or challenges assumptions, finds counter-evidence
- **Judge**: Synthesizes multiple perspectives and makes final decisions
- **Domain Expert**: Applies specialized knowledge and heuristics
- **Custom**: User-defined agents for specific use cases

### Alignment & Resolution as Deterministic Engines

The alignment and resolution system is built as **pure, deterministic engines** with no side effects:

```python
# Pure alignment analysis (no logging, no I/O)
class AlignmentAnalyzer:
    def analyze_alignment(
        self, 
        task: EvaluationTask, 
        agent_decisions: List[AgentDecision],
        event_callback: Optional[Callable] = None  # Pure interface
    ) -> AlignmentSummary:
        # Pure deterministic analysis
        # Emits structured events via callback
        pass

# Pure disagreement resolution (no logging, no I/O)  
class DisagreementResolver:
    def resolve_disagreement(
        self,
        task: EvaluationTask,
        agent_decisions: List[AgentDecision], 
        alignment_summary: AlignmentSummary,
        event_callback: Optional[Callable] = None  # Pure interface
    ) -> Tuple[Any, float, str, List[str]]:
        # Pure deterministic resolution
        # Emits structured events via callback
        pass
```

**Key Features:**
- **Deterministic**: Same inputs always produce identical outputs
- **Configurable**: All thresholds injected via `AlignmentThresholds`
- **Observable**: Structured events emitted via pure callback interface
- **Extensible**: Plugin architecture for custom resolution strategies

### 4. Decision Types and Flexibility

The framework supports multiple decision types through a polymorphic design:

```python
class DecisionType(ABC):
    def validate_decision(self, decision) -> bool: pass
    def normalize_confidence(self, confidence) -> float: pass

# Concrete implementations
BooleanDecision()      # True/False decisions
CategoricalDecision()  # Classification into predefined categories  
ScalarDecision()       # Numeric scoring/ranking
FreeFormDecision()     # Open-ended recommendations
```

### 5. Policy-Driven Human-in-the-Loop Integration

The HITL system uses configurable policies to determine when human review is needed:

```python
class HITLTriggerPolicy:
    def __init__(
        self,
        trigger_on_hard_disagreement: bool = True,
        trigger_on_insufficient_signal: bool = True,
        trigger_on_low_confidence: bool = True,
        min_confidence_threshold: float = 0.6,
        max_confidence_spread: float = 0.4,
    ):
        # Policy configuration for HITL triggers
        pass

class HITLManager:
    def __init__(self, provider: HITLProvider, trigger_policy: HITLTriggerPolicy):
        # Policy-driven HITL management
        pass
    
    def should_request_review(self, result: EvaluationResult) -> Tuple[bool, str]:
        # Apply trigger policy to determine if review is needed
        pass
    
    def create_review_request(self, result: EvaluationResult) -> HITLRequest:
        # Create structured review artifacts with complete context
        pass
```

**HITL Provider Interface:**

```python
class HITLProvider(ABC):
    def submit_review_request(self, request: HITLRequest) -> str: pass
    def get_review_status(self, review_id: str) -> str: pass
    def get_review_response(self, review_id: str) -> HITLResponse: pass
    def cancel_review_request(self, review_id: str) -> bool: pass
```

**Key Features:**
- **Policy-Driven Triggers**: Configurable thresholds for when to request human review
- **Structured Artifacts**: Complete context packages for human reviewers
- **Provider Abstraction**: Interface-based integration with any review system
- **Workflow Agnostic**: No assumptions about UI, notifications, or review processes

## Design Principles

### 1. Separation of Concerns

- **Configuration**: Prompts, thresholds, and settings are externalized
- **Business Logic**: Core evaluation logic is separate from domain specifics
- **Infrastructure**: LLM providers, logging, and I/O are abstracted

### 2. Extensibility

- **Plugin Architecture**: New agent types can be added without modifying core code
- **Provider Abstraction**: Support for multiple LLM providers (OpenAI, Anthropic, local)
- **Decision Types**: New decision formats can be added through the DecisionType interface

### 3. Observability

- **Structured Logging**: All operations are logged with structured metadata
- **Request Tracing**: Unique IDs track requests through the entire pipeline
- **Alignment Metrics**: Detailed analysis of agent agreement and disagreement

### 4. Production Readiness

- **Error Handling**: Comprehensive error handling with retry logic
- **Validation**: Input validation and output sanitization throughout
- **Performance**: Efficient execution with optional parallel agent processing

## Data Flow

### 1. Evaluation Request Flow

```
EvaluationTask → MultiAgentEvaluator → [Agent1, Agent2, AgentN] → AlignmentEngine → EvaluationResult
```

1. **Task Creation**: User creates EvaluationTask with inputs and criteria
2. **Agent Execution**: Evaluator runs each agent with the task
3. **Output Collection**: Agent outputs are collected and validated
4. **Alignment Analysis**: AlignmentEngine analyzes agreement/disagreement
5. **Decision Synthesis**: Final decision is synthesized from agent outputs
6. **Result Generation**: Complete EvaluationResult is returned

### 2. HITL Integration Flow

```
EvaluationResult → HITLManager → HITLProvider → External Review System → HITLResponse
```

1. **Disagreement Detection**: AlignmentEngine identifies need for human review
2. **Request Creation**: HITLManager creates structured review request
3. **External Submission**: HITLProvider submits to external review system
4. **Human Review**: Human reviewer analyzes agent outputs and provides decision
5. **Response Integration**: HITLResponse is integrated back into the system

## Configuration Architecture

### 1. Hierarchical Configuration

```
Environment Variables → Configuration Files → Runtime Overrides
```

- **Environment**: Sensitive data (API keys) and deployment-specific settings
- **Files**: Agent configurations, prompts, and thresholds
- **Runtime**: Task-specific overrides and dynamic adjustments

### 2. Prompt Management

```
prompts/
├── advocate.txt      # Advocate agent prompt template
├── skeptic.txt       # Skeptic agent prompt template
├── judge.txt         # Judge agent prompt template
└── domain/
    ├── compatibility.txt
    └── risk_assessment.txt
```

- **Template System**: Prompts use variable substitution for dynamic content
- **Version Control**: Prompts are versioned and tracked like code
- **Validation**: Prompt templates are validated for required variables

## Extension Points

### 1. Adding New Agent Types

```python
class CustomAgent(LLMAgent):
    def _build_prompt(self, task: EvaluationTask) -> str:
        # Custom prompt building logic
        pass
    
    def _parse_response(self, task: EvaluationTask, response: str) -> AgentOutput:
        # Custom response parsing logic
        pass
```

### 2. Adding New Decision Types

```python
class RankingDecision(DecisionType):
    def __init__(self, items: List[str]):
        self.items = items
    
    def validate_decision(self, decision: List[str]) -> bool:
        # Validate ranking order
        pass
```

### 3. Adding New LLM Providers

```python
class CustomProvider(LLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        # Custom LLM integration
        pass
    
    def get_provider_name(self) -> str:
        return "custom-provider"
```

## Performance Considerations

### 1. Parallel Execution

- Agents can be executed in parallel for improved performance
- Configurable concurrency limits prevent resource exhaustion
- Timeout handling ensures system responsiveness

### 2. Caching and Optimization

- Prompt templates are cached after first load
- LLM responses can be cached for identical inputs
- Configuration is loaded once and reused

### 3. Resource Management

- Connection pooling for LLM providers
- Graceful degradation when agents fail
- Memory-efficient processing of large evaluations

## Security Considerations

### 1. Input Validation

- All inputs are validated against schemas
- Prompt injection protection through sanitization
- Output validation prevents malformed responses

### 2. Credential Management

- API keys are never logged or exposed
- Environment-based credential management
- Secure defaults for all configurations

### 3. Error Handling

- Sensitive information is excluded from error messages
- Structured logging avoids credential leakage
- Graceful failure modes prevent information disclosure