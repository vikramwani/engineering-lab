# Agent Alignment Framework

A production-ready, domain-agnostic Python framework for building multi-agent evaluation systems with deterministic alignment analysis, disagreement detection, and human-in-the-loop escalation contracts.

## 🚀 Overview

The Agent Alignment Framework enables robust decision-making through multi-perspective evaluation, where AI agents analyze problems from different viewpoints, detect disagreements, and synthesize final decisions with calibrated confidence. The framework is designed as a **pure reasoning engine** that can be embedded in any system without modification.

📘 **Design & Positioning**  
See [docs/positioning.md](docs/positioning.md) for how this framework fits alongside agent orchestration systems like Strands.


### Key Principles

- **Deterministic**: Same inputs always produce identical outputs with no randomness
- **Domain Agnostic**: Works across any evaluation domain without hardcoded assumptions  
- **Pure Core Logic**: No side effects, logging, or I/O in core reasoning functions
- **Embeddable**: Can be integrated into any system architecture (APIs, batch jobs, UIs)
- **Contract-Driven**: HITL escalation as pure, serializable contracts rather than workflows

### Core Capabilities

- **Multi-Agent Orchestration**: Coordinate multiple agents with specialized roles and perspectives
- **Deterministic Alignment Analysis**: Detect agreement patterns, confidence spreads, and disagreement areas
- **Schema-Driven Evaluations**: Support boolean, categorical, scalar, and free-form decision types
- **HITL Escalation Contract**: Pure, deterministic human review escalation without workflow assumptions
- **LLM Provider Agnostic**: Works with OpenAI, Anthropic, local models, or custom providers
- **Production Ready**: Structured logging, error handling, request tracing, and comprehensive validation

## 🏗️ Architecture

The framework enforces strict separation between pure core logic and infrastructure concerns:

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

**Architectural Guarantees:**
- Core reasoning functions are pure with no side effects
- Infrastructure handles all I/O, logging, and external communication
- Event callbacks provide clean interface between layers
- Framework can be embedded in any system without modification

## 🎯 Core Concepts

### Evaluation Task
Defines what needs to be evaluated - the input schema and evaluation criteria.

### Agent Roles
Specialized perspectives that agents take when evaluating:
- **Advocate**: Argues for positive outcomes, finds supporting evidence
- **Skeptic**: Challenges assumptions, identifies risks and counter-evidence  
- **Judge**: Synthesizes perspectives and makes final decisions
- **Domain Expert**: Applies specialized knowledge and heuristics
- **Custom Roles**: Define your own agent perspectives

### Alignment States
The framework deterministically detects four alignment states:
- **FULL_ALIGNMENT**: All agents agree on decision with high confidence
- **SOFT_DISAGREEMENT**: Minor differences in confidence or reasoning approach
- **HARD_DISAGREEMENT**: Fundamental conflicts in decisions (triggers HITL escalation)
- **INSUFFICIENT_SIGNAL**: Agents lack confidence or sufficient information

### HITL Escalation Contract
When disagreement exceeds thresholds, the framework generates structured escalation contracts:
- **Pure, deterministic logic** with no UI or workflow assumptions
- **Complete context preservation** with all agent decisions and reasoning
- **Machine-readable reasons** for why human review is needed
- **Serializable payloads** ready for any downstream review system (queues, APIs, webhooks)

## 🚀 Quick Start

### Installation

```bash
pip install agent-alignment-framework
```

### Basic Usage

```python
# Run all framework tests and examples
python scripts/run_tests.py

# Or run individually:
python tests/test_framework_validation.py  # Core validation (9 tests)
python examples/example_usage.py           # End-to-end demo
python examples/simple_hitl_demo.py        # HITL contract demo

# Optional: Test with real LLM providers (requires API keys)
python scripts/live_llm_smoke_test.py --provider openai
```

```python
from agent_alignment import (
    MultiAgentEvaluator, AgentRole, EvaluationTask, 
    BooleanDecisionSchema, LLMClient
)

# Define your evaluation task
task = EvaluationTask(
    task_id="compatibility-001",
    task_type="compatibility_check",
    decision_schema=BooleanDecisionSchema(
        positive_label="compatible",
        negative_label="incompatible"
    ),
    context={
        "item_a": {"name": "iPhone 15", "type": "smartphone"},
        "item_b": {"name": "MagSafe Charger", "type": "charger"}
    },
    evaluation_criteria="Determine if these items are compatible"
)

# Configure agent roles
roles = [
    AgentRole(
        name="advocate", 
        role_type="advocate",
        instruction="Find evidence FOR compatibility",
        prompt_template="prompts/advocate.txt"
    ),
    AgentRole(
        name="skeptic", 
        role_type="skeptic", 
        instruction="Find evidence AGAINST compatibility",
        prompt_template="prompts/skeptic.txt"
    ),
    AgentRole(
        name="judge", 
        role_type="judge",
        instruction="Make final decision based on evidence",
        prompt_template="prompts/judge.txt"
    )
]

# Create LLM client and evaluator
llm_client = LLMClient.from_provider("openai")  # or "anthropic", "local"
evaluator = MultiAgentEvaluator.from_roles(roles, llm_client)

# Run evaluation
result = evaluator.evaluate(task)

print(f"Decision: {result.synthesized_decision}")
print(f"Confidence: {result.confidence}")
print(f"Alignment: {result.alignment_summary.state}")

# Check if human review is needed
if result.requires_human_review:
    print("Agents disagreed - human review recommended")
    
    # Create HITL escalation contract
    hitl_request = evaluator.create_hitl_request(result)
    if hitl_request:
        print(f"Escalation reason: {hitl_request.escalation_reason}")
        print(f"Summary: {hitl_request.summary}")
        # Send to your review system (queue, API, webhook, etc.)
```

### Advanced Usage: Custom Decision Schemas

```python
from agent_alignment import EvaluationTask, ScalarDecisionSchema, CategoricalDecisionSchema

# Scalar evaluation (0-100 score)
task = EvaluationTask(
    task_id="quality-001",
    task_type="quality_assessment",
    decision_schema=ScalarDecisionSchema(min_value=0, max_value=100),
    context={"document": "..."},
    evaluation_criteria="Rate the quality of this document"
)

# Categorical evaluation
task = EvaluationTask(
    task_id="classification-001",
    task_type="content_classification", 
    decision_schema=CategoricalDecisionSchema(
        categories=["news", "opinion", "analysis"]
    ),
    context={"article": "..."},
    evaluation_criteria="Classify this article type"
)
```

## 📋 Use Cases

This framework is designed for any evaluation scenario where multiple perspectives improve decision quality:

### Business & Operations
- **Risk Assessment**: Financial, operational, or strategic risk evaluation
- **Vendor Evaluation**: Multi-criteria supplier assessment
- **Investment Analysis**: Due diligence with multiple analyst perspectives
- **Policy Impact**: Analyzing policy changes from stakeholder viewpoints

### Content & Media
- **Content Moderation**: Safety, quality, and guideline compliance
- **Creative Review**: Evaluating creative work from different criteria
- **Fact Checking**: Multi-source verification and credibility assessment
- **Translation Quality**: Accuracy, fluency, and cultural appropriateness

### Technical & Engineering
- **Code Review**: Security, performance, maintainability analysis
- **Architecture Decisions**: Technical trade-off evaluation
- **Product Compatibility**: Hardware/software compatibility assessment
- **Security Assessment**: Multi-vector threat analysis

### Research & Analysis
- **Literature Review**: Multi-perspective research synthesis
- **Data Quality**: Completeness, accuracy, and reliability assessment
- **Experimental Design**: Methodology evaluation from different angles
- **Hypothesis Testing**: Evidence evaluation with bias detection

## 🔧 Configuration

### Environment Variables

```bash
# LLM Provider Configuration
LLM_PROVIDER=openai  # openai, anthropic, local
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=ant-...

# Framework Configuration  
LOG_LEVEL=INFO
REQUEST_TIMEOUT_SECONDS=30
MAX_RETRIES=3

# Human-in-the-Loop Thresholds
HITL_CONFIDENCE_THRESHOLD=0.7
HITL_DISAGREEMENT_THRESHOLD=0.3
```

### Agent Configuration

```python
from agent_alignment.config import AgentConfig

config = AgentConfig(
    roles=[
        {
            "name": "advocate",
            "instruction": "Find evidence supporting the positive case",
            "prompt_template": "prompts/advocate.txt",
            "max_tokens": 500
        },
        {
            "name": "skeptic", 
            "instruction": "Challenge assumptions and find counter-evidence",
            "prompt_template": "prompts/skeptic.txt",
            "max_tokens": 500
        }
    ],
    alignment_thresholds={
        "soft_disagreement": 0.2,
        "hard_disagreement": 0.4,
        "insufficient_signal": 0.5
    }
)
```

## 📚 Documentation

- [Framework Positioning](docs/positioning.md) - Purpose and ecosystem fit
- [Architecture Guide](docs/architecture.md) - Deep dive into framework design
- [Adding New Use Cases](docs/adding-a-new-use-case.md) - Step-by-step guide
- [Human-in-the-Loop Integration](docs/human-in-the-loop.md) - HITL patterns
- [Testing Framework](docs/testing.md) - Deterministic vs non-deterministic tests
- [API Reference](docs/api-reference.md) - Complete API documentation

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/your-org/agent-alignment-framework
cd agent-alignment-framework
pip install -e ".[dev]"
pytest
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- [GitHub Issues](https://github.com/your-org/agent-alignment-framework/issues)
- [Documentation](https://agent-alignment-framework.readthedocs.io)
- [Community Discord](https://discord.gg/agent-alignment)