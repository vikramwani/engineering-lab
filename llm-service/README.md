# LLM Compatibility Service

A production-ready FastAPI microservice that leverages Large Language Models to evaluate product compatibility relationships using a sophisticated multi-agent debate architecture. The service provides intelligent compatibility analysis between products with structured JSON responses, confidence scoring, and comprehensive relationship classification.

## 🚀 Overview

This service analyzes two products and determines their compatibility relationship using a **multi-agent debate system** powered by OpenAI's GPT models. It's designed for e-commerce platforms, inventory management systems, and product recommendation engines that need to understand how products relate to each other.

### Multi-Agent Debate Architecture

The service employs a sophisticated three-agent debate system:

1. **Advocate Agent**: Argues FOR compatibility, finding evidence that products work together
2. **Skeptic Agent**: Argues AGAINST compatibility, identifying potential issues and incompatibilities  
3. **Judge Agent**: Resolves the debate by weighing both perspectives and making a final decision

This architecture provides:
- **More robust evaluations** through multiple perspectives
- **Calibrated confidence** based on agent agreement/disagreement
- **Better explainability** with clear reasoning from each perspective
- **Reduced bias** by considering both positive and negative evidence

### Key Capabilities

- **Intelligent Multi-Agent Analysis**: Debate-style evaluation with advocate, skeptic, and judge agents
- **Structured Output**: Returns standardized JSON with compatibility status, relationship type, confidence scores, and evidence
- **Production Ready**: Includes authentication, logging, error handling, and monitoring
- **Robust Validation**: Handles edge cases, normalizes confidence values, and validates all inputs
- **Comprehensive Testing**: Includes validation scripts and health checks
- **Clean Architecture**: Separation of configuration, prompts, and business logic

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                          │
│                   (API Layer & Routing)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                CompatibilityService                             │
│              (Multi-Agent Orchestrator)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────────────────────┐
        ▼             ▼             ▼                             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐         ┌─────────────┐
│ Advocate    │ │ Skeptic     │ │ Judge       │         │ Config &    │
│ Agent       │ │ Agent       │ │ Agent       │         │ Prompts     │
│             │ │             │ │             │         │             │
│ Argues FOR  │ │ Argues      │ │ Resolves    │         │ Versioned   │
│ Compatibility│ │ AGAINST     │ │ Debate      │         │ Disk-based  │
└─────────────┘ └─────────────┘ └─────────────┘         └─────────────┘
        │             │             │                             │
        └─────────────┼─────────────┘                             │
                      ▼                                           │
                ┌─────────────────────────┐                       │
                │    Final Decision       │◄──────────────────────┘
                │  (CompatibilityResponse)│
                └─────────────────────────┘
```

### Components

- **API Layer**: FastAPI application with routing, middleware, and error handling
- **Multi-Agent Service**: Orchestrates debate between advocate, skeptic, and judge agents
- **Agent System**: Specialized agents with individual prompts and reasoning capabilities
- **Configuration Management**: Environment-based settings with immutable defaults
- **Prompt Management**: Versioned, disk-based prompts separated from business logic
- **LLM Client**: Multi-provider support (OpenAI/XAI/Local) with retry logic and timeout handling
- **Authentication**: API key-based security
- **Logging**: Structured JSON logging with request tracing and agent-level observability

---

## 📋 API Reference

### Health Check

**GET** `/health`

Simple health check endpoint for monitoring and load balancers.

**Response**
```json
{
  "status": "ok"
}
```

### Text Generation

**POST** `/generate`

Generate text using the LLM service directly.

**Headers**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Request Body**
```json
{
  "prompt": "Your text prompt here",
  "max_tokens": 256
}
```

**Response**
```json
{
  "request_id": "uuid-string",
  "output": "Generated text response",
  "latency_ms": 1250
}
```

### Compatibility Evaluation

**POST** `/compatibility/evaluate`

Evaluate compatibility between two products with detailed analysis.

**Headers**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Request Body**
```json
{
  "product_a": {
    "id": "A1",
    "title": "ACME Air Purifier Model X",
    "category": "air_purifier",
    "brand": "ACME",
    "attributes": {
      "model": "X",
      "filter_type": "HEPA"
    }
  },
  "product_b": {
    "id": "B1", 
    "title": "ACME HEPA Replacement Filter for Model X",
    "category": "filter",
    "brand": "ACME",
    "attributes": {
      "compatible_models": ["X"],
      "filter_type": "HEPA"
    }
  }
}
```

**Response**
```json
{
  "compatible": true,
  "relationship": "replacement_filter",
  "confidence": 0.95,
  "explanation": "Product B is a replacement filter specifically designed for Product A's air purifier model.",
  "evidence": [
    "Product B title explicitly mentions compatibility with Model X",
    "Both products share the same HEPA filter type",
    "Product B attributes list Model X in compatible_models"
  ]
}
```

### Compatibility Explanation (Detailed Analysis)

**POST** `/compatibility/explain`

Get detailed explanation of compatibility evaluation with per-agent decisions and alignment analysis.

**Headers**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Request Body**
Same as `/compatibility/evaluate`

**Response**
```json
{
  "final_decision": {
    "compatible": true,
    "relationship": "replacement_filter",
    "confidence": 0.95,
    "explanation": "Final decision based on multi-agent analysis...",
    "evidence": ["Evidence point 1", "Evidence point 2"]
  },
  "agent_decisions": [
    {
      "agent_name": "Advocate Agent",
      "compatible": true,
      "relationship": "replacement_filter",
      "confidence": 0.92,
      "explanation": "Advocate's reasoning...",
      "evidence": ["Supporting evidence 1", "Supporting evidence 2"],
      "reasoning": "Detailed reasoning from advocate perspective"
    },
    {
      "agent_name": "Skeptic Agent", 
      "compatible": true,
      "relationship": "replacement_filter",
      "confidence": 0.88,
      "explanation": "Skeptic's reasoning...",
      "evidence": ["Counter-evidence considered"],
      "reasoning": "Detailed reasoning from skeptic perspective"
    },
    {
      "agent_name": "Judge Agent",
      "compatible": true,
      "relationship": "replacement_filter", 
      "confidence": 0.95,
      "explanation": "Judge's final reasoning...",
      "evidence": ["Reconciled evidence"],
      "reasoning": "Final decision rationale"
    }
  ],
  "alignment_summary": {
    "compatible_agreement": true,
    "relationship_agreement": true,
    "confidence_spread": 0.04,
    "avg_confidence": 0.92,
    "disagreement_areas": []
  },
  "request_id": "abc123"
}
```

---

## 🎨 Web UI for Testing

The service includes a lightweight web interface for testing and debugging compatibility evaluations.

### Accessing the UI

Navigate to `http://localhost:8000/` when the service is running to access the testing interface.

### UI Features

- **Interactive Product Input**: Editable forms for Product A and Product B with JSON attribute editing
- **Dual Evaluation Modes**: 
  - **Evaluate**: Quick compatibility assessment
  - **Explain**: Detailed multi-agent analysis with per-agent decisions
- **Visual Results Display**: 
  - Compatibility status with color-coded badges
  - Confidence scores with visual indicators
  - Evidence lists and explanations
  - Agent decision breakdown (explain mode)
  - Alignment analysis showing agent agreement/disagreement
- **Real-time Testing**: Immediate API calls with loading states and error handling
- **Responsive Design**: Works on desktop and mobile devices

### Using the UI

1. **Enter Product Information**: Fill in the product details for both products
2. **Choose Evaluation Type**:
   - Click **"Evaluate Compatibility"** for basic assessment
   - Click **"Explain Compatibility"** for detailed multi-agent analysis
3. **Review Results**: 
   - Basic results show final decision, relationship, and confidence
   - Detailed results show individual agent decisions and alignment analysis
4. **Clear and Repeat**: Use "Clear Results" to reset and test new product combinations

The UI is perfect for:
- **Development Testing**: Quick validation of service functionality
- **Demo Purposes**: Showcasing the multi-agent debate system
- **Debugging**: Understanding how agents reach their decisions
- **API Exploration**: Learning the request/response formats

---

## 🔗 Relationship Types

The service classifies product relationships into these standardized categories:

| Relationship | Description | Example |
|--------------|-------------|---------|
| `replacement_filter` | Product B replaces a regularly changed component | Air purifier + replacement filter |
| `replacement_part` | Product B replaces a fixed internal component | Laptop + replacement battery |
| `accessory` | Product B adds optional functionality | Camera + lens attachment |
| `consumable` | Product B is used up over time | Printer + ink cartridge |
| `power_supply` | Product B provides electrical power | Device + charger |
| `not_compatible` | Products are explicitly incompatible | iPhone case + Android phone |
| `insufficient_information` | Cannot determine relationship | Unclear or missing product details |

---

## 🔐 Authentication & Security

### API Key Authentication

All endpoints (except `/health`) require a valid API key in the `X-API-Key` header.

**Security Features:**
- API key validation on every request
- Request ID tracking for audit trails
- Structured logging without sensitive data exposure
- Input validation and sanitization

### Error Responses

| Status Code | Description | When It Occurs |
|-------------|-------------|----------------|
| `200` | Success | Valid request processed successfully |
| `401` | Unauthorized | Missing or invalid API key |
| `422` | Unprocessable Entity | Invalid request body or validation errors |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server errors |
| `503` | Service Unavailable | LLM service temporarily unavailable |
| `504` | Gateway Timeout | LLM request timed out |

---

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.9+
- OpenAI API key
- Service API key (for authentication)

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key
SERVICE_API_KEY=your-service-api-key

# Optional (with defaults)
MODEL=gpt-4o-mini
DEFAULT_MAX_TOKENS=256
REQUEST_TIMEOUT_SECONDS=15
```

### Installation

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd llm-service
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the service:**
   ```bash
   uvicorn src.api:app --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .

EXPOSE 8000
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🧪 Testing & Validation

### Validation Scripts

The project includes comprehensive validation scripts:

```bash
# Test core service functionality
python3 scripts/validate_service.py

# Test compatibility evaluation
python3 scripts/validate_compatibility.py
```

### Test Coverage

- ✅ Health endpoint functionality
- ✅ Authentication (missing/invalid API keys)
- ✅ Text generation with proper response structure
- ✅ Compatibility evaluation with real product data
- ✅ Input validation and error handling
- ✅ Confidence score normalization
- ✅ Relationship classification accuracy

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# Access web UI
open http://localhost:8000/

# Generate text
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world"}'

# Evaluate compatibility
curl -X POST http://localhost:8000/compatibility/evaluate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# Get detailed explanation
curl -X POST http://localhost:8000/compatibility/explain \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

---

## 📊 Monitoring & Observability

### Structured Logging

The service uses structured JSON logging with the following fields:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "llm_service",
  "message": "request_completed",
  "event": "request_completed",
  "request_id": "uuid-string",
  "method": "POST",
  "path": "/compatibility/evaluate",
  "status_code": 200,
  "latency_ms": 1250
}
```

### Key Metrics to Monitor

- **Request latency**: Track response times for performance
- **Error rates**: Monitor 4xx/5xx responses
- **LLM availability**: Track 503/504 errors
- **Confidence scores**: Monitor evaluation quality
- **Request volume**: Track usage patterns

### Health Monitoring

- **Health endpoint**: `/health` for load balancer checks
- **Request IDs**: Every request gets a unique ID for tracing
- **Error context**: Detailed error logging without sensitive data

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key for LLM access |
| `SERVICE_API_KEY` | ✅ | - | API key for service authentication |
| `MODEL` | ❌ | `gpt-4o-mini` | OpenAI model to use |
| `DEFAULT_MAX_TOKENS` | ❌ | `256` | Default token limit for responses |
| `REQUEST_TIMEOUT_SECONDS` | ❌ | `15` | Timeout for LLM requests |

### Performance Tuning

- **Timeout settings**: Adjust `REQUEST_TIMEOUT_SECONDS` based on your needs
- **Token limits**: Set `DEFAULT_MAX_TOKENS` to balance cost and quality
- **Model selection**: Choose between speed (`gpt-4o-mini`) and quality (`gpt-4`)
- **Retry logic**: Built-in exponential backoff for LLM failures

---

## 🚀 Production Deployment

### Deployment Checklist

- [ ] Set production API keys in environment
- [ ] Configure proper logging aggregation
- [ ] Set up health check monitoring
- [ ] Configure rate limiting (if needed)
- [ ] Set up SSL/TLS termination
- [ ] Configure backup/failover for LLM service
- [ ] Set up metrics collection and alerting

### Scaling Considerations

- **Stateless design**: Service can be horizontally scaled
- **LLM rate limits**: Monitor OpenAI usage and implement queuing if needed
- **Memory usage**: Minimal memory footprint, suitable for containerization
- **Database**: No persistent storage required (stateless)

---

## 🤝 Contributing

### Development Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install black flake8 mypy pytest
   ```

2. Run code formatting:
   ```bash
   black src/
   flake8 src/
   mypy src/
   ```

3. Run tests:
   ```bash
   python3 scripts/validate_service.py
   python3 scripts/validate_compatibility.py
   ```

### Code Standards

- **PEP 8**: Follow Python style guidelines
- **Type hints**: Use type annotations for all functions
- **Docstrings**: Document all public methods and classes
- **Error handling**: Proper exception handling with logging
- **Testing**: Validate all changes with provided scripts

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support

For issues, questions, or contributions:

1. Check existing issues in the repository
2. Create a new issue with detailed description
3. Include logs and error messages when reporting bugs
4. Provide minimal reproduction steps

### Common Issues

**Authentication Errors (401)**
- Verify `SERVICE_API_KEY` is set correctly
- Check `X-API-Key` header is included in requests

**LLM Errors (503/504)**
- Verify `OPENAI_API_KEY` is valid and has credits
- Check OpenAI service status
- Review timeout settings

**Validation Errors (422)**
- Ensure request body matches expected schema
- Check product objects have required fields (id, title, category, brand)
