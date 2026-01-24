# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SchemaBuilder is a FastAPI backend for generating JSON schemas from sample JSON data. It provides schema inference, quality scoring, validation, structural analysis, and mock data generation.

## Common Commands

```bash
# Install dependencies
poetry install

# Run the API server
poetry run uvicorn src.api.main:app --reload

# Run all tests
poetry run pytest

# Run a single test file
poetry run pytest tests/unit/test_scoring/test_scoring_engine.py

# Run a specific test
poetry run pytest tests/unit/test_scoring/test_scoring_engine.py::test_score_schema -v

# Run tests with coverage
poetry run pytest --cov=src tests/

# Format code
poetry run black src tests
```

## Architecture

### Layer Structure

```
API Layer (src/api/)
    ↓ Depends()
Business Logic Layer (src/bl/)
    ↓ uses
Domain Layer (src/domain/) ← interfaces & models
    ↑ implements
Infrastructure Layer (src/infrastructure/) ← external services
```

### Key Services and Data Flow

**Schema Building Flow** (`POST /schemas/build`):
1. `GroupedSchemaBuilder` orchestrates the full pipeline
2. `SchemaAnalyzer` detects structural conflicts → recommends split/merge
3. `SchemaInferrer` generates schema for each object using `PATTERN_REGISTRY`
4. `SchemaMerger` combines schemas (uses `anyOf` for incompatible types)
5. `RegexInjector` adds AI-generated patterns (when enabled)
6. `ScoringEngine` evaluates quality (strictness, completeness, ambiguity, security)
7. `SchemaValidator` validates input data against generated schema

### Business Logic Modules (`src/bl/`)

| Module | Service | Purpose |
|--------|---------|---------|
| `builder/` | `SchemaBuilderService` | Schema inference, merging, AI regex injection |
| `analyzer/` | `SchemaAnalyzer` | Structural analysis, similarity calculation, grouping |
| `scoring/` | `ScoringEngine` | Quality scoring with weighted rules |
| `validator/` | `SchemaValidator` | JSON Schema validation with error formatting |
| `generator/` | `GeneratorService` | Mock data generation, regex synthesis |

### Dependency Injection

Services are composed via FastAPI's `Depends()` in `src/api/main.py`:
```python
def get_schema_service(ai: IAIService = Depends(get_ai_service)) -> ISchemaService:
    return SchemaBuilderService(ai_service=ai)
```

### Configuration

- **Pattern definitions**: `config/patterns.yaml` (email, UUID, date, etc.)
- **Scoring weights**: `src/bl/scoring/config/weights.py`
- **Environment**: `.env` file with `ENABLE_AI`, `OPENAI_API_KEY`

## Code Patterns

- Domain interfaces in `src/domain/interfaces.py` define contracts (`ISchemaService`, `IAIService`)
- Custom exceptions inherit from `SchemaBuilderError` with `to_dict()` for API responses
- All modules use `LoggerFactory.get_logger(__name__)` for logging
- Pydantic models handle request/response validation
- YAML configs loaded via `src/core/config_loader.py`

## Testing

- Unit tests mirror source structure: `tests/unit/test_builder/`, `tests/unit/test_scoring/`, etc.
- Integration tests use `httpx.ASGITransport` for full API testing
- Fixtures in `tests/conftest.py`: `MockAIService`, `FailingAIService`, sample data objects
- Test async endpoints with `@pytest.mark.asyncio`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_AI` | Enable AI-powered regex generation | `false` |
| `OPENAI_API_KEY` | OpenAI API key (required if AI enabled) | - |
