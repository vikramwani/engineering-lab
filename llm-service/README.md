# LLM Compatibility Service

A production-ready FastAPI microservice that leverages Large Language Models to evaluate product compatibility relationships. The service provides intelligent compatibility analysis between products with structured JSON responses, confidence scoring, and comprehensive relationship classification.

## 🚀 Overview

This service analyzes two products and determines their compatibility relationship using OpenAI's GPT models. It's designed for e-commerce platforms, inventory management systems, and product recommendation engines that need to understand how products relate to each other.

### Key Capabilities

- **Intelligent Analysis**: Uses LLM reasoning to understand complex product relationships
- **Structured Output**: Returns standardized JSON with compatibility status, relationship type, confidence scores, and evidence
- **Production Ready**: Includes authentication, logging, error handling, and monitoring
- **Robust Validation**: Handles edge cases, normalizes confidence values, and validates all inputs
- **Comprehensive Testing**: Includes validation scripts and health checks

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│  Compatibility   │────│   LLM Client    │
│   (API Layer)   │    │     Service      │    │  (OpenAI API)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
    ┌─────────┐              ┌──────────┐           ┌──────────────┐
    │  Auth   │              │  Models  │           │    Config    │
    │ Module  │              │ & Prompt │           │  & Settings  │
    └─────────┘              └──────────┘           └──────────────┘
```

### Components

- **API Layer**: FastAPI application with routing, middleware, and error handling
- **Compatibility Service**: Core business logic for product analysis
- **LLM Client**: OpenAI integration with retry logic and timeout handling
- **Authentication**: API key-based security
- **Configuration**: Environment-based settings management
- **Logging**: Structured JSON logging with request tracing

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
