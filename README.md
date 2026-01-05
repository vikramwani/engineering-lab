# Engineering Lab - AI & LLM Projects

This repository contains a collection of production-ready AI and LLM projects, ranging from simple examples to sophisticated multi-agent frameworks. Each project demonstrates different aspects of building reliable, scalable AI systems.

## 🏗️ Repository Structure

```
engineering-lab/
├── agent-alignment-framework/    # Multi-agent evaluation & alignment framework
├── llm-service/                  # Production LLM API microservice
├── hello-llm/                    # Simple LLM integration example
├── projects/                     # Additional experimental projects
├── docs/                         # Shared documentation
└── tools/                        # Shared utilities and tools
```

## 🚀 Projects Overview

### 1. Agent Alignment Framework
**Path**: `agent-alignment-framework/`  
**Status**: ✅ Production Ready (v2.0.0)

A deterministic, domain-agnostic framework for multi-agent evaluation with disagreement detection and human-in-the-loop escalation contracts.

**Key Features**:
- **Multi-agent orchestration** with specialized roles (advocate, skeptic, judge)
- **Deterministic alignment analysis** with explicit disagreement detection
- **HITL escalation contracts** - pure, serializable payloads for human review
- **Schema-driven evaluations** (Boolean, Categorical, Scalar, Free-form)
- **LLM provider agnostic** (OpenAI, Anthropic, Local models)
- **Embeddable architecture** - works in APIs, batch jobs, UIs, agent platforms

**Use Cases**:
- Risk assessment and compliance evaluation
- Content moderation and quality review
- Technical decision analysis (code review, architecture)
- Multi-perspective research and analysis

**Quick Start**:
```bash
cd agent-alignment-framework
python scripts/run_tests.py                    # Run all tests
python examples/example_usage.py               # Try the demo
python scripts/live_llm_smoke_test.py --help   # Optional LLM integration test
```

**Documentation**: [Framework README](agent-alignment-framework/README.md) | [Architecture](agent-alignment-framework/docs/architecture.md) | [Positioning](agent-alignment-framework/docs/positioning.md)

---

### 2. LLM Compatibility Service
**Path**: `llm-service/`  
**Status**: ✅ Production Ready

A FastAPI microservice that provides intelligent product compatibility analysis using a multi-agent debate architecture. Designed for e-commerce platforms and inventory management systems.

**Key Features**:
- **Multi-agent debate system** for nuanced compatibility analysis
- **Production-grade FastAPI** with authentication, validation, and error handling
- **Structured JSON responses** with confidence scoring
- **Comprehensive relationship classification** (replacement, accessory, consumable, etc.)
- **Request tracing and observability** with structured logging
- **Resilient architecture** with retries, timeouts, and graceful degradation

**Use Cases**:
- E-commerce product recommendations
- Inventory management and procurement
- Product catalog organization
- Compatibility verification systems

**Quick Start**:
```bash
cd llm-service
pip install -r requirements.txt
uvicorn src.api:app --reload
```

**Documentation**: [Service README](llm-service/README.md)

---

### 3. Hello LLM
**Path**: `hello-llm/`  
**Status**: ✅ Example/Learning

A minimal example demonstrating basic OpenAI API integration. Perfect for learning the fundamentals of LLM API usage.

**Key Features**:
- **Simple OpenAI client** with environment-based configuration
- **Clean example code** showing best practices
- **Minimal dependencies** for easy understanding

**Use Cases**:
- Learning LLM API basics
- Quick prototyping and experimentation
- Reference implementation for simple integrations

**Quick Start**:
```bash
cd hello-llm
pip install openai python-dotenv
# Set OPENAI_API_KEY in .env file
python app.py
```

---

### 4. Experimental Projects
**Path**: `projects/`  
**Status**: 🧪 Experimental

Additional projects and experiments in various stages of development.

- `projects/hello-llm/` - Alternative hello-world implementations
- `projects/sandbox/` - Experimental code and prototypes

---

## 🎯 Project Relationships

### Complementary Architecture

The projects in this repository are designed to work together while maintaining clear boundaries:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  (Your business logic, UIs, workflows)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              Agent Alignment Framework                      │
│  • Multi-agent evaluation and disagreement detection        │
│  • HITL escalation contracts                                │
│  • Domain-agnostic reasoning engine                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  LLM Service Layer                          │
│  • Production LLM API (llm-service)                         │
│  • Provider abstraction and resilience                      │
│  • Authentication, validation, observability                │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 LLM Provider APIs                           │
│  (OpenAI, Anthropic, Local models)                          │
└─────────────────────────────────────────────────────────────┘
```

### Integration Patterns

1. **Simple Integration**: Use `hello-llm` patterns for basic LLM calls
2. **Production API**: Use `llm-service` for scalable, resilient LLM access
3. **Multi-Agent Evaluation**: Use `agent-alignment-framework` for complex decision-making
4. **Full Stack**: Combine all layers for sophisticated AI applications

## 🛠️ Development Setup

### Prerequisites

- Python 3.9+ (recommended: 3.11)
- Git
- API keys for LLM providers (OpenAI, Anthropic)

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd engineering-lab

# Set up environment variables
cp llm-service/.env.example llm-service/.env
cp hello-llm/.env.example hello-llm/.env  # if exists
# Edit .env files with your API keys

# Install dependencies for each project as needed
cd agent-alignment-framework && pip install -e .
cd ../llm-service && pip install -r requirements.txt
cd ../hello-llm && pip install openai python-dotenv
```

### Running Tests

```bash
# Agent Alignment Framework (comprehensive test suite)
cd agent-alignment-framework
python scripts/run_tests.py

# LLM Service (API and integration tests)
cd llm-service
python test_providers.py
python test_logging.py

# Hello LLM (simple execution test)
cd hello-llm
python app.py
```

## 📚 Documentation

### Framework Documentation
- [Agent Alignment Framework](agent-alignment-framework/README.md) - Complete framework guide
- [Framework Positioning](agent-alignment-framework/docs/positioning.md) - Purpose and ecosystem fit
- [Architecture Guide](agent-alignment-framework/docs/architecture.md) - Technical deep dive
- [HITL Integration](agent-alignment-framework/docs/human-in-the-loop.md) - Human review patterns
- [Testing Guide](agent-alignment-framework/docs/testing.md) - Test boundaries and validation

### Service Documentation
- [LLM Service](llm-service/README.md) - Production API service guide

### Learning Resources
- [Hello LLM](hello-llm/) - Basic LLM integration examples

## 🚀 Deployment

### Production Deployment Options

**Agent Alignment Framework**:
- Embed directly in applications as a library
- Deploy as a microservice with REST API wrapper
- Use in batch processing systems
- Integrate with existing agent platforms

**LLM Service**:
- Docker containerization (Dockerfile included)
- Kubernetes deployment with horizontal scaling
- API Gateway integration
- Load balancer configuration

**Integration Patterns**:
- Event-driven architecture with message queues
- Synchronous API calls for real-time evaluation
- Batch processing for large-scale analysis

## 🤝 Contributing

Each project has its own contribution guidelines:

- **Agent Alignment Framework**: See [Contributing Guide](agent-alignment-framework/CONTRIBUTING.md)
- **LLM Service**: Follow standard FastAPI development practices
- **Examples**: Keep simple and focused on learning

### Development Principles

1. **Production Quality**: All code should be production-ready or clearly marked as experimental
2. **Clear Boundaries**: Each project has a specific purpose and scope
3. **Comprehensive Testing**: Deterministic tests for core logic, integration tests for APIs
4. **Documentation First**: Every project includes complete documentation
5. **Security Conscious**: No API keys in code, secure defaults, input validation

## 📄 License

This repository is licensed under the MIT License. See individual project directories for specific license information.

## 🆘 Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and community support
- **Documentation**: Check project-specific README files and documentation

---

**Engineering Lab** - Building reliable, scalable AI systems through practical examples and production-ready frameworks.