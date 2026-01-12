# Agent Alignment UI - Test Suite

This directory contains comprehensive tests for the Agent Alignment UI system.

## Test Files

### `test_system_integration.py`
**Purpose**: End-to-end system integration testing  
**Coverage**: 
- Backend health checks
- API key management functionality
- Complete evaluation pipeline
- Data persistence verification
- Frontend component integration

**Usage**:
```bash
# Ensure both backend and frontend are running
cd agent-alignment-ui
python tests/test_system_integration.py
```

### `test_frontend_runtime.py`
**Purpose**: Frontend runtime stability and API proxy testing  
**Coverage**:
- Frontend page loading without runtime errors
- API endpoint accessibility through proxy
- Data structure validation
- Error handling verification

**Usage**:
```bash
# Ensure frontend is running on localhost:3000
python tests/test_frontend_runtime.py
```

### `test_shared_env_integration.py`
**Purpose**: Shared environment configuration testing  
**Coverage**:
- API key preloading from root `.env` file
- Real LLM evaluation functionality
- Multi-agent system verification
- Environment variable integration

**Usage**:
```bash
# Ensure backend is running and .env is configured
python tests/test_shared_env_integration.py
```

### `test_display_format.py`
**Purpose**: Display format logic verification  
**Coverage**:
- "Compatible (Relationship)" format testing
- Edge case handling
- Fallback behavior verification

**Usage**:
```bash
# Standalone test, no server required
python tests/test_display_format.py
```

## Running All Tests

```bash
cd agent-alignment-ui

# Start backend (terminal 1)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001

# Start frontend (terminal 2)
cd frontend
npm start

# Run tests (terminal 3)
python tests/test_system_integration.py
python tests/test_frontend_runtime.py
python tests/test_shared_env_integration.py
python tests/test_display_format.py
```

## Test Requirements

- **Backend**: Must be running on `localhost:8001`
- **Frontend**: Must be running on `localhost:3000`
- **Environment**: Root `.env` file with valid API keys
- **Dependencies**: `requests` library for HTTP testing

## Expected Results

All tests should pass when:
- ✅ Backend and frontend are properly configured and running
- ✅ API keys are valid and loaded from shared `.env`
- ✅ All components are functioning without runtime errors
- ✅ Display format logic is working correctly