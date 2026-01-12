# Engineering Lab

A comprehensive workspace for multi-agent AI systems, LLM service abstractions, and interactive evaluation tools.

## 🏗️ Projects Overview

This repository contains multiple interconnected projects that form a complete ecosystem for multi-agent AI development and evaluation:

### 🧠 [Agent Alignment Framework](./agent-alignment-framework/)
**Purpose**: Core library for multi-agent evaluation and alignment analysis  
**Type**: Python package (library-grade)  
**Key Features**:
- Multi-agent decision orchestration with advocate/skeptic/judge patterns
- Alignment analysis and disagreement detection
- LLM provider abstraction (OpenAI, Anthropic)
- Human-in-the-loop (HITL) escalation system
- Deterministic testing with mock responses

**Use Cases**: Product compatibility evaluation, content moderation, risk assessment, any scenario requiring multiple AI perspectives with alignment analysis.

### 🖥️ [Agent Alignment UI](./agent-alignment-ui/)
**Purpose**: Full-stack web application for interactive multi-agent evaluations  
**Type**: FastAPI backend + React frontend  
**Key Features**:
- Interactive evaluation creation and configuration
- Real-time evaluation progress with WebSocket updates
- Comprehensive result visualization and alignment analysis
- Evaluation history management with export capabilities
- API key management and provider configuration
- Human-in-the-loop interface for disputed decisions

**Architecture**: 
- **Backend**: FastAPI server with REST APIs and WebSocket support
- **Frontend**: React + TypeScript with Material-UI components
- **Integration**: Seamless integration with Agent Alignment Framework

### 🔧 [LLM Service](./llm-service/)
**Purpose**: Centralized LLM provider abstraction and prompt management  
**Type**: Service layer  
**Key Features**:
- Provider-agnostic LLM interface (OpenAI, Anthropic, etc.)
- Centralized prompt template management
- Request/response logging and monitoring
- Configuration management for different environments

### 👋 [Hello LLM](./hello-llm/)
**Purpose**: Minimal demo application for basic LLM interactions  
**Type**: Simple demo/sandbox  
**Key Features**:
- Basic chat interface
- Quick LLM provider testing
- Development sandbox for experimentation

## 🔄 Project Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    Engineering Lab                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   LLM Service   │◄───┤     Agent Alignment UI          │ │
│  │                 │    │                                 │ │
│  │ • Provider      │    │ • FastAPI Backend               │ │
│  │   Abstraction   │    │ • React Frontend                │ │
│  │ • Prompt Mgmt   │    │ • Real-time Updates             │ │
│  │ • Logging       │    │ • History Management            │ │
│  └─────────────────┘    │ • API Key Management            │ │
│                         └─────────────────┬───────────────┘ │
│                                           │                 │
│  ┌─────────────────┐    ┌─────────────────▼───────────────┐ │
│  │   Hello LLM     │    │   Agent Alignment Framework     │ │
│  │                 │    │                                 │ │
│  │ • Simple Demo   │    │ • Multi-agent Orchestration     │ │
│  │ • Quick Testing │    │ • Alignment Analysis            │ │
│  │ • Sandbox       │    │ • HITL Escalation               │ │
│  └─────────────────┘    │ • Decision Schemas              │ │
│                         └─────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Integration Flow**:
1. **Agent Alignment Framework** provides the core multi-agent evaluation engine
2. **Agent Alignment UI** provides the interactive interface and orchestrates evaluations
3. **LLM Service** provides centralized LLM access and prompt management
4. **Hello LLM** serves as a simple testing ground and demo

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- API keys for OpenAI and/or Anthropic

### 1. Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd engineering-lab

# Copy environment template
cp .env.example .env

# Add your API keys to .env
# OPENAI_API_KEY=your-openai-key
# ANTHROPIC_API_KEY=your-anthropic-key
```

### 2. Agent Alignment Framework (Core Library)
```bash
cd agent-alignment-framework

# Install dependencies
pip install -e .

# Run tests
python scripts/run_tests.py

# Try the compatibility demo
cd examples/compatibility
python demo.py
```

### 3. Agent Alignment UI (Full Application)
```bash
cd agent-alignment-ui

# Start backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001

# Start frontend (new terminal)
cd frontend
npm install
npm start
```

Visit `http://localhost:3000` for the interactive UI.

### 4. LLM Service (Optional)
```bash
cd llm-service
pip install -r requirements.txt
# Configure and run as needed
```

## 📊 Use Cases & Examples

### Product Compatibility Evaluation
Evaluate whether two products are compatible using multiple AI agents:
- **Advocate Agent**: Argues for compatibility
- **Skeptic Agent**: Identifies potential issues
- **Judge Agent**: Makes final determination
- **System**: Analyzes alignment and escalates disagreements

### Content Moderation
Multi-perspective content analysis:
- Different agents evaluate content from various angles
- Alignment analysis identifies consensus vs. disagreement
- Human review triggered for disputed cases

### Risk Assessment
Comprehensive risk evaluation:
- Multiple agents assess different risk dimensions
- Confidence scoring and evidence collection
- Alignment analysis for decision confidence

## 🧪 Testing & Development

### Framework Testing
```bash
cd agent-alignment-framework
python scripts/run_tests.py                    # Deterministic tests
python scripts/live_llm_smoke_test.py         # Live LLM tests (optional)
```

### UI Testing
```bash
cd agent-alignment-ui
python tests/test_system_integration.py       # Full system test
python tests/test_frontend_runtime.py         # Frontend stability
python tests/test_shared_env_integration.py   # Environment integration
```

### Development Workflow
1. **Framework Development**: Work in `agent-alignment-framework/` for core logic
2. **UI Development**: Work in `agent-alignment-ui/` for interface and user experience
3. **Integration Testing**: Use provided test suites to verify end-to-end functionality
4. **Live Testing**: Use Hello LLM for quick experiments and LLM Service for production scenarios

## 📚 Documentation

- **[Agent Alignment Framework](./agent-alignment-framework/README.md)**: Core library documentation
- **[Framework Positioning](./agent-alignment-framework/docs/positioning.md)**: Philosophy and design principles
- **[Testing Guide](./agent-alignment-framework/docs/testing.md)**: Testing strategies and best practices
- **[Agent Alignment UI](./agent-alignment-ui/README.md)**: Full-stack application guide
- **[Evaluation History](./agent-alignment-ui/docs/evaluation-history.md)**: History management guide

## 🤝 Contributing

1. **Framework Contributions**: Focus on `agent-alignment-framework/` for core functionality
2. **UI Contributions**: Work in `agent-alignment-ui/` for user interface improvements
3. **Service Contributions**: Enhance `llm-service/` for provider integrations
4. **Testing**: Add tests for new features and ensure existing tests pass
5. **Documentation**: Update relevant documentation for changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔧 Architecture Notes

### Design Principles
- **Separation of Concerns**: Framework, UI, and services are clearly separated
- **Provider Agnostic**: Works with multiple LLM providers
- **Extensible**: Easy to add new agent types, decision schemas, and evaluation criteria
- **Observable**: Comprehensive logging, monitoring, and result visualization
- **Human-Centric**: Built-in human-in-the-loop capabilities for disputed decisions

### Deployment Options
- **Development**: Run components locally with provided scripts
- **Production**: Deploy backend and frontend separately, use external databases
- **Hybrid**: Use framework as library in existing applications

This engineering lab provides a complete foundation for building sophisticated multi-agent AI systems with proper alignment analysis, user interfaces, and production-ready components.