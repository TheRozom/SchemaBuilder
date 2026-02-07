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
5. `ScoringEngine` evaluates quality (strictness, completeness, ambiguity, security)
6. `SchemaValidator` validates input data against generated schema

### Business Logic Modules (`src/bl/`)

| Module | Service | Purpose |
|--------|---------|---------|
| `builder/` | `SchemaBuilderService` | Schema inference, merging |
| `analyzer/` | `SchemaAnalyzer` | Structural analysis, similarity calculation, grouping |
| `scoring/` | `ScoringEngine` | Quality scoring with weighted rules |
| `validator/` | `SchemaValidator` | JSON Schema validation with error formatting |
| `generator/` | `GeneratorService` | Mock data generation, regex synthesis |

### Dependency Injection

Services are composed via FastAPI's `Depends()` in `src/api/routers/schemas.py`:
```python
def get_facade() -> SchemaBuilderFacade:
    factory = get_factory()
    return SchemaBuilderFacade(schema_service=factory.create_schema_service())
```

### Configuration

- **Pattern definitions**: `config/patterns.yaml` (email, UUID, date, etc.)
- **Scoring weights**: `src/bl/scoring/config/weights.py`

## Code Patterns

- Domain interfaces in `src/domain/interfaces.py` define contracts (`ISchemaService`)
- Custom exceptions inherit from `SchemaBuilderError` with `to_dict()` for API responses
- All modules use `LoggerFactory.get_logger(__name__)` for logging
- Pydantic models handle request/response validation
- YAML configs loaded via `src/core/config_loader.py`

### Dependency Injection Pattern

Services use centralized `service_config` (in `src/core/service_config.py`) for all shared utilities:

```python
from src.core.service_config import service_config

class MyService:
    def __init__(self):
        self.dependency = service_config.dependency
```

**Key points:**
- All services directly use `service_config` - no constructor parameters for dependencies
- Tests can mock by modifying `service_config` attributes or using `service_config.reset()`
- `service_config` uses `@cached_property` for lazy-loaded singletons
- Only stateless utilities belong in `service_config` (TreeBuilder, SchemaMerger, etc.)

## Code Style

- **IMPORTANT**: Never use docstrings (triple-quoted strings `"""`) in this codebase
- **IMPORTANT**: Never use inline comments (`#`) - code should be self-documenting
- Keep function and variable names clear and descriptive

## Testing

- Unit tests mirror source structure: `tests/unit/test_builder/`, `tests/unit/test_scoring/`, etc.
- Integration tests use `httpx.ASGITransport` for full API testing
- Fixtures in `tests/conftest.py`: sample data objects
- Test async endpoints with `@pytest.mark.asyncio`
