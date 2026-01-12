# Agent Alignment UI

A generic web-based visualization interface for Agent Alignment Framework evaluations. This UI provides comprehensive visualization of multi-agent decisions, alignment analysis, and HITL escalation workflows.

## Overview

The Agent Alignment UI is a **domain-agnostic visualization tool** that can display results from any Agent Alignment Framework evaluation, including:

- **Multi-agent decisions** with confidence scoring and evidence
- **Alignment analysis** with visual disagreement detection
- **HITL escalation requests** with complete context
- **Interactive exploration** of agent reasoning and evidence
- **Real-time evaluation** with live agent orchestration

## Features

### 🎯 Multi-Agent Visualization
- **Agent Decision Cards** showing individual agent outputs
- **Confidence Visualization** with color-coded confidence levels
- **Evidence Display** with expandable evidence lists
- **Role-based Styling** (advocate, skeptic, judge, expert)

### 📊 Alignment Analysis Dashboard
- **Alignment State Indicators** (Full, Soft, Hard, Insufficient)
- **Confidence Distribution Charts** showing agent agreement patterns
- **Disagreement Area Breakdown** with detailed analysis
- **Consensus Strength Meters** with visual indicators

### 🚨 HITL Integration
- **Escalation Alerts** when human review is required
- **Complete Context Display** with all agent decisions
- **Review Interface** for human decision input
- **Escalation History** tracking and audit trails

### 🔄 Interactive Features
- **Live Evaluation** - Run evaluations directly from the UI
- **Scenario Comparison** - Compare multiple evaluation results
- **Export Functionality** - Download results as JSON/PDF
- **Responsive Design** - Works on desktop, tablet, and mobile

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Alignment UI                          │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   React     │  │   FastAPI   │  │   Agent     │            │
│  │  Frontend   │  │   Backend   │  │ Alignment   │            │
│  │             │  │             │  │ Framework   │            │
│  │ • Visualiz. │  │ • API       │  │             │            │
│  │ • Interact. │  │ • WebSocket │  │ • Multi-    │            │
│  │ • HITL UI   │  │ • File I/O  │  │   agent     │            │
│  │             │  │             │  │ • Alignment │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend**:
- **React 18** with TypeScript for type safety
- **Material-UI (MUI)** for consistent design system
- **Recharts** for data visualization and charts
- **React Query** for API state management
- **WebSocket** for real-time updates

**Backend**:
- **FastAPI** for high-performance API server
- **WebSocket** support for real-time communication
- **Pydantic** for data validation and serialization
- **Agent Alignment Framework** integration

## Quick Start

### Prerequisites

```bash
# Backend requirements
Python 3.9+
pip install -r requirements.txt

# Frontend requirements  
Node.js 18+
npm install
```

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd agent-alignment-ui

# Backend setup
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY="your-openai-key"
uvicorn main:app --reload --port 8000

# Frontend setup (new terminal)
cd frontend
npm install
npm start
```

### Production Deployment

```bash
# Docker deployment
docker-compose up -d

# Or manual deployment
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
cd frontend && npm run build && serve -s build -l 3000
```

## Usage Examples

### 1. Visualizing Compatibility Evaluation

```python
# Run compatibility evaluation
from agent_alignment_framework.examples.compatibility import CompatibilityEvaluator

evaluator = CompatibilityEvaluator()
result = evaluator.evaluate_compatibility(product_a, product_b)

# Send to UI via API
import requests
response = requests.post("http://localhost:8000/api/evaluations", json=result)
```

### 2. Live Evaluation Interface

```typescript
// React component for live evaluation
const LiveEvaluationPanel = () => {
  const [evaluation, setEvaluation] = useState(null);
  
  const runEvaluation = async (taskData) => {
    const response = await fetch('/api/evaluate', {
      method: 'POST',
      body: JSON.stringify(taskData)
    });
    const result = await response.json();
    setEvaluation(result);
  };
  
  return (
    <EvaluationVisualization evaluation={evaluation} />
  );
};
```

### 3. HITL Review Interface

```typescript
// HITL review component
const HITLReviewPanel = ({ hitlRequest }) => {
  const submitReview = async (decision) => {
    await fetch(`/api/hitl/${hitlRequest.request_id}/review`, {
      method: 'POST',
      body: JSON.stringify({
        decision,
        rationale: reviewRationale,
        reviewer_id: currentUser.id
      })
    });
  };
  
  return (
    <HITLReviewInterface 
      request={hitlRequest}
      onSubmit={submitReview}
    />
  );
};
```

## API Reference

### Evaluation Endpoints

```http
POST /api/evaluations
Content-Type: application/json

{
  "task_id": "eval-001",
  "task_type": "compatibility",
  "context": {...},
  "decision_schema": {...}
}
```

### WebSocket Events

```javascript
// Connect to real-time updates
const ws = new WebSocket('ws://localhost:8000/ws');

// Listen for evaluation updates
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.type === 'evaluation_progress') {
    updateEvaluationProgress(update.data);
  }
};
```

### HITL Endpoints

```http
GET /api/hitl/requests
POST /api/hitl/{request_id}/review
GET /api/hitl/{request_id}/status
```

## Component Library

### Core Components

```typescript
// Agent decision visualization
<AgentDecisionCard 
  decision={agentDecision}
  showEvidence={true}
  expandable={true}
/>

// Alignment analysis display
<AlignmentAnalysis 
  summary={alignmentSummary}
  showCharts={true}
  interactive={true}
/>

// HITL escalation alert
<HITLEscalationAlert 
  request={hitlRequest}
  onReview={handleReview}
  severity="high"
/>

// Evaluation timeline
<EvaluationTimeline 
  evaluations={evaluationHistory}
  onSelect={handleSelect}
/>
```

### Visualization Components

```typescript
// Confidence distribution chart
<ConfidenceChart 
  data={confidenceData}
  type="bar"
  animated={true}
/>

// Alignment state indicator
<AlignmentStateIndicator 
  state={alignmentState}
  size="large"
  showLabel={true}
/>

// Evidence network graph
<EvidenceNetworkGraph 
  evidence={evidenceData}
  interactive={true}
  clustered={true}
/>
```

## Configuration

### Environment Variables

```bash
# Backend configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=ant-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
LOG_LEVEL=INFO

# Frontend configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=development
```

### UI Themes

```typescript
// Custom theme configuration
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    alignment: {
      full: '#4caf50',
      soft: '#ff9800', 
      hard: '#f44336',
      insufficient: '#9e9e9e',
    }
  }
});
```

## Testing

### Frontend Tests

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e
```

### Backend Tests

```bash
# API tests
pytest tests/test_api.py -v

# WebSocket tests
pytest tests/test_websocket.py -v

# Integration tests
pytest tests/test_integration.py -v
```

## Performance Considerations

### Optimization Strategies
- **Virtual scrolling** for large evaluation lists
- **Lazy loading** of detailed agent decisions
- **Caching** of frequent evaluation results
- **WebSocket connection pooling** for real-time updates

### Monitoring
- **Performance metrics** (render time, API latency)
- **User interaction tracking** (clicks, navigation)
- **Error monitoring** with detailed stack traces
- **Real-time usage analytics**

## Deployment

### Docker Deployment

```dockerfile
# Multi-stage build for production
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim as backend
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/build ./static

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-alignment-ui
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-alignment-ui
  template:
    metadata:
      labels:
        app: agent-alignment-ui
    spec:
      containers:
      - name: ui
        image: agent-alignment-ui:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-api-key
```

## Contributing

1. Follow React and FastAPI best practices
2. Add tests for new components and endpoints
3. Update documentation for changes
4. Ensure responsive design compatibility
5. Test with multiple evaluation types

## Roadmap

### Phase 1: Core Visualization ✅
- Agent decision display
- Alignment analysis charts
- Basic HITL interface

### Phase 2: Interactive Features 🔄
- Live evaluation interface
- Real-time WebSocket updates
- Advanced filtering and search

### Phase 3: Advanced Analytics 📋
- Historical trend analysis
- Performance benchmarking
- Custom dashboard creation

### Phase 4: Enterprise Features 📋
- Multi-tenant support
- Advanced security features
- Integration with external systems

---

The Agent Alignment UI provides a comprehensive, domain-agnostic interface for visualizing and interacting with multi-agent evaluations, making the Agent Alignment Framework accessible to both technical and non-technical users.