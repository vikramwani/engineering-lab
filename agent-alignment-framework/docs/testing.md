# Testing Framework

The Agent Alignment Framework uses a multi-layered testing approach that clearly separates deterministic core validation from non-deterministic integration testing.

## Test Categories

### 1. Deterministic Core Tests ✅

**Purpose**: Validate framework correctness, logic, and contracts

**Characteristics**:
- **Deterministic**: Same inputs always produce identical outputs
- **Fast**: No external API calls or network dependencies
- **Reliable**: Never flaky, always pass/fail consistently
- **CI/CD Ready**: Safe to run in automated pipelines
- **Required**: Must pass for framework to be considered working

**Test Files**:
- `validate_framework.py` - Core framework validation (9 tests)
- `example_usage.py` - End-to-end demo with mock LLM
- `simple_hitl_demo.py` - HITL escalation contract validation

**What They Test**:
- ✅ Model validation and serialization
- ✅ Decision schema validation (Boolean, Categorical, Scalar, Free-form)
- ✅ Alignment analysis algorithms (deterministic scoring)
- ✅ Alignment state detection (Full, Soft, Hard, Insufficient)
- ✅ HITL escalation contract (pure functions)
- ✅ Agent orchestration logic
- ✅ Error handling and edge cases
- ✅ Public API surface and backward compatibility

**Mock Components**:
- Mock LLM providers that return predictable responses
- Deterministic agent decisions for alignment testing
- Controlled scenarios for each alignment state

### 2. Non-Deterministic Integration Tests ⚠️

**Purpose**: Validate real-world LLM integration and end-to-end functionality

**Characteristics**:
- **Non-Deterministic**: Results vary between runs due to LLM variability
- **Slow**: Makes real API calls to LLM providers
- **Potentially Flaky**: LLM responses can vary significantly
- **Cost**: Uses real API credits/tokens
- **Optional**: Framework correctness is NOT dependent on these tests

**Test Files**:
- `scripts/live_llm_smoke_test.py` - Live LLM integration validation

**What They Test**:
- 🔄 Real LLM provider integration (OpenAI, Anthropic, Local)
- 🔄 End-to-end evaluation pipeline with actual LLM responses
- 🔄 Agent prompt processing and response parsing
- 🔄 Network resilience and error handling
- 🔄 Performance under realistic conditions

**Important Notes**:
- **NOT required for framework validation**
- **NOT included in CI/CD pipelines**
- **Results will vary between runs**
- **Requires valid API keys**
- **Can be safely skipped**

## Test Execution

### Running Core Tests (Required)

```bash
# Run all deterministic core tests
python validate_framework.py

# Run example with mock LLM
python example_usage.py

# Run HITL contract demo
python simple_hitl_demo.py
```

**Expected Results**: All tests should pass consistently with identical outputs.

### Running Integration Tests (Optional)

```bash
# Set up API keys (choose one)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="ant-..."

# Run live LLM smoke test
python scripts/live_llm_smoke_test.py --provider openai
python scripts/live_llm_smoke_test.py --provider anthropic
```

**Expected Results**: Tests may pass or fail depending on LLM responses. Failures do NOT indicate framework issues.

## Framework Guarantees

The Agent Alignment Framework provides these **deterministic guarantees** validated by core tests:

### Core Logic Guarantees
- ✅ **Deterministic Alignment Analysis**: Same agent decisions → Same alignment state
- ✅ **Consistent Scoring**: Alignment scores are reproducible and explainable
- ✅ **Pure Functions**: Core logic has no side effects or external dependencies
- ✅ **Schema Validation**: All decision types are properly validated
- ✅ **Error Handling**: Graceful degradation and clear error messages

### HITL Contract Guarantees
- ✅ **Deterministic Escalation**: Same alignment state → Same escalation decision
- ✅ **Complete Context**: All agent decisions and reasoning preserved
- ✅ **Serializable Payloads**: Full JSON serialization support
- ✅ **Domain Agnostic**: No hardcoded domain logic
- ✅ **Backward Compatible**: Existing integrations continue working

### API Stability Guarantees
- ✅ **Public API**: Stable interfaces with semantic versioning
- ✅ **Model Compatibility**: Pydantic models maintain field compatibility
- ✅ **Import Paths**: Core imports remain stable across versions
- ✅ **Configuration**: Settings and thresholds are configurable

## What Tests DON'T Guarantee

The framework **does NOT guarantee**:

- ❌ **LLM Response Quality**: Framework cannot control LLM output quality
- ❌ **Specific Decisions**: Actual evaluation outcomes depend on LLM responses
- ❌ **Response Times**: LLM API latency is external to the framework
- ❌ **API Availability**: LLM provider uptime is not framework responsibility
- ❌ **Cost Control**: Token usage depends on prompt complexity and LLM responses

## Test Development Guidelines

### Adding Deterministic Tests

When adding new core functionality:

1. **Write deterministic tests first** using mock components
2. **Test all edge cases** with controlled inputs
3. **Validate error conditions** with invalid inputs
4. **Ensure reproducibility** - same inputs must produce same outputs
5. **Add to `validate_framework.py`** for inclusion in core test suite

### Adding Integration Tests

When adding LLM provider support:

1. **Add to smoke test** for basic integration validation
2. **Mark as non-deterministic** in documentation
3. **Include error handling** for API failures
4. **Make optional** - don't break core functionality if unavailable
5. **Document API requirements** (keys, models, etc.)

## Continuous Integration

### CI Pipeline Tests (Required)
```yaml
# Example CI configuration
test:
  script:
    - python validate_framework.py
    - python example_usage.py  
    - python simple_hitl_demo.py
  # Only run deterministic tests in CI
```

### Local Development Tests (Optional)
```bash
# Full test suite including live LLM tests
make test-all

# Core tests only (CI equivalent)
make test-core

# Live LLM tests only (requires API keys)
make test-integration
```

## Debugging Test Failures

### Core Test Failures
- **Always investigate** - indicates framework regression
- **Check for breaking changes** in core logic
- **Validate model compatibility** if Pydantic errors
- **Review alignment algorithm** if scoring inconsistencies

### Integration Test Failures
- **Usually not framework issues** - often LLM API problems
- **Check API keys and quotas** first
- **Verify network connectivity** to LLM providers
- **Review LLM response parsing** if JSON errors
- **Consider LLM response variability** - may need multiple runs

## Test Maintenance

### Regular Maintenance
- **Run core tests** before every commit
- **Update mock responses** when changing agent prompts
- **Validate backward compatibility** when changing models
- **Review test coverage** for new functionality

### Release Testing
- **Full core test suite** must pass
- **Integration tests** should be attempted but failures are acceptable
- **Performance benchmarks** using mock LLMs
- **Documentation examples** must work with current API

This testing approach ensures the framework core is rock-solid and deterministic while allowing flexibility for real-world LLM integration challenges.